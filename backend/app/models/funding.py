"""Community Funding Hub models (EP-9) — 04 §2.9, entities E-43..E-46.

Table definitions only; no all-or-nothing refund logic, no match accrual, and no
pool/cap exhaustion logic (that is application behaviour). All money is MoneyMinor
(BIGINT minor units) — never float, per the non-negotiable. Derived money columns
(project totals, pool committed/disbursed, match accrued/released) are maintained
by the funding/ledger services, not written directly.

Round-Ups (EP-10, E-47/E-48) are OUT of this slice; note also that EP-10 is flagged
as likely unlawful for an SCC (CLAUDE.md), so Backing.source=ROUND_UP is modelled
only because 04 lists it as a value — no round-up capture is built here.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


# --- Enums (values verbatim from 04 §2.9) ---

class CommunityProjectStatus(enum.Enum):
    """E-43 status."""

    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    PUBLISHED = "PUBLISHED"
    DECLINED = "DECLINED"
    FUNDED = "FUNDED"
    UNSUCCESSFUL_REFUNDED = "UNSUCCESSFUL_REFUNDED"
    COMPLETED = "COMPLETED"


class BackingSource(enum.Enum):
    """E-44 source."""

    SAVINGS = "SAVINGS"
    ROUND_UP = "ROUND_UP"


class BackingStatus(enum.Enum):
    """E-44 status."""

    SETTLED = "SETTLED"
    REFUNDED = "REFUNDED"


class GrantPoolStatus(enum.Enum):
    """E-45 status."""

    OPEN = "OPEN"
    EXHAUSTED = "EXHAUSTED"
    CLOSED = "CLOSED"


class SurplusMatchStatus(enum.Enum):
    """E-46 status."""

    ACCRUING = "ACCRUING"
    PENDING_BALLOT = "PENDING_BALLOT"
    RELEASED = "RELEASED"
    HALTED_CAP = "HALTED_CAP"
    HALTED_POOL = "HALTED_POOL"


# --- Tables ---

class CommunityProject(Base, UUIDPrimaryKey, Timestamps):
    """E-43 CommunityProject — a Pitch Board listing (DEC-14, US-9.1). Submitter is
    a member OR a registered org (submitter_org JSON). `amount_*` are derived
    aggregates maintained by the services. Impact figures are labelled 'estimated'
    (DEC-15) — a data concern, not a schema one."""

    __tablename__ = "community_project"

    submitter_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    submitter_org = mapped_column(JSONB)  # registered local organization
    title: Mapped[str] = mapped_column(String(120))
    goals: Mapped[str] = mapped_column(Text)
    budget = mapped_column(JSONB)
    timeline = mapped_column(JSONB)
    impact_description: Mapped[str] = mapped_column(Text)
    documents = mapped_column(JSONB)  # object refs
    funding_goal = mapped_column(MoneyMinor)
    deadline: Mapped[datetime.datetime]
    all_or_nothing: Mapped[bool] = mapped_column(Boolean)
    # Derived aggregates — maintained by the funding/ledger services.
    amount_backed = mapped_column(MoneyMinor)
    amount_matched = mapped_column(MoneyMinor)
    amount_disbursed = mapped_column(MoneyMinor)
    status: Mapped[CommunityProjectStatus] = mapped_column(
        Enum(CommunityProjectStatus, name="community_project_status")
    )
    review = mapped_column(JSONB)  # approve/decline reasons (US-12 review queue)
    updates = mapped_column(JSONB)  # 1..N project-poster updates
    impact_report = mapped_column(JSONB)  # raised/matched/disbursed + outcomes
    published_at: Mapped[Optional[datetime.datetime]]


class Backing(Base, UUIDPrimaryKey, Timestamps):
    """E-44 Backing — a member's contribution from Primary Savings (DEC-14, US-9.2).
    `amount` is money (MoneyMinor). Refunds are a separate reversing transaction
    (refund_transaction_id), not a mutation."""

    __tablename__ = "backing"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_project.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    amount = mapped_column(MoneyMinor)
    recurring = mapped_column(JSONB)  # {frequency, next_run_at}
    source: Mapped[BackingSource] = mapped_column(Enum(BackingSource, name="backing_source"))
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    refund_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    status: Mapped[BackingStatus] = mapped_column(Enum(BackingStatus, name="backing_status"))


class CommunityGrantPool(Base, UUIDPrimaryKey, Timestamps):
    """E-45 CommunityGrantPool — surplus-funded pool, one per fiscal year (DEC-14).
    `budget`/`committed`/`disbursed` are money (MoneyMinor); committed/disbursed are
    derived. `pool_account_id` is a SYSTEM Account.

    `funded_from_declaration_id` references E-32 DividendDeclaration, which lives in
    the Dividend Service slice (S-7) and is NOT defined in this slice — so it is a
    plain UUID column here, not a ForeignKey (a cross-slice FK would break the
    standalone gate). The relational FK is wired up at integration when both slices
    share one Base.metadata. [INFERRED cross-slice link — flagged for integration.]"""

    __tablename__ = "community_grant_pool"
    __table_args__ = (UniqueConstraint("fiscal_year"),)

    fiscal_year: Mapped[int] = mapped_column(Integer)
    # Cross-slice reference to E-32 DividendDeclaration (Dividend Service, S-7).
    funded_from_declaration_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    pool_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    budget = mapped_column(MoneyMinor)
    committed = mapped_column(MoneyMinor)  # derived
    disbursed = mapped_column(MoneyMinor)  # derived
    status: Mapped[GrantPoolStatus] = mapped_column(
        Enum(GrantPoolStatus, name="grant_pool_status")
    )


class SurplusMatch(Base, UUIDPrimaryKey, Timestamps):
    """E-46 SurplusMatch — match accrual/release for one project (<= 1:1, DEC-14).
    `match_ratio_bps` is a stored integer (<= 10000 = 1:1) — the ratio is data, not
    a baked constant. Release is governed by a certified COMMUNITY_GRANT ballot
    (release_ballot_id), never staff discretion (enforced in the service).
    UQ(pool, project)."""

    __tablename__ = "surplus_match"
    __table_args__ = (UniqueConstraint("pool_id", "project_id"),)

    pool_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_grant_pool.id")
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_project.id")
    )
    match_ratio_bps: Mapped[int] = mapped_column(Integer)  # <= 10000 = 1:1
    project_cap = mapped_column(MoneyMinor)
    accrued_amount = mapped_column(MoneyMinor)
    release_ballot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    released_amount = mapped_column(MoneyMinor)
    release_transaction_ids = mapped_column(ARRAY(UUID(as_uuid=True)))  # traceability
    status: Mapped[SurplusMatchStatus] = mapped_column(
        Enum(SurplusMatchStatus, name="surplus_match_status")
    )
