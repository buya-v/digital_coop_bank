"""KYC session/status service + draft->Member promotion (EP-1 slice 2, T2).

Owns the ХУР/XYP state-register KYC flow on the pre-auth onboarding DRAFT and the
promotion to an E-1 Member on approval. Reuses the slice-1 foundation (the
onboarding repository, the bootstrap-token hash, the timestamp helpers) and never
commits — the router owns the transaction boundary (slice-1 convention).

THE KYC-BEFORE-MEMBER RECONCILIATION (04 §2 vs the contract, DEC-4):
`KycSubmission` (E-2) has a NOT-NULL `member_id` FK, but KYC runs during the
PRE-AUTH application, before any Member exists. So the IN-FLIGHT handle
(`kyc_inquiry_id` + `kyc_status`) lives on the DRAFT; the member-linked
`KycSubmission` (evidence/result) is created only AT PROMOTION, once a Member
exists. A Member is created ONLY on APPROVED — never on REJECTED/PENDING_REVIEW
(DEC-4: no member record ever reaches a rejected status; a rejected or abandoned
application leaves NO member row).

This slice STOPS at membership_status PENDING_PAYMENT — no share purchase, no
MembershipShare, no ledger, no money.
"""
from __future__ import annotations

import dataclasses
import datetime
import secrets

from sqlalchemy.orm import Session

from app.adapters.ekyc.port import (
    EkycApplicant,
    EkycProvider,
    EkycProviderError,
    EkycResult,
)
from app.models.identity import (
    KycDocumentType,
    KycResult,
    KycScreeningResult,
    KycStatus,
    OnboardingApplication,
    OnboardingApplicationStatus,
)
from app.models.membership import Member, MembershipStatus
from app.repositories.identity import KycSubmissionRepository
from app.repositories.membership import MemberRepository, utc_now
from app.repositories.onboarding import OnboardingApplicationRepository
from app.services.onboarding import _hash_token, _now_iso

# Statuses that are recorded as FINAL on the draft: once here, getKycStatus does
# NOT re-poll the provider (APPROVED is promoted-and-frozen; REJECTED is a decided
# no-Member outcome the applicant would restart with a new session). PENDING_REVIEW
# is intentionally NOT here — it keeps polling until manual review resolves it.
_RECORDED_FINAL = frozenset({KycStatus.APPROVED, KycStatus.REJECTED})

# Public member_id (DEC-28): `DCB-` + 8 chars from an unambiguous alphabet
# (Crockford-style: no 0/O/1/I/L/U to avoid transcription errors). Drawn from
# `secrets` so it is non-guessable — NEVER a sequence, and never derived from the
# UUID PK or any personal data.
_MEMBER_ID_ALPHABET = "23456789ABCDEFGHJKMNPQRSTVWXYZ"
_MEMBER_ID_LENGTH = 8


class KycError(Exception):
    """Base for KYC domain errors (mapped to HTTP by the router)."""


class KycAlreadyApproved(KycError):
    """KYC is already approved for this applicant (maps to 409 KYC_ALREADY_APPROVED)."""


class KycProviderUnavailable(KycError):
    """The eKYC provider is unreachable (maps to 502 VENDOR_UNAVAILABLE)."""


class KycPromotionIncomplete(KycError):
    """The register approved but the draft lacks a DEC-6 name part required to
    create a Member (defensive; the happy path PATCHes identity before KYC).
    Maps to 409 STATE_CONFLICT."""


@dataclasses.dataclass(frozen=True)
class KycSessionResult:
    """Backs KycSessionResponse (kyc_inquiry_id + session_token + kyc_status)."""

    kyc_inquiry_id: str
    session_token: str
    kyc_status: KycStatus  # IN_PROGRESS (contract-pinned literal for this response)


@dataclasses.dataclass(frozen=True)
class KycStatusResult:
    """Backs KycStatusResponse (kyc_status + retry_guidance + pending_review)."""

    kyc_status: KycStatus
    retry_guidance: str | None
    pending_review: bool


class KycService:
    def __init__(self, session: Session, provider: EkycProvider) -> None:
        self._repo = OnboardingApplicationRepository(session)
        self._members = MemberRepository(session)
        self._submissions = KycSubmissionRepository(session)
        self._provider = provider

    # --- createKycSession ----------------------------------------------------

    def create_session(self, resume_token: str) -> KycSessionResult | None:
        """Start a KYC session via the eKYC port; store the inquiry id + set the
        draft IN_PROGRESS. Returns None if the token matches no draft (-> 401).
        Raises KycAlreadyApproved / KycProviderUnavailable.
        """
        draft = self._repo.get_by_resume_token_hash(_hash_token(resume_token))
        if draft is None:
            return None
        if draft.kyc_status is KycStatus.APPROVED:
            raise KycAlreadyApproved()

        try:
            session = self._provider.start_verification(self._applicant(draft))
        except EkycProviderError as exc:
            raise KycProviderUnavailable() from exc

        draft.kyc_inquiry_id = session.inquiry_id
        draft.kyc_status = session.status  # IN_PROGRESS
        state = dict(draft.onboarding_state or {})
        kyc = dict(state.get("kyc") or {})
        kyc.update(
            {
                "inquiry_id": session.inquiry_id,
                "status": session.status.value,
                "started_at": _now_iso(),
            }
        )
        state["kyc"] = kyc
        self._stamp(state, "kyc_session_started_at")
        draft.onboarding_state = state
        self._repo.update(draft)
        return KycSessionResult(
            kyc_inquiry_id=session.inquiry_id,
            session_token=session.session_token,
            kyc_status=session.status,
        )

    # --- getKycStatus (re-polls the port; promotes on APPROVED) --------------

    def get_status(self, resume_token: str) -> KycStatusResult | None:
        """Return current KYC status; re-poll the port and drive the state
        machine (promote on APPROVED; never create a Member otherwise). Returns
        None if the token matches no draft (-> 401)."""
        draft = self._repo.get_by_resume_token_hash(_hash_token(resume_token))
        if draft is None:
            return None

        status = draft.kyc_status
        if status is None or draft.kyc_inquiry_id is None:
            # No session started yet.
            return KycStatusResult(
                kyc_status=KycStatus.NOT_STARTED,
                retry_guidance=None,
                pending_review=False,
            )
        if status in _RECORDED_FINAL:
            # Idempotent: already decided and persisted; do not re-poll/re-promote.
            return KycStatusResult(
                kyc_status=status,
                retry_guidance=None,
                pending_review=False,
            )

        # IN_PROGRESS or PENDING_REVIEW -> re-poll the register.
        try:
            result = self._provider.get_result(draft.kyc_inquiry_id)
        except EkycProviderError as exc:
            raise KycProviderUnavailable() from exc

        new_status = result.status
        if new_status is KycStatus.APPROVED:
            self._promote(draft, result)
            pending_review = False
        elif new_status is KycStatus.REJECTED:
            # DEC-4: a rejected result creates NO Member. Only the draft is marked.
            draft.kyc_status = KycStatus.REJECTED
            pending_review = False
        elif new_status is KycStatus.PENDING_REVIEW:
            draft.kyc_status = KycStatus.PENDING_REVIEW
            pending_review = True
        else:  # IN_PROGRESS
            draft.kyc_status = KycStatus.IN_PROGRESS
            pending_review = False

        self._record_result_on_state(draft, result)
        self._repo.update(draft)
        return KycStatusResult(
            kyc_status=new_status,
            retry_guidance=result.retry_guidance,
            pending_review=pending_review,
        )

    # --- promotion (the crux) ------------------------------------------------

    def _promote(self, draft: OnboardingApplication, result: EkycResult) -> Member:
        """Create an E-1 Member from the draft on APPROVED KYC and the
        member-linked E-2 KycSubmission. DEC-4: this is the ONLY path that ever
        creates a Member. membership_status: PENDING_KYC -> PENDING_PAYMENT.
        STOPS at PENDING_PAYMENT (no share purchase / ledger / money)."""
        if not draft.ner or not draft.etsgiin_ner:
            # The register would not approve an identity we never captured; guard
            # so a malformed flow fails loudly rather than inserting a bad Member.
            raise KycPromotionIncomplete()

        # DEC-6(d): the KYC-verified registration number is authoritative.
        verified_reg = (
            result.verified_registration_number or draft.registration_number
        )
        if not verified_reg:
            # Never create a Member without its sole identity key (the registration
            # number). A state-register approval always echoes one; guard anyway so a
            # NULL key can never reach the member table.
            raise KycPromotionIncomplete()

        # PENDING_KYC -> PENDING_PAYMENT: the member is born the instant KYC is
        # approved and immediately advances past KYC. (No member exists at
        # PENDING_KYC before approval — DEC-4 — so the transient state never
        # persists to a rejected outcome.)
        member = self._members.create(
            member_id=self._generate_member_id(),
            ovog=draft.ovog,
            etsgiin_ner=draft.etsgiin_ner,
            ner=draft.ner,
            mrz_name_latin=draft.mrz_name_latin,
            registration_number=verified_reg,
            membership_status=MembershipStatus.PENDING_KYC,
            # Contact channels + structured address carried over from the draft
            # (email/phone were required at bootstrap; address is captured during
            # the identity step). preferred_language defaults to Cyrillic-Mongolian.
            email=draft.email,
            phone_number=draft.phone_number,
            address_line_1=draft.address_line_1,
            address_line_2=draft.address_line_2,
            city=draft.city,
            region=draft.region,
            postal_code=draft.postal_code,
            country=draft.country,
        )
        member.membership_status = MembershipStatus.PENDING_PAYMENT

        submitted_at = self._session_started_at(draft)
        resolved_at = utc_now()
        assert draft.kyc_inquiry_id is not None  # guaranteed by get_status guard
        self._submissions.create(
            member_id=member.id,
            kyc_inquiry_id=draft.kyc_inquiry_id,
            document_type=KycDocumentType.NATIONAL_ID,
            ocr_extracted_fields=dict(result.verified_fields),
            screening_result=KycScreeningResult.CLEAR,
            result=KycResult.PASSED,
            result_reasons=dict(result.reasons),
            evidence_refs=dict(result.evidence),
            submitted_at=submitted_at,
            resolved_at=resolved_at,
        )

        draft.kyc_status = KycStatus.APPROVED
        # The draft is now handed off; freeze it (DRAFT -> SUBMITTED).
        draft.status = OnboardingApplicationStatus.SUBMITTED
        return member

    # --- helpers -------------------------------------------------------------

    def _generate_member_id(self) -> str:
        """Mint a unique non-guessable public member_id (`DCB-XXXXXXXX`, DEC-28).

        Retries on the (astronomically unlikely) collision against an existing
        row so the UNIQUE constraint is never the thing that surfaces it."""
        for _ in range(10):
            candidate = "DCB-" + "".join(
                secrets.choice(_MEMBER_ID_ALPHABET) for _ in range(_MEMBER_ID_LENGTH)
            )
            if self._members.get_by_member_id(candidate) is None:
                return candidate
        # 30^8 space makes 10 straight collisions effectively impossible; fail
        # loudly rather than loop unboundedly if it somehow happens.
        raise KycPromotionIncomplete()

    @staticmethod
    def _applicant(draft: OnboardingApplication) -> EkycApplicant:
        dob = draft.date_of_birth.isoformat() if draft.date_of_birth else None
        return EkycApplicant(
            registration_number=draft.registration_number,
            ner=draft.ner,
            etsgiin_ner=draft.etsgiin_ner,
            ovog=draft.ovog,
            date_of_birth=dob,
        )

    def _record_result_on_state(
        self, draft: OnboardingApplication, result: EkycResult
    ) -> None:
        state = dict(draft.onboarding_state or {})
        kyc = dict(state.get("kyc") or {})
        kyc["status"] = result.status.value
        kyc["resolved_at"] = _now_iso()
        if result.verified_registration_number is not None:
            # Recorded so a later PATCH detects a provisional/verified conflict
            # (409 REGISTRATION_NUMBER_MISMATCH; DEC-6(d)).
            kyc["verified_registration_number"] = result.verified_registration_number
        state["kyc"] = kyc
        self._stamp(state, "kyc_resolved_at")
        draft.onboarding_state = state

    @staticmethod
    def _session_started_at(draft: OnboardingApplication) -> datetime.datetime:
        state = draft.onboarding_state or {}
        kyc = state.get("kyc") or {}
        started = kyc.get("started_at")
        if isinstance(started, str):
            try:
                return datetime.datetime.fromisoformat(started)
            except ValueError:
                pass
        return utc_now()

    @staticmethod
    def _stamp(state: dict[str, object], key: str) -> None:
        existing = state.get("kpi_timestamps")
        kpi: dict[str, object] = dict(existing) if isinstance(existing, dict) else {}
        kpi[key] = _now_iso()
        state["kpi_timestamps"] = kpi
