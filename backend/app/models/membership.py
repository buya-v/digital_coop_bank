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
    number as the identity key. No first_name/last_name (a non-negotiable)."""

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
