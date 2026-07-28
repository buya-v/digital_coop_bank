"""Identity-domain models (E-2 KycSubmission, E-3 DeviceBinding, E-4 ConsentRecord).

Derived from 04_technical_architecture.md §2.2 (lines 145-173), owned by S-1
(Identity & Onboarding Service). Table definitions only — no behaviour.

Enums whose value sets 04 enumerates are real Enums (values verbatim). Money is
MoneyMinor; ids are UUID; FKs are by table-name string. `kyc_inquiry_id`
(E-2) is the eKYC-provider inquiry reference (migrated to match 04 (DEC-5 /
rails run) — the former vendor-named field is now role-neutral; the concrete
eKYC provider is a procurement/TBD decision, with ХУР/XYP state-register lookup
the compliant-alternative candidate). Reproduced here to mirror 04 §2 faithfully.

Nullability convention: a field is Optional iff 04 marks it `?`; otherwise NOT
NULL. (04 does not otherwise specify column nullability.)
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import JSON, Date, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey


class KycDocumentType(enum.Enum):
    """E-2 document_type. Values verbatim from 04 §2."""

    PASSPORT = "PASSPORT"
    DRIVERS_LICENSE = "DRIVERS_LICENSE"
    NATIONAL_ID = "NATIONAL_ID"


class KycScreeningResult(enum.Enum):
    """E-2 screening_result — sanctions/PEP watchlist outcome. Verbatim from 04."""

    CLEAR = "CLEAR"
    POTENTIAL_MATCH = "POTENTIAL_MATCH"
    MATCH = "MATCH"


class KycResult(enum.Enum):
    """E-2 result. Verbatim from 04 (maps to member KycStatus)."""

    PASSED = "PASSED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    FAILED = "FAILED"


class KycStatus(enum.Enum):
    """KYC lifecycle status (04 §2.2 E-1 `kyc_status`, DEC-19).

    Value set verbatim from 04 / the OpenAPI `KycStatus` schema. This is the
    IN-FLIGHT status carried on the pre-auth onboarding DRAFT while the ХУР/XYP
    state-register lookup runs — BEFORE any E-1 Member exists (DEC-4). It is the
    contract vocabulary returned by createKycSession / getKycStatus. NULL on the
    draft column means the applicant has NOT started KYC (surfaced as
    NOT_STARTED); the enum still lists NOT_STARTED so a caller may set it
    explicitly and so the migration type matches the contract enum exactly.
    """

    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DevicePlatform(enum.Enum):
    """E-3 platform. Values verbatim from 04 §2."""

    IOS = "IOS"
    ANDROID = "ANDROID"
    WEB = "WEB"


class DeviceStatus(enum.Enum):
    """E-3 status. Values verbatim from 04 §2."""

    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class ConsentType(enum.Enum):
    """E-4 consent_type. Values verbatim from 04 §2."""

    TERMS_AND_BYLAWS = "TERMS_AND_BYLAWS"
    PRIVACY_POLICY = "PRIVACY_POLICY"
    E_SIGN_DISCLOSURE = "E_SIGN_DISCLOSURE"
    MARKETING = "MARKETING"
    DATA_SHARING_OPEN_BANKING = "DATA_SHARING_OPEN_BANKING"
    IMPACT_SPOTLIGHT = "IMPACT_SPOTLIGHT"


class ConsentAction(enum.Enum):
    """E-4 action. Values verbatim from 04 §2."""

    GRANTED = "GRANTED"
    WITHDRAWN = "WITHDRAWN"


class OnboardingApplicationStatus(enum.Enum):
    """Lifecycle status of a pre-auth onboarding DRAFT (EP-1 slice 1).

    04 §2 does not enumerate an OnboardingApplication entity or its status set —
    it models onboarding save/resume state as the E-1 Member `onboarding_state`
    JSON (04 §2.2, line 140) reached AFTER a member exists. This value set is the
    contract-side lifecycle of the *pre-auth* draft the OpenAPI schemas define
    (`OnboardingApplicationCreateRequest/Response/Current/Patch*`), which the
    contract itself does not name; DRAFT/SUBMITTED are the two states this slice
    needs (create -> DRAFT; identity captured/handed to KYC -> SUBMITTED). KYC,
    eligibility and promotion to a Member are later slices.
    """

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"


class OnboardingApplication(Base, UUIDPrimaryKey, Timestamps):
    """Resumable, pre-auth onboarding draft (US-1.1; F-A, 04 §2.1 line 82).

    RECONCILIATION (04 §2 vs the OpenAPI contract): 04 §2.2 does NOT define a
    distinct onboarding entity — it carries save/resume onboarding state on the
    E-1 Member (`onboarding_state` JSON) and drives progression through
    `MembershipStatus`/`KycStatus`. The OpenAPI contract, however, exposes a
    *pre-auth* `OnboardingApplication` resource: `POST /onboarding/applications`
    mints an `application_id` + `resume_token` and returns `kyc_status =
    NOT_STARTED` BEFORE any authenticated Member (or IdP subject) exists, and
    PATCH carries provisional DEC-6 identity fields. Modelling onboarding as a
    Member-in-PENDING_KYC would require inserting a Member row at that pre-auth
    bootstrap; a rejected application would then have to be deleted, which
    violates DEC-4 ("no member record reaches a rejected membership status") and
    the audit posture. So this is a DISTINCT draft entity — the physical form the
    contract forces and the server-side resumable application F-A describes —
    PROMOTED to an E-1 Member on KYC approval (a later slice). It is not in this
    slice's scope to create a Member. No field here is invented: every column
    maps to a contract property or a DEC-6 identity field.

    Nullability: identity/address/dob fields are Optional because the draft row
    is created at the pre-auth bootstrap (email + phone + channel code only) and
    filled step-by-step by PATCH (whose schema marks every field optional);
    NOT-NULL enforcement of the DEC-6 name parts happens at promotion to Member.
    No money/float. No first_name/last_name. registration_number is structural-
    only (10 chars, 2 Cyrillic + 8 digits) — no check-digit is guessed here.
    """

    __tablename__ = "onboarding_application"

    # Verified contact channels supplied at create (OnboardingApplicationCreateRequest).
    email: Mapped[str] = mapped_column(String(320))
    phone_number: Mapped[str] = mapped_column(String(32))  # E.164
    # Bootstrap "resume_token" (CreateResponse) — stored as a hash so a leaked row
    # does not yield a usable token; the service compares hashes. Application-scoped
    # only; NOT full auth/MFA (a later slice).
    resume_token_hash: Mapped[str] = mapped_column(String(128), unique=True)

    # DEC-6 three-part Mongolian name (Cyrillic canonical); all Optional in the draft.
    ovog: Mapped[Optional[str]] = mapped_column(String(120))  # clan, optional
    etsgiin_ner: Mapped[Optional[str]] = mapped_column(String(120))  # patronymic
    ner: Mapped[Optional[str]] = mapped_column(String(120))  # given name
    # Verbatim Latin from the document MRZ; KYC-populated, never derived (DEC-6).
    mrz_name_latin: Mapped[Optional[str]] = mapped_column(String(120))
    # Provisional national registration number (2 Cyrillic + 8 digits); the
    # KYC-verified value is authoritative (DEC-6(d)). Unique; STRUCTURAL validation
    # only — the check-digit algorithm is unpublished (never guessed).
    # NOT unique on the draft: it is a provisional, applicant-entered value (the
    # authoritative uniqueness lives on Member). A unique constraint here would let a
    # throwaway draft pre-claim a real applicant's registration number and block them.
    registration_number: Mapped[Optional[str]] = mapped_column(String(10))

    # DEC-6 structured postal address (OnboardingApplicationPatchRequest).
    address_line_1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    region: Mapped[Optional[str]] = mapped_column(String(120))  # aimag
    postal_code: Mapped[Optional[str]] = mapped_column(String(32))
    country: Mapped[Optional[str]] = mapped_column(String(120))
    date_of_birth: Mapped[Optional[datetime.date]] = mapped_column(Date)

    status: Mapped[OnboardingApplicationStatus] = mapped_column(
        Enum(OnboardingApplicationStatus, name="onboarding_application_status")
    )
    # Save/resume step state + KPI-1.1 instrumentation timestamps — mirrors the
    # E-1 `onboarding_state` JSON (04 §2.2); backs the Current response's
    # current_step / saved_data / progress_pct / kpi_timestamps views.
    onboarding_state: Mapped[Optional[dict]] = mapped_column(JSON)

    # --- In-flight KYC state (T2) --------------------------------------------
    # WHY these are real columns (not `onboarding_state` JSON): the OpenAPI
    # contract RETURNS both — createKycSession returns `kyc_inquiry_id` and
    # getKycStatus/createKycSession return `kyc_status`. `kyc_inquiry_id` must be
    # UNIQUE (it is the eKYC-provider inquiry reference and the E-2 KycSubmission
    # join key at promotion), and `kyc_status` gates the create/promote state
    # machine (409 KYC_ALREADY_APPROVED; idempotent promotion) — both want
    # first-class column semantics (a UNIQUE constraint, an ENUM type), which a
    # JSON blob cannot express. The KYC RESULT/evidence still lands on the
    # member-linked E-2 KycSubmission row created AT PROMOTION (04 §2.2), when a
    # Member finally exists (DEC-4); only the in-flight handle lives here.
    # NULL kyc_status == NOT_STARTED (no session yet). Both Optional because the
    # draft is created pre-KYC.
    kyc_inquiry_id: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    kyc_status: Mapped[Optional[KycStatus]] = mapped_column(
        Enum(KycStatus, name="kyc_status")
    )


class KycSubmission(Base, UUIDPrimaryKey, Timestamps):
    """E-2 KycSubmission — one verification attempt (retries create new rows).

    JSON fields are encrypted at rest per 04 (encryption is a service concern,
    not modelled here). submitted_at/resolved_at are the domain lifecycle
    timestamps; created_at/updated_at come from the Timestamps mixin.
    """

    __tablename__ = "kyc_submission"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # eKYC-provider inquiry reference (DEC-5). Migrated to match 04 (DEC-5 /
    # rails run) — role-neutral; the concrete eKYC provider is procurement/TBD.
    kyc_inquiry_id: Mapped[str] = mapped_column(String(128), unique=True)
    document_type: Mapped[KycDocumentType] = mapped_column(
        Enum(KycDocumentType, name="kyc_document_type")
    )
    # Vendor OCR output mapped to DEC-6 fields; encrypted.
    ocr_extracted_fields: Mapped[dict] = mapped_column(JSON)
    screening_result: Mapped[KycScreeningResult] = mapped_column(
        Enum(KycScreeningResult, name="kyc_screening_result")
    )
    result: Mapped[KycResult] = mapped_column(Enum(KycResult, name="kyc_result"))
    result_reasons: Mapped[dict] = mapped_column(JSON)
    # Encrypted object-store URIs (ID images, selfie) with retention class.
    evidence_refs: Mapped[dict] = mapped_column(JSON)
    submitted_at: Mapped[datetime.datetime]
    resolved_at: Mapped[Optional[datetime.datetime]]


class DeviceBinding(Base, UUIDPrimaryKey, Timestamps):
    """E-3 DeviceBinding — a trusted device for biometrics/MFA/step-up (US-1.4).

    bound_at/last_seen_at/revoked_at are the domain lifecycle timestamps;
    created_at/updated_at come from the Timestamps mixin.
    """

    __tablename__ = "device_binding"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    device_fingerprint: Mapped[str] = mapped_column(String(255))
    platform: Mapped[DevicePlatform] = mapped_column(
        Enum(DevicePlatform, name="device_platform")
    )
    push_token: Mapped[Optional[str]] = mapped_column(String(255))
    biometric_enabled: Mapped[bool]
    status: Mapped[DeviceStatus] = mapped_column(Enum(DeviceStatus, name="device_status"))
    bound_at: Mapped[datetime.datetime]
    last_seen_at: Mapped[datetime.datetime]
    revoked_at: Mapped[Optional[datetime.datetime]]


class ConsentRecord(Base, UUIDPrimaryKey):
    """E-4 ConsentRecord — append-only record of consent grant/withdrawal
    (US-1.5, US-13.6). Append-only, so it carries only its own `recorded_at`
    (no Timestamps mixin — mirrors the LedgerEntry append-only precedent).
    """

    __tablename__ = "consent_record"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    consent_type: Mapped[ConsentType] = mapped_column(
        Enum(ConsentType, name="consent_type")
    )
    action: Mapped[ConsentAction] = mapped_column(Enum(ConsentAction, name="consent_action"))
    version: Mapped[str] = mapped_column(String(64))  # document version consented to
    recorded_at: Mapped[datetime.datetime]
    channel: Mapped[str] = mapped_column(String(64))
