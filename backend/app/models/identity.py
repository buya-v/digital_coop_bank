"""Identity-domain models (E-2 KycSubmission, E-3 DeviceBinding, E-4 ConsentRecord).

Derived from 04_technical_architecture.md §2.2 (lines 145-173), owned by S-1
(Identity & Onboarding Service). Table definitions only — no behaviour.

Enums whose value sets 04 enumerates are real Enums (values verbatim). Money is
MoneyMinor; ids are UUID; FKs are by table-name string. `persona_inquiry_id`
(E-2) is kept verbatim from 04, but note: it is a vendor-named field (Persona)
flagged in CLAUDE.md as a US-market leak — the Mongolia migration will revisit
the eKYC vendor. Reproduced here only to mirror 04 §2 faithfully.

Nullability convention: a field is Optional iff 04 marks it `?`; otherwise NOT
NULL. (04 does not otherwise specify column nullability.)
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import JSON, Enum, ForeignKey, String
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
    # Vendor reference (DEC-5). Vendor-named field flagged in CLAUDE.md — verbatim
    # from 04 §2 only; the Mongolia migration will revisit the eKYC vendor.
    persona_inquiry_id: Mapped[str] = mapped_column(String(128), unique=True)
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
