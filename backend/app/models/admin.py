"""Admin/back-office models (04 §2.11 — EP-12): E-52..E-55.

Table definitions only. Staff are a SEPARATE realm from members (P-5): a
StaffUser is never a Member row. Enums are real where 04 lists their values
(StaffRole, statuses, case/priority sets); `action_type` and config `key` are
open Strings in 04 and stay String. Maker-checker's "checker ≠ maker" and
maker-checker-everywhere are LOGIC/constraint concerns — the columns are here,
the enforcement is not.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey


class StaffRole(enum.Enum):
    """E-52 `roles[]`. Values verbatim from 04 §2.11 (RBAC matrix §5.1)."""

    OPS_ADMIN = "OPS_ADMIN"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    LOAN_OFFICER = "LOAN_OFFICER"
    GOVERNANCE_ADMIN = "GOVERNANCE_ADMIN"
    FINANCE_ADMIN = "FINANCE_ADMIN"
    AUDITOR = "AUDITOR"
    SUPER_ADMIN = "SUPER_ADMIN"


class StaffStatus(enum.Enum):
    """E-52 `status`. Values verbatim from 04 §2.11."""

    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DEACTIVATED = "DEACTIVATED"


class ApprovalStatus(enum.Enum):
    """E-53 `status`. Values verbatim from 04 §2.11."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ComplianceCaseType(enum.Enum):
    """E-54 `case_type`. Values verbatim from 04 §2.11."""

    KYC_REVIEW = "KYC_REVIEW"
    AML_ALERT = "AML_ALERT"
    SAR = "SAR"
    FRAUD = "FRAUD"
    DISPUTE = "DISPUTE"


class ComplianceCasePriority(enum.Enum):
    """E-54 `priority`. Values verbatim from 04 §2.11."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceCaseStatus(enum.Enum):
    """E-54 `status`. Values verbatim from 04 §2.11."""

    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_REVIEW = "IN_REVIEW"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ESCALATED = "ESCALATED"
    CLOSED_APPROVED = "CLOSED_APPROVED"
    CLOSED_REJECTED = "CLOSED_REJECTED"
    CLOSED_FILED = "CLOSED_FILED"
    CLOSED_NO_ACTION = "CLOSED_NO_ACTION"


class StaffUser(Base, UUIDPrimaryKey, Timestamps):
    """E-52 StaffUser — P-5 back-office identity, a realm distinct from members.
    MFA is mandatory (a policy/auth concern, not a column). `roles` is Enum[] in
    04 → an array of StaffRole."""

    __tablename__ = "staff_user"

    staff_idp_id: Mapped[str] = mapped_column(String(128), unique=True)
    display_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True)
    roles: Mapped[list[StaffRole]] = mapped_column(
        ARRAY(Enum(StaffRole, name="staff_role"))
    )
    status: Mapped[StaffStatus] = mapped_column(Enum(StaffStatus, name="staff_status"))


class MakerCheckerApproval(Base, UUIDPrimaryKey, Timestamps):
    """E-53 MakerCheckerApproval — the generic four-eyes envelope for every
    mutating back-office action. `checker_staff_id` MUST differ from
    `maker_staff_id` (04: enforced at the data layer); that inequality is a
    constraint/logic concern — modelled here only as the two FK columns plus this
    note, not encoded. `action_type` is an open String in 04 (examples:
    MEMBER_STATUS_TRANSITION, CONFIG_CHANGE, DIVIDEND_EXECUTION) — no value set is
    listed, so it stays String rather than an invented enum."""

    __tablename__ = "maker_checker_approval"

    action_type: Mapped[str] = mapped_column(String(64))
    subject_ref: Mapped[dict[str, Any]] = mapped_column(JSONB)  # target entity type + id
    proposed_change: Mapped[dict[str, Any]] = mapped_column(JSONB)  # before/after
    maker_staff_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_user.id")
    )
    # Optional until a checker acts; must differ from maker (enforced in logic).
    checker_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_user.id")
    )
    status: Mapped[ApprovalStatus] = mapped_column(
        Enum(ApprovalStatus, name="approval_status")
    )
    maker_note: Mapped[Optional[str]] = mapped_column(String(2000))
    checker_note: Mapped[Optional[str]] = mapped_column(String(2000))
    decided_at: Mapped[Optional[datetime.datetime]]


class ComplianceCase(Base, UUIDPrimaryKey, Timestamps):
    """E-54 ComplianceCase — unified work-queue case for KYC escalations, AML
    alerts and SAR workflow. Tipping-off safeguard (04): a SAR case must have NO
    member-visible trace, ever — an access-control/logic obligation, noted here,
    not modelled as a column. `sar_package` dual-review is maker-checker logic."""

    __tablename__ = "compliance_case"

    case_type: Mapped[ComplianceCaseType] = mapped_column(
        Enum(ComplianceCaseType, name="compliance_case_type")
    )
    subject_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    source_refs: Mapped[dict[str, Any]] = mapped_column(JSONB)
    alert_details: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    sar_package: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    assigned_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_user.id")
    )
    sla_due_at: Mapped[datetime.datetime]
    priority: Mapped[ComplianceCasePriority] = mapped_column(
        Enum(ComplianceCasePriority, name="compliance_case_priority")
    )
    status: Mapped[ComplianceCaseStatus] = mapped_column(
        Enum(ComplianceCaseStatus, name="compliance_case_status")
    )
    opened_at: Mapped[datetime.datetime]
    closed_at: Mapped[Optional[datetime.datetime]]


class ConfigurationParameter(Base, UUIDPrimaryKey, Timestamps):
    """E-55 ConfigurationParameter — the versioned, effective-dated RUNTIME
    config registry (US-12.5). This is where seed values (share par, P2P limits,
    round-up threshold, common-bond rules) live AT RUNTIME, so `value` is an OPEN
    type (JSONB): the row structure is modelled, but NO specific seed value is
    baked in as a column default — a parameter is whatever the current effective
    version holds. `key` has no listed value set (04 gives examples only) → open
    String. `governing_ballot_id` references the governance Ballot (E-33, another
    slice); it is a bare UUID here — the FK is intentionally NOT enforced across
    slices in this worktree (no ballot table present), noted for the merge."""

    __tablename__ = "configuration_parameter"
    __table_args__ = (UniqueConstraint("key", "version"),)  # UQ(key, version)

    key: Mapped[str] = mapped_column(String(128))
    value: Mapped[Any] = mapped_column(JSONB)  # OPEN type — never a baked seed value
    version: Mapped[int] = mapped_column(Integer)
    effective_from: Mapped[datetime.datetime]
    effective_to: Mapped[Optional[datetime.datetime]]
    approval_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("maker_checker_approval.id")
    )
    # Mandatory when the parameter is governed by a certified FINANCIAL_POLICY /
    # GOVERNANCE_BYLAW ballot outcome. Cross-slice ref to Ballot (governance) —
    # kept as a plain UUID; conditional-mandatoriness is logic, not a column.
    governing_ballot_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("ballot.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("staff_user.id")
    )
