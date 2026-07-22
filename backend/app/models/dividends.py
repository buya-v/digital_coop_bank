"""Patronage Dividend models (EP-7): E-31..E-33.

Table definitions only — no factor accumulation, no calculation run, no split
percentages baked in. Derived from 04 §2.7 verbatim.

SCORE-TYPE FLAG (REVIEW ME): E-31 types `loan_repayment_performance_score` and
`governance_participation_score` as `Decimal(5,4)` — 0..1 rate/score values,
NOT money. The model-gate forbids Numeric/Float on every column (to make
float-money mistakes impossible), so these Decimals cannot be stored as
Numeric. They are stored as a SCALED INTEGER: value ×10_000, giving an integer
in 0..10_000 that preserves the 4 decimal places of Decimal(5,4) exactly. The
application must divide by 10_000 to recover the score. This scaling choice is
the one design decision flagged for the reviewer (see handoff). Alternatives
considered: String (lossless but not comparable/aggregable in SQL) — rejected
in favour of the exact integer representation. NOT Float, NOT Numeric.

The money inputs on E-31 (avg_savings_balance, transaction_volume) ARE money →
MoneyMinor. The E-32 money fields likewise. `factor_weights` stays JSON; the
split percentages / weights are configuration (FINANCIAL_POLICY ballots), never
hard-coded here.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor

# Scaling factor for the Decimal(5,4) score columns (see module docstring).
SCORE_SCALE = 10_000  # value stored = round(score * SCORE_SCALE); 0..10_000


# --------------------------------------------------------------------------- #
# E-31 PatronageFactorRecord                                                   #
# --------------------------------------------------------------------------- #
class PatronagePeriod(enum.Enum):
    """E-31 period. 04 §2.7 lists a single value (MONTH); modelled as a real
    single-value enum rather than invented alternatives."""

    MONTH = "MONTH"


class PatronageFactorRecord(Base, UUIDPrimaryKey, Timestamps):
    """E-31 PatronageFactorRecord — per-member, per-period weighted patronage
    factors (DEC-10, US-7.1); feeds the real-time Dividend Estimator (US-7.3).
    Recomputable deterministically from ledger/governance history."""

    __tablename__ = "patronage_factor_record"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    fiscal_year: Mapped[int] = mapped_column(Integer)
    period: Mapped[PatronagePeriod] = mapped_column(
        Enum(PatronagePeriod, name="patronage_period")
    )
    # UQ(member, year, period_key) in 04. period_key identifies which month.
    period_key: Mapped[str] = mapped_column(String(16))  # e.g. "2026-01" (inferred format)
    # Money inputs.
    avg_savings_balance = mapped_column(MoneyMinor)
    transaction_volume = mapped_column(MoneyMinor)
    # Decimal(5,4) 0..1 SCORES — stored as scaled integer (×SCORE_SCALE); NOT
    # money, NOT Numeric/Float. See module docstring / handoff FLAG.
    loan_repayment_performance_score: Mapped[Optional[int]] = mapped_column(Integer)
    # Delegated participation counts for the delegator (DEC-16).
    governance_participation_score: Mapped[Optional[int]] = mapped_column(Integer)
    computed_at: Mapped[Optional[datetime.datetime]]


# --------------------------------------------------------------------------- #
# E-32 DividendDeclaration                                                     #
# --------------------------------------------------------------------------- #
class DividendDeclarationStatus(enum.Enum):
    """E-32 status. Values verbatim from 04 §2.7. Dual approval
    (MakerCheckerApproval) required before EXECUTING."""

    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    RECONCILED = "RECONCILED"
    CANCELLED = "CANCELLED"


class DividendDeclaration(Base, UUIDPrimaryKey, Timestamps):
    """E-32 DividendDeclaration — one annual Patronage Dividend run
    (DEC-10, US-7.1/US-12.6). Money fields are MoneyMinor; the 10% Community
    Grant split is NOT baked in (it is the ratified/config input, not a
    schema constant)."""

    __tablename__ = "dividend_declaration"

    fiscal_year: Mapped[int] = mapped_column(Integer, unique=True)
    # AGM-ratified input + mandatory linkage to the ratifying AGM record.
    ratified_surplus = mapped_column(MoneyMinor)
    agm_record_ref: Mapped[str] = mapped_column(String(255))
    distributable_pool = mapped_column(MoneyMinor)
    community_grant_allocation = mapped_column(MoneyMinor)  # the 10% pool feed (KPI-4.2)
    # Weights are configuration (FINANCIAL_POLICY ballots), never hard-coded.
    factor_weights = mapped_column(JSONB)
    # Logical reference to ConfigurationParameter (E-... defined in another slice).
    # Modelled as a bare UUID, NOT a ForeignKey, so this slice's model-gate stays
    # self-contained (the target table is not present in this worktree). The
    # relational intent is documented; wire the real FK when the schema is merged.
    factor_weights_config_ref: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    status: Mapped[DividendDeclarationStatus] = mapped_column(
        Enum(DividendDeclarationStatus, name="dividend_declaration_status")
    )
    calculation_run_ref: Mapped[Optional[str]] = mapped_column(String(255))
    reconciliation_report_ref: Mapped[Optional[str]] = mapped_column(String(255))
    declared_at: Mapped[Optional[datetime.datetime]]
    approved_at: Mapped[Optional[datetime.datetime]]
    executed_at: Mapped[Optional[datetime.datetime]]


# --------------------------------------------------------------------------- #
# E-33 DividendAllocation                                                      #
# --------------------------------------------------------------------------- #
class PayoutDestination(enum.Enum):
    """E-33 payout_destination. Values verbatim from 04 §2.7 — snapshot of the
    member's standing election at execution."""

    SAVINGS = "SAVINGS"
    SHARE_REINVESTMENT = "SHARE_REINVESTMENT"


class DividendAllocationStatus(enum.Enum):
    """E-33 status. Values verbatim from 04 §2.7."""

    CALCULATED = "CALCULATED"
    PAID = "PAID"
    REINVESTED = "REINVESTED"
    FAILED_RETRYING = "FAILED_RETRYING"
    ESCALATED = "ESCALATED"


class DividendAllocation(Base, UUIDPrimaryKey, Timestamps):
    """E-33 DividendAllocation — per-member entitlement within a declaration
    (US-7.1/US-7.2). UQ(declaration, member)."""

    __tablename__ = "dividend_allocation"

    dividend_declaration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dividend_declaration.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    entitlement_amount = mapped_column(MoneyMinor)
    # Full per-factor breakdown shown to the member.
    explainability = mapped_column(JSONB)
    payout_destination: Mapped[PayoutDestination] = mapped_column(
        Enum(PayoutDestination, name="payout_destination")
    )
    payout_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    reinvested_share_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("membership_share.id")
    )
    status: Mapped[DividendAllocationStatus] = mapped_column(
        Enum(DividendAllocationStatus, name="dividend_allocation_status")
    )
    paid_at: Mapped[Optional[datetime.datetime]]
    statement_ref: Mapped[Optional[str]] = mapped_column(String(255))
    tax_document_ref: Mapped[Optional[str]] = mapped_column(String(255))
