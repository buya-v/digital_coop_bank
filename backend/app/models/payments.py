"""Payments-domain models (EP-4): E-14..E-17.

Table definitions only — no payment logic, no rail selection, no idempotency
enforcement. Derived from 04 §2.4 verbatim.

MARKET NOTE (CLAUDE.md): 04 was written against US/EU rails and vendors. The
`rail` enum values (ACH | WIRE | RTP) and the Plaid vendor references
(`plaid_item_ref`, `processor_token_ref`) are modelled *as 04 states them*, but
the Mongolia migration must replace them — rails become RTGS (Банксүлжээ /
Banksuljee) above the Governor-set threshold and ACH+ at/below it; card rails
clear via NETC; Plaid is not a Mongolian vendor. These are flagged, not
silently "corrected", because the schema mirrors the ratified 04 baseline.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor
from app.models.deposits import RecipientIdentifierType


# --------------------------------------------------------------------------- #
# E-14 ExternalAccountLink                                                     #
# --------------------------------------------------------------------------- #
class VerificationMethod(enum.Enum):
    """E-14 verification_method. Values verbatim from 04 §2.4."""

    PLAID_INSTANT = "PLAID_INSTANT"
    MICRO_DEPOSIT = "MICRO_DEPOSIT"


class ExternalAccountLinkStatus(enum.Enum):
    """E-14 status. Values verbatim from 04 §2.4."""

    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    RELINK_REQUIRED = "RELINK_REQUIRED"
    REMOVED = "REMOVED"


class ExternalAccountLink(Base, UUIDPrimaryKey, Timestamps):
    """E-14 ExternalAccountLink — a verified external bank account (US-4.2).

    Account/routing numbers are tokenized at the sponsor bank, never stored raw.
    The *_ref columns are encrypted vendor references (encryption is an
    application concern, not modelled here)."""

    __tablename__ = "external_account_link"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # Vendor references (04 leaks the Plaid vendor into the schema — CLAUDE.md).
    # Encrypted at rest by the application layer.
    plaid_item_ref: Mapped[Optional[str]] = mapped_column(String(255))
    processor_token_ref: Mapped[Optional[str]] = mapped_column(String(255))
    institution_name: Mapped[Optional[str]] = mapped_column(String(255))
    account_mask: Mapped[Optional[str]] = mapped_column(String(32))
    account_subtype: Mapped[Optional[str]] = mapped_column(String(64))
    verification_method: Mapped[VerificationMethod] = mapped_column(
        Enum(VerificationMethod, name="verification_method")
    )
    status: Mapped[ExternalAccountLinkStatus] = mapped_column(
        Enum(ExternalAccountLinkStatus, name="external_account_link_status")
    )
    # Reuse of transaction data for underwriting requires explicit consent (E-4).
    open_banking_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[datetime.datetime]]


# --------------------------------------------------------------------------- #
# E-15 Payee                                                                   #
# --------------------------------------------------------------------------- #
class PayeeType(enum.Enum):
    """E-15 payee_type. Values verbatim from 04 §2.4."""

    INTERNAL_MEMBER = "INTERNAL_MEMBER"
    EXTERNAL_ACCOUNT = "EXTERNAL_ACCOUNT"
    BILLER = "BILLER"


class PayeeStatus(enum.Enum):
    """E-15 status. Values verbatim from 04 §2.4."""

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Payee(Base, UUIDPrimaryKey, Timestamps):
    """E-15 Payee — bill-pay payee managed by the member (US-4.3)."""

    __tablename__ = "payee"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    name: Mapped[str] = mapped_column(String(100))
    payee_type: Mapped[PayeeType] = mapped_column(Enum(PayeeType, name="payee_type"))
    # Polymorphic: a recipient identifier (DEC-3) OR ExternalAccountLink/biller
    # details, depending on payee_type. Stored as an opaque string ref (04 §2.4).
    target_ref: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[PayeeStatus] = mapped_column(Enum(PayeeStatus, name="payee_status"))


# --------------------------------------------------------------------------- #
# E-16 ScheduledPayment                                                        #
# --------------------------------------------------------------------------- #
class PaymentRail(enum.Enum):
    """E-16 rail. Values verbatim from 04 §2.4.

    MARKET NOTE: ACH | WIRE | RTP are US rails that do not exist in Mongolia
    (CLAUDE.md). The Mongolia migration replaces them with RTGS/Banksuljee and
    ACH+ (threshold set by Governor's order → configuration, never hard-coded).
    Modelled here as 04 states so the schema mirrors the ratified baseline."""

    INTERNAL_P2P = "INTERNAL_P2P"
    ACH = "ACH"
    WIRE = "WIRE"
    RTP = "RTP"


class ScheduledPaymentStatus(enum.Enum):
    """E-16 status. Values verbatim from 04 §2.4."""

    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class ScheduledPayment(Base, UUIDPrimaryKey, Timestamps):
    """E-16 ScheduledPayment — future-dated / recurring schedule (US-4.3).

    Each execution posts a Transaction (1—N); that posting is done by the
    payments service, not here."""

    __tablename__ = "scheduled_payment"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    payee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payee.id")
    )
    amount = mapped_column(MoneyMinor)  # money, integer minor units
    rail: Mapped[PaymentRail] = mapped_column(Enum(PaymentRail, name="payment_rail"))
    # schedule {type: ONE_OFF|RECURRING, start_date, frequency?, end_date?} (04).
    schedule = mapped_column(JSONB)
    # Insufficient-funds retry policy with member notification (US-11.1).
    retry_policy = mapped_column(JSONB, nullable=True)
    next_run_at: Mapped[Optional[datetime.datetime]]
    status: Mapped[ScheduledPaymentStatus] = mapped_column(
        Enum(ScheduledPaymentStatus, name="scheduled_payment_status")
    )


# --------------------------------------------------------------------------- #
# E-17 PaymentRequest (+ child share rows)                                     #
# --------------------------------------------------------------------------- #
class SplitMode(enum.Enum):
    """E-17 split_mode. Values verbatim from 04 §2.4."""

    EQUAL = "EQUAL"
    CUSTOM = "CUSTOM"


class PaymentRequestStatus(enum.Enum):
    """E-17 status. Values verbatim from 04 §2.4."""

    OPEN = "OPEN"
    PARTIALLY_SETTLED = "PARTIALLY_SETTLED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PaymentRequestShareStatus(enum.Enum):
    """E-17 per-share status. Values verbatim from 04 §2.4."""

    PENDING = "PENDING"
    PAID = "PAID"
    DECLINED = "DECLINED"
    CANCELLED = "CANCELLED"


class PaymentRequest(Base, UUIDPrimaryKey, Timestamps):
    """E-17 PaymentRequest — expense split / request-to-pay among members
    (US-4.4). Splitting with non-members is out of scope."""

    __tablename__ = "payment_request"

    requester_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # Split of an existing entry, or an ad-hoc amount.
    origin_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    split_mode: Mapped[SplitMode] = mapped_column(Enum(SplitMode, name="split_mode"))
    total_amount = mapped_column(MoneyMinor)  # money, integer minor units
    reminders_sent: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[PaymentRequestStatus] = mapped_column(
        Enum(PaymentRequestStatus, name="payment_request_status")
    )
    expires_at: Mapped[Optional[datetime.datetime]]


class PaymentRequestShare(Base, UUIDPrimaryKey, Timestamps):
    """E-17 "shares child rows" — one debtor's slice of a PaymentRequest.

    04 nests these inside E-17; modelled as a child table (the relational form
    of a repeating child group). Settlement auto-reconciles via US-4.1 P2P."""

    __tablename__ = "payment_request_share"

    payment_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_request.id")
    )
    # Debtor identified per RecipientIdentifierType (DEC-3, 04 §2.4 line 301).
    # T4 reconciliation: this is the SAME concept as E-11 GroupPotMember.invited_via
    # (deposits.py), which owns the real enum/type — not a DeferredEnum. deposits
    # creates the Postgres type; this column references it (create_type=False) so
    # CREATE TYPE runs exactly once.
    debtor_identifier_type: Mapped[RecipientIdentifierType] = mapped_column(
        Enum(RecipientIdentifierType, name="recipient_identifier_type", create_type=False)
    )
    debtor_identifier: Mapped[str] = mapped_column(String(255))
    amount = mapped_column(MoneyMinor)  # money, integer minor units
    status: Mapped[PaymentRequestShareStatus] = mapped_column(
        Enum(PaymentRequestShareStatus, name="payment_request_share_status")
    )
    settled_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
