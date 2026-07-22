"""Deposits-domain models (E-9 SavingsGoal, E-10 GroupPot, E-11 GroupPotMember,
E-12 GroupPotApprovalRequest, E-13 GroupPotApprovalDecision).

Derived from 04_technical_architecture.md §2.3 (lines 229-265), owned by S-3
(Account & Ledger Service). Table definitions only — no behaviour.

Money (target_amount, current_amount, total_contributed, amount) is MoneyMinor
(BIGINT minor units) — never a float. `current_amount` and `total_contributed`
are DERIVED from attributed LedgerEntries per 04; the column stores whatever the
(not-yet-built) ledger service materializes — no derivation logic here. FKs are
by table-name string; member/account/transaction tables are the foundation.

Nullability convention: Optional iff 04 marks the field `?`; otherwise NOT NULL.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


class SavingsGoalStatus(enum.Enum):
    """E-9 status. Values verbatim from 04 §2."""

    ACTIVE = "ACTIVE"
    ACHIEVED = "ACHIEVED"
    ARCHIVED = "ARCHIVED"


class GroupPotStatus(enum.Enum):
    """E-10 status. Values verbatim from 04 §2."""

    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


class GroupPotMemberRole(enum.Enum):
    """E-11 role. Values verbatim from 04 §2."""

    CREATOR = "CREATOR"
    MEMBER = "MEMBER"


class RecipientIdentifierType(enum.Enum):
    """E-11 invited_via (`RecipientIdentifierType`). Values verbatim from 04 §2."""

    PHONE = "PHONE"
    EMAIL = "EMAIL"
    MEMBER_ID = "MEMBER_ID"


class GroupPotMemberStatus(enum.Enum):
    """E-11 status. Values verbatim from 04 §2."""

    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    DECLINED = "DECLINED"
    REMOVED = "REMOVED"
    LEFT = "LEFT"


class GroupPotApprovalStatus(enum.Enum):
    """E-12 status. Values verbatim from 04 §2."""

    PENDING = "PENDING"
    APPROVED_EXECUTED = "APPROVED_EXECUTED"
    REJECTED = "REJECTED"
    CANCELLED_UNREACHABLE = "CANCELLED_UNREACHABLE"
    EXPIRED = "EXPIRED"


class GroupPotApprovalDecisionType(enum.Enum):
    """E-13 decision. Values verbatim from 04 §2."""

    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SavingsGoal(Base, UUIDPrimaryKey, Timestamps):
    """E-9 SavingsGoal — personal sub-account pot under the Primary Savings
    Account (DEC-13, US-3.3). Valid Round-Up destination (DEC-12).

    04 lists `created_at`; it is provided by the Timestamps mixin (updated_at is
    additionally provided by the mixin — inferred, not listed in 04).
    """

    __tablename__ = "savings_goal"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    savings_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    name: Mapped[str] = mapped_column(String(60))
    emoji_or_image_ref: Mapped[Optional[str]] = mapped_column(String(255))
    target_amount = mapped_column(MoneyMinor)  # money, integer minor units
    target_date: Mapped[Optional[datetime.date]]
    # Derived from attributed LedgerEntries — materialized by the ledger service.
    current_amount = mapped_column(MoneyMinor)
    # {amount, frequency, source_account_id, next_run_at} — scheduled top-ups.
    auto_transfer: Mapped[dict] = mapped_column(JSON)


class GroupPot(Base, UUIDPrimaryKey, Timestamps):
    """E-10 GroupPot — shared multi-member pot with collective m-of-n approval
    (DEC-13, US-3.4). account_id is UQ (1—1 with a GROUP_POT Account).

    04 lists `created_at` (Timestamps mixin); updated_at is mixin-inferred.
    """

    __tablename__ = "group_pot"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id"), unique=True
    )
    creator_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    name: Mapped[str] = mapped_column(String(80))
    purpose: Mapped[str] = mapped_column(String(280))
    approval_threshold_m: Mapped[int] = mapped_column(Integer)
    status: Mapped[GroupPotStatus] = mapped_column(Enum(GroupPotStatus, name="group_pot_status"))


class GroupPotMember(Base, UUIDPrimaryKey, Timestamps):
    """E-11 GroupPotMember — membership of a pot. UQ(group_pot_id, member_id).

    invited_at/responded_at are the domain lifecycle timestamps; created_at/
    updated_at come from the Timestamps mixin.
    """

    __tablename__ = "group_pot_member"
    __table_args__ = (UniqueConstraint("group_pot_id", "member_id"),)

    group_pot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group_pot.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    role: Mapped[GroupPotMemberRole] = mapped_column(
        Enum(GroupPotMemberRole, name="group_pot_member_role")
    )
    invited_via: Mapped[RecipientIdentifierType] = mapped_column(
        Enum(RecipientIdentifierType, name="recipient_identifier_type")
    )
    status: Mapped[GroupPotMemberStatus] = mapped_column(
        Enum(GroupPotMemberStatus, name="group_pot_member_status")
    )
    total_contributed = mapped_column(MoneyMinor)  # derived from LedgerEntries
    invited_at: Mapped[datetime.datetime]
    responded_at: Mapped[Optional[datetime.datetime]]


class GroupPotApprovalRequest(Base, UUIDPrimaryKey, Timestamps):
    """E-12 GroupPotApprovalRequest — a pending outbound transfer awaiting m-of-n
    approval (US-3.5). transaction_id references a Transaction held PENDING with
    funds on hold (the hold is a ledger posting, not modelled here).

    expires_at/resolved_at are domain lifecycle timestamps; created_at/updated_at
    come from the Timestamps mixin.
    """

    __tablename__ = "group_pot_approval_request"

    group_pot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group_pot.id")
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    initiated_by_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    amount = mapped_column(MoneyMinor)  # money, integer minor units
    recipient: Mapped[dict] = mapped_column(JSON)
    purpose: Mapped[str] = mapped_column(String(280))
    required_approvals: Mapped[int] = mapped_column(Integer)  # snapshot of m at creation
    status: Mapped[GroupPotApprovalStatus] = mapped_column(
        Enum(GroupPotApprovalStatus, name="group_pot_approval_status")
    )
    expires_at: Mapped[datetime.datetime]
    resolved_at: Mapped[Optional[datetime.datetime]]


class GroupPotApprovalDecision(Base, UUIDPrimaryKey):
    """E-13 GroupPotApprovalDecision — one approver's decision on a request.
    UQ(approval_request_id, approver_member_id). Written to the pot ledger view
    and the immutable audit log (append-only; carries only its own `decided_at`,
    no Timestamps mixin — mirrors the LedgerEntry append-only precedent).
    """

    __tablename__ = "group_pot_approval_decision"
    __table_args__ = (UniqueConstraint("approval_request_id", "approver_member_id"),)

    approval_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("group_pot_approval_request.id")
    )
    approver_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    decision: Mapped[GroupPotApprovalDecisionType] = mapped_column(
        Enum(GroupPotApprovalDecisionType, name="group_pot_approval_decision")
    )
    decided_at: Mapped[datetime.datetime]
    auth_context: Mapped[dict] = mapped_column(JSON)  # step-up evidence
