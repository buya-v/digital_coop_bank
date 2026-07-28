"""Membership-domain models — proof of the derivation pattern (E-1, E-5).

The remaining ~57 entities from 04 §2 are derived the same way in the model
slices. Enums whose values 04 lists are real Enums; money is MoneyMinor; ids are
UUID; timestamps via the mixin. Nothing here implements behaviour — these are
table definitions only.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


class MembershipStatus(enum.Enum):
    """DEC-4 / 04 §2 membership status machine. Values verbatim from 04."""

    PENDING_KYC = "PENDING_KYC"
    PENDING_PAYMENT = "PENDING_PAYMENT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CLOSED = "CLOSED"


class ShareClass(enum.Enum):
    """E-5 share_class. Values verbatim from 04."""

    MEMBERSHIP = "MEMBERSHIP"
    REINVESTED_PATRONAGE = "REINVESTED_PATRONAGE"


class ShareStatus(enum.Enum):
    MEMBER = "ISSUED"
    REDEEMED = "REDEEMED"


class Member(Base, UUIDPrimaryKey, Timestamps):
    """E-1 Member. Name model per the AMENDED DEC-6: three Mongolian name parts,
    Cyrillic canonical, plus the verbatim MRZ Latin string and the registration
    number as the identity key. No first_name/last_name (a non-negotiable).

    Profile extension (T2): the member-facing `member_id` (non-guessable public
    id, DEC-28), a structured postal address, contact channels, and the preferred
    language. `legal_name` is DERIVED read-only (a Python property below), NEVER a
    stored editable column — editing it is rejected (422). These populate at KYC
    promotion (services/kyc.py `_promote`); a Member never exists before then
    (DEC-4)."""

    __tablename__ = "member"

    # DEC-6 three-part Mongolian name (Cyrillic canonical).
    ovog: Mapped[Optional[str]] = mapped_column(String(120))  # clan, optional
    etsgiin_ner: Mapped[str] = mapped_column(String(120))  # patronymic
    ner: Mapped[str] = mapped_column(String(120))  # given name — the identity
    # Verbatim Latin from the document MRZ; never derived/transliterated (DEC-6).
    mrz_name_latin: Mapped[Optional[str]] = mapped_column(String(120))
    # 10-char national registration number (2 Cyrillic letters + 8 digits) — the
    # sole identity-matching key; unique. Structural validation only (the check
    # digit algorithm is unpublished — patterns.md).
    registration_number: Mapped[Optional[str]] = mapped_column(String(10), unique=True)

    membership_status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, name="membership_status")
    )

    # Member-facing non-guessable public id (E-1 `member_id`, DEC-28), e.g.
    # `DCB-8K4W2M9X`. UNIQUE, system-owned (generated at promotion, never member-
    # editable). Distinct from the UUID PK, which is internal.
    member_id: Mapped[str] = mapped_column(String(16), unique=True)

    # DEC-6 structured postal address (E-1; member-editable).
    address_line_1: Mapped[Optional[str]] = mapped_column(String(255))
    address_line_2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    region: Mapped[Optional[str]] = mapped_column(String(120))  # aimag
    postal_code: Mapped[Optional[str]] = mapped_column(String(32))
    country: Mapped[Optional[str]] = mapped_column(String(120))

    # Contact channels / P2P identifiers (E-1, DEC-3). Populated from the draft at
    # promotion (the draft requires both at bootstrap), so NOT NULL here.
    email: Mapped[str] = mapped_column(String(320))
    phone_number: Mapped[str] = mapped_column(String(32))  # E.164

    # Preferred UI language (E-1). Default Cyrillic-Mongolian (`mn`) per CLAUDE.md.
    preferred_language: Mapped[str] = mapped_column(String(35), default="mn")

    @property
    def legal_name(self) -> str:
        """DERIVED read-only legal name (E-1, DEC-6): the three Cyrillic name parts
        in Mongolian order — optional ovog (clan), patronymic, given name — joined
        with spaces. NEVER stored; editing it yields 422 LEGAL_NAME_NOT_EDITABLE."""
        return " ".join(
            part for part in (self.ovog, self.etsgiin_ner, self.ner) if part
        )


class MembershipShare(Base, UUIDPrimaryKey, Timestamps):
    """E-5 MembershipShare. par_value is money (MoneyMinor); DEC-11 sets the
    working value at ₮10,000 (provisional) but that is US-12.5 config, NOT a
    schema default — the column just stores whatever par a share was issued at."""

    __tablename__ = "membership_share"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    certificate_number: Mapped[str] = mapped_column(String(64), unique=True)
    par_value = mapped_column(MoneyMinor)  # money, integer minor units (MNT)
    share_class: Mapped[ShareClass] = mapped_column(Enum(ShareClass, name="share_class"))
    status: Mapped[ShareStatus] = mapped_column(Enum(ShareStatus, name="share_status"))
    issued_at: Mapped[datetime.datetime]
    redeemed_at: Mapped[Optional[datetime.datetime]]
