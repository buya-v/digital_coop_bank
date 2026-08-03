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

from sqlalchemy import JSON, Date, Enum, ForeignKey, String, UniqueConstraint
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


class MfaFactorType(enum.Enum):
    """Persisted MFA factor type for the `mfa_factor` table.

    04 §2.2 does NOT model a standalone MFA-factor entity — it carries only
    `DeviceBinding.biometric_enabled` (a boolean) for on-device biometrics. The
    OpenAPI `MfaFactorType` schema lists TOTP / SMS / BIOMETRIC, but this table
    persists only the two factors the enrollment feature actually implements and
    stores state for: TOTP (an app-generated seed, encrypted at rest) and SMS (an
    out-of-band code delivered via a port). BIOMETRIC is NOT a server-stored
    secret — it is device-local (already covered by `DeviceBinding`) — so it is
    rejected at the API boundary (422) and never reaches this column. Constraining
    the persisted value set to the supported factors keeps the DB enum honest
    about what the system can actually verify.
    """

    TOTP = "TOTP"
    SMS = "SMS"


class MfaFactorStatus(enum.Enum):
    """Lifecycle of an `mfa_factor` row.

    A factor is created PENDING at enrollment and becomes ACTIVE only after the
    member proves a correct code (the binding step / first successful step-up,
    enforced by the step-up slice). A PENDING (never-confirmed) factor must never
    authorize a step-up — the two-state machine makes "confirmed" a first-class,
    queryable fact rather than an implicit flag.
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"


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


class MfaFactor(Base, UUIDPrimaryKey, Timestamps):
    """An enrolled multi-factor authentication factor for a member (US-1.4).

    NEW entity (not in 04 §2.2): the enrollment feature needs first-class,
    per-factor lifecycle state that `DeviceBinding.biometric_enabled` (a boolean)
    cannot express — a PENDING vs ACTIVE binding status, and, for TOTP, a stored
    shared secret. It backs `POST /auth/mfa/enrollments` and is the credential the
    step-up slice verifies against.

    SECURITY — secret at rest:
    - `secret_ciphertext` holds the TOTP shared secret AFTER app-level
      authenticated encryption (Fernet / AES-GCM via `cryptography`; see
      `app.auth.mfa`). The PLAINTEXT seed is NEVER stored, logged, or returned
      after the one-time enrollment binding challenge. It is decrypted only
      in-memory to verify a submitted code.
    - The column is Optional: an SMS factor has no server-stored TOTP seed (its
      one-time code is delivered out-of-band through the SMS port and is a
      transient verification concern, not persisted at rest here).

    Uniqueness: at most one factor per (member, factor_type). A member re-enrolling
    a still-PENDING factor re-issues the challenge on the same row; a duplicate of
    an already-ACTIVE factor is refused (409 FACTOR_EXISTS).
    """

    __tablename__ = "mfa_factor"
    __table_args__ = (
        UniqueConstraint(
            "member_id", "factor_type", name="uq_mfa_factor_member_factor_type"
        ),
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    factor_type: Mapped[MfaFactorType] = mapped_column(
        Enum(MfaFactorType, name="mfa_factor_type")
    )
    status: Mapped[MfaFactorStatus] = mapped_column(
        Enum(MfaFactorStatus, name="mfa_factor_status")
    )
    # Encrypted TOTP shared secret (CIPHERTEXT ONLY). NULL for SMS. Never plaintext.
    secret_ciphertext: Mapped[Optional[str]] = mapped_column(String(512))
    # Set when the factor is proven and promoted PENDING -> ACTIVE (the step-up
    # slice performs the binding); NULL while PENDING.
    confirmed_at: Mapped[Optional[datetime.datetime]]
    # --- Step-up brute-force lockout counters (the step-up slice, US-1.4) -----
    # Consecutive failed step-up `factor_response` attempts against this factor.
    # Reset to 0 on a correct code. When it reaches the service threshold the
    # factor LOCKS (createStepUpToken -> 423) — the DB fact behind "never unlimited
    # TOTP guessing". Server default 0 so pre-existing rows and inserts that omit
    # it are well-defined.
    failed_attempts: Mapped[int] = mapped_column(default=0, server_default="0")
    # When the factor last locked. A lockout auto-expires after a fixed window
    # (see the step-up service) so a member is never permanently locked out with no
    # unlock path; NULL while not locked.
    locked_at: Mapped[Optional[datetime.datetime]]
    # --- SMS one-time-code CHALLENGE (SMS factor only, US-1.4) ----------------
    # An SMS factor has no server-stored seed (see `secret_ciphertext` above):
    # instead the server ISSUES a one-time code, delivers it out of band via the
    # SMS port, and remembers it here just long enough to verify one step-up
    # response. Only the HASH is kept — the plaintext code is NEVER stored, logged,
    # or returned (SHA-256 hex; see `app.auth.mfa.hash_sms_code`). SINGLE-USE: the
    # step-up service CLEARS this hash on the first correct code, so a replay of a
    # spent code finds no challenge and fails. Both NULL for a TOTP factor and for
    # an SMS factor with no outstanding challenge.
    sms_challenge_hash: Mapped[Optional[str]] = mapped_column(String(128))
    # When the outstanding SMS challenge expires (a few minutes out; see
    # `SMS_CHALLENGE_TTL`). An expired code is refused even if never used; NULL when
    # no challenge is outstanding.
    sms_challenge_expires_at: Mapped[Optional[datetime.datetime]]


class StepUpToken(Base, UUIDPrimaryKey, Timestamps):
    """A single-use, short-lived step-up assertion issued to a member (US-1.4).

    NEW entity (not in 04 §2.2): the backend ISSUES a security credential — the
    step-up token the `stepUpAssertion` scheme (root.yaml) requires on sensitive
    operations (revokeDevice, and later card reveal / vote / external payment).
    Minted by `POST /auth/step-up` AFTER the member proves an MFA `factor_response`;
    consumed exactly once by `require_step_up`.

    SECURITY — this is a bearer credential, so it is stored the way a credential
    must be:
    - **Hash only.** `token_hash` is the SHA-256 of the opaque random token; the
      plaintext token is returned to the client exactly once and is NEVER stored,
      logged, or recoverable from this row. A leaked DB row therefore yields no
      usable token (same posture as `onboarding_application.resume_token_hash`).
    - **Single-use.** `consumed_at` is set the first (and only) time the token is
      accepted; a replay finds it already consumed and is refused. Consumption is a
      DB fact (a conditional UPDATE guarded by `consumed_at IS NULL`), not a
      stateless-JWT JTI dance.
    - **Short-lived.** `expires_at` is a few minutes out; an expired token is
      refused even if never consumed.
    - **Member-bound.** `member_id` is the minting member; `require_step_up`
      rejects a token presented by any other member — a token minted for A can
      never authorize an action for B.
    - **Optionally action-bound.** `requested_action` (nullable) pins the token to
      one sensitive operation when set; a general token (NULL) is accepted by any
      step-up-gated operation.

    `created_at`/`updated_at` come from the Timestamps mixin (`created_at` is the
    mint time). No money / ledger.
    """

    __tablename__ = "step_up_token"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # SHA-256 hex of the opaque token (64 chars); UNIQUE so a presented token maps
    # to at most one row. The plaintext is NEVER stored.
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    # The sensitive action this token authorizes, when scoped (e.g. "revokeDevice");
    # NULL means a general step-up assertion accepted by any gated operation.
    requested_action: Mapped[Optional[str]] = mapped_column(String(128))
    # Short expiry (a few minutes); an expired token is refused.
    expires_at: Mapped[datetime.datetime]
    # Set once, atomically, when the token is spent; NULL while unused (single-use).
    consumed_at: Mapped[Optional[datetime.datetime]]


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
