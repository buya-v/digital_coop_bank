"""Compliance & transparency models (04 §2.11 — EP-12/EP-13): E-56..E-59.

Table definitions only. Money is MoneyMinor (E-59 total_managed_funds). Enums
are real where 04 lists their values (E-57 request_type/status, E-58 status);
`report_key` and hashes are open Strings. The audit hash chain and its
verification, WORM append-only enforcement, and retention/erasure automation are
all LOGIC — this module models only the columns those services read and write.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Any, Optional

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


class DataSubjectRequestType(enum.Enum):
    """E-57 `request_type`. Values verbatim from 04 §2.11."""

    ACCESS = "ACCESS"
    DELETION = "DELETION"
    RECTIFICATION = "RECTIFICATION"
    PORTABILITY = "PORTABILITY"


class DataSubjectRequestStatus(enum.Enum):
    """E-57 `status`. Values verbatim from 04 §2.11."""

    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_REDACTION = "PENDING_REDACTION"
    DELIVERED = "DELIVERED"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    REJECTED_LEGAL_BASIS = "REJECTED_LEGAL_BASIS"


class RegulatoryReportStatus(enum.Enum):
    """E-58 `status`. Values verbatim from 04 §2.11."""

    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SUBMITTED = "SUBMITTED"


class AuditLogEntry(Base, UUIDPrimaryKey):
    """E-56 AuditLogEntry — platform-wide, append-only, tamper-evident audit
    event; every service writes here (foundational). WORM (write-once-read-many):
    like LedgerEntry, this table is append-only, so it deliberately does NOT use
    the Timestamps mixin — an immutable record has no `updated_at`; its domain
    time is `occurred_at`. `prev_hash`/`entry_hash` are the tamper-evidence hash
    chain (04); they are String columns only — computing and VERIFYING the chain
    is the audit service's logic, not built here. `sequence` is monotonic."""

    __tablename__ = "audit_log_entry"

    sequence: Mapped[int] = mapped_column(BigInteger)  # monotonic
    prev_hash: Mapped[Optional[str]] = mapped_column(String(128))  # null at chain genesis
    entry_hash: Mapped[str] = mapped_column(String(128))
    actor: Mapped[dict[str, Any]] = mapped_column(JSONB)  # member/staff/system + auth ctx
    action: Mapped[str] = mapped_column(String(128))
    subject: Mapped[dict[str, Any]] = mapped_column(JSONB)  # entity type + id
    before: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    after: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    occurred_at: Mapped[datetime.datetime]
    correlation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))


class DataSubjectRequest(Base, UUIDPrimaryKey, Timestamps):
    """E-57 DataSubjectRequest — DSAR/deletion workflow with statutory deadline
    tracking. `retention_overrides` itemizes financial-records retention that
    lawfully overrides deletion; the automatic retention/erasure-by-record-class
    rules are logic, not modelled here."""

    __tablename__ = "data_subject_request"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    request_type: Mapped[DataSubjectRequestType] = mapped_column(
        Enum(DataSubjectRequestType, name="data_subject_request_type")
    )
    status: Mapped[DataSubjectRequestStatus] = mapped_column(
        Enum(DataSubjectRequestStatus, name="data_subject_request_status")
    )
    deadline_at: Mapped[datetime.datetime]
    fulfilment_package_ref: Mapped[Optional[str]] = mapped_column(String(512))
    retention_overrides: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    received_at: Mapped[datetime.datetime]
    resolved_at: Mapped[Optional[datetime.datetime]]


class RegulatoryReportRun(Base, UUIDPrimaryKey, Timestamps):
    """E-58 RegulatoryReportRun — one execution of a catalog report. `report_key`
    is an open String (report definitions are configuration-driven, Open Item 3 —
    no fixed value set to enumerate). `threshold_breaches` carries KPI-2.3/2.4/2.5
    breach alerts to P-5; producing them is logic."""

    __tablename__ = "regulatory_report_run"

    report_key: Mapped[str] = mapped_column(String(128))
    as_of: Mapped[datetime.datetime]  # point-in-time snapshot
    output_ref: Mapped[Optional[str]] = mapped_column(String(512))
    schedule_ref: Mapped[Optional[str]] = mapped_column(String(256))
    threshold_breaches: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    status: Mapped[RegulatoryReportStatus] = mapped_column(
        Enum(RegulatoryReportStatus, name="regulatory_report_status")
    )
    submission_log: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    run_at: Mapped[datetime.datetime]


class CapitalAllocationSnapshot(Base, UUIDPrimaryKey, Timestamps):
    """E-59 CapitalAllocationSnapshot — daily-or-better snapshot behind the
    Transparent Capital Ledger (DEC-15) and the Impact Scorecard attribution.
    `total_managed_funds` is money → MoneyMinor. `allocations` is per-category
    JSON `{amount, percentage}` reconciling to 100%; those nested per-category
    amounts are integer minor units too (they live inside the JSON structure, so
    they are not separate MoneyMinor columns) — the reconciliation-to-100% and
    the `"estimated"` labelling (DEC-15) are logic. `source_ledger_hash` is the
    reconciliation proof against the ledger (a String column; proving it is
    logic)."""

    __tablename__ = "capital_allocation_snapshot"

    as_of: Mapped[datetime.datetime] = mapped_column(unique=True)
    total_managed_funds = mapped_column(MoneyMinor)  # money, integer minor units (MNT)
    allocations: Mapped[dict[str, Any]] = mapped_column(JSONB)
    spotlights: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
    source_ledger_hash: Mapped[str] = mapped_column(String(128))
