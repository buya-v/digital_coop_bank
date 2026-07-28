"""Deterministic in-memory MOCK of the ХУР/XYP state-register eKYC provider.

No network, no biometrics, no external SDK — a stub that lets the onboarding KYC
flow (and its tests) exercise every branch of the state machine deterministically.

How the outcome is driven (per the brief: "keyed off a field in the request or a
config TOGGLE"): the terminal outcome is a construction-time toggle,
`scripted_status`, so a caller/test picks exactly which branch a given provider
instance drives:

  - IN_PROGRESS      -> `get_result` stays pending (models a slow register).
  - APPROVED         -> register resolves clean; promotion may proceed.
  - PENDING_REVIEW   -> register resolves to manual review; NO promotion.
  - REJECTED         -> register rejects; NO Member is ever created (DEC-4).

`verified_registration_number` lets a test simulate the register returning an
authoritative value that DIFFERS from the applicant's provisional one
(DEC-6(d)); by default the register echoes the applicant's value (a confirmation).
`unavailable=True` makes the provider raise `EkycProviderError` (-> 502).

State is per-instance and in-memory: `start_verification` remembers the applicant
by `inquiry_id`, and `get_result` reads it back — so a single instance must be
reused across the create+poll of one applicant (the app/test wires it that way).
"""
from __future__ import annotations

import secrets

from app.adapters.ekyc.port import (
    EkycApplicant,
    EkycProvider,
    EkycProviderError,
    EkycResult,
    EkycSession,
)
from app.models.identity import KycStatus

_TERMINAL = frozenset(
    {KycStatus.APPROVED, KycStatus.PENDING_REVIEW, KycStatus.REJECTED}
)

# Applicant-facing capture guidance surfaced as KycStatusResponse.retry_guidance.
# Generic and non-biometric (this is a register lookup, not a document scan).
_DEFAULT_GUIDANCE: dict[KycStatus, str | None] = {
    KycStatus.IN_PROGRESS: "Verification is still in progress; check back shortly.",
    KycStatus.PENDING_REVIEW: "Your details are under manual review; no action needed.",
    KycStatus.REJECTED: (
        "We could not verify your identity against the state register. "
        "Check your registration number and personal details, then try again."
    ),
    KycStatus.APPROVED: None,
}


class MockEkycProvider(EkycProvider):
    """Deterministic, no-network ХУР/XYP state-register stub."""

    def __init__(
        self,
        scripted_status: KycStatus = KycStatus.APPROVED,
        *,
        verified_registration_number: str | None = None,
        retry_guidance: str | None = None,
        unavailable: bool = False,
    ) -> None:
        if scripted_status is KycStatus.NOT_STARTED:
            # NOT_STARTED is a draft state (no inquiry exists), never a provider
            # outcome — refuse it so a mis-scripted test fails loudly.
            raise ValueError("scripted_status must not be NOT_STARTED")
        self._scripted_status = scripted_status
        self._verified_registration_number = verified_registration_number
        self._retry_guidance = retry_guidance
        self._unavailable = unavailable
        self._inquiries: dict[str, EkycApplicant] = {}

    def start_verification(self, applicant: EkycApplicant) -> EkycSession:
        if self._unavailable:
            raise EkycProviderError("state register unreachable")
        inquiry_id = f"kyc_{secrets.token_hex(16)}"
        session_token = f"sess_{secrets.token_urlsafe(24)}"
        self._inquiries[inquiry_id] = applicant
        return EkycSession(
            inquiry_id=inquiry_id,
            session_token=session_token,
            status=KycStatus.IN_PROGRESS,
        )

    def get_result(self, inquiry_id: str) -> EkycResult:
        if self._unavailable:
            raise EkycProviderError("state register unreachable")
        applicant = self._inquiries.get(inquiry_id)
        if applicant is None:
            raise EkycProviderError(f"unknown inquiry_id: {inquiry_id}")

        status = self._scripted_status
        guidance = (
            self._retry_guidance
            if self._retry_guidance is not None
            else _DEFAULT_GUIDANCE.get(status)
        )

        if status not in _TERMINAL:
            # Still IN_PROGRESS: the register has not resolved, so no verified
            # fields/evidence are available yet.
            return EkycResult(
                inquiry_id=inquiry_id,
                status=status,
                verified_registration_number=None,
                verified_fields={},
                evidence={},
                reasons={},
                retry_guidance=guidance,
            )

        # Resolved. The register's authoritative registration number is either an
        # explicit override (to simulate a DEC-6(d) discrepancy) or an echo of the
        # applicant's provisional value (a confirmation).
        verified_reg = (
            self._verified_registration_number
            if self._verified_registration_number is not None
            else applicant.registration_number
        )
        verified_fields: dict[str, object] = {
            "registration_number": verified_reg,
            "ner": applicant.ner,
            "etsgiin_ner": applicant.etsgiin_ner,
            "ovog": applicant.ovog,
            "date_of_birth": applicant.date_of_birth,
            "source": "STATE_REGISTER_LOOKUP",
        }
        evidence: dict[str, object] = {
            "provider": "MOCK_STATE_REGISTER",
            "inquiry_id": inquiry_id,
            "lookup_kind": "STATE_REGISTER",
        }
        reasons: dict[str, object] = {"decision": status.value}
        return EkycResult(
            inquiry_id=inquiry_id,
            status=status,
            verified_registration_number=verified_reg,
            verified_fields=verified_fields,
            evidence=evidence,
            reasons=reasons,
            retry_guidance=guidance,
        )
