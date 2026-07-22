"""Round-Up models (EP-10): E-47 RoundUpConfig, E-48 RoundUpCapture.

Table definitions only — no round-up computation, no batching, no transfer.
Derived from 04 §2.9 verbatim.

ENTITY-GATED (like Cards): EP-10 Round-Ups depend on card settlement events, so
they fall WITH Cards — which are very likely unlawful for an SCC (CLAUDE.md,
"Known defects"). These tables are modelled for SCHEMA COMPLETENESS; the round-up
FEATURE must not be built until the entity/Cards decision clears.

`batch_threshold` has a config default (04 says $5.00) — that is a
Configuration Registry value (US-12.5), NOT a schema constant, so no default
amount is baked into the column here. Amounts also need re-denominating to MNT
under the Mongolia migration (CLAUDE.md), and "whole-dollar" round-up semantics
become whole-MNT-unit semantics.

Two FK targets — SavingsGoal and CommunityProject — are defined in other model
slices, so they are modelled as bare UUID columns (not ForeignKey) to keep this
slice's model-gate self-contained; the relational intent is documented in-line.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


# --------------------------------------------------------------------------- #
# E-47 RoundUpConfig                                                           #
# --------------------------------------------------------------------------- #
class RoundUpDestinationType(enum.Enum):
    """E-47 destination_type. Values verbatim from 04 §2.9 — the ONLY two
    destinations (DEC-12)."""

    SAVINGS_GOAL = "SAVINGS_GOAL"
    COMMUNITY_PROJECT = "COMMUNITY_PROJECT"


class RoundUpConfig(Base, UUIDPrimaryKey, Timestamps):
    """E-47 RoundUpConfig — per-member Round-Up settings (DEC-12, US-10.1).
    One row per member. Changes take effect on the next card transaction."""

    __tablename__ = "roundup_config"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id"), unique=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    destination_type: Mapped[RoundUpDestinationType] = mapped_column(
        Enum(RoundUpDestinationType, name="roundup_destination_type")
    )
    # Logical FK→SavingsGoal (other slice) — bare UUID to keep the gate
    # self-contained; exactly one of these two is set per destination_type.
    savings_goal_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    # Logical FK→CommunityProject (other slice), which must be PUBLISHED.
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    multiplier: Mapped[int] = mapped_column(Integer, default=1)  # ∈ {1, 2, 3} (04)
    monthly_cap = mapped_column(MoneyMinor, nullable=True)  # money, optional
    accumulated_pending = mapped_column(MoneyMinor)  # money
    # Config default in 04 ($5.00) is a Configuration Registry value (US-12.5),
    # NOT hard-coded here — the column just stores the effective threshold.
    batch_threshold = mapped_column(MoneyMinor)  # money


# --------------------------------------------------------------------------- #
# E-48 RoundUpCapture                                                          #
# --------------------------------------------------------------------------- #
class RoundUpCaptureStatus(enum.Enum):
    """E-48 status. Values verbatim from 04 §2.9."""

    ACCUMULATED = "ACCUMULATED"
    TRANSFERRED = "TRANSFERRED"
    SKIPPED_INSUFFICIENT_FUNDS = "SKIPPED_INSUFFICIENT_FUNDS"
    SKIPPED_CAP = "SKIPPED_CAP"


class RoundUpCapture(Base, UUIDPrimaryKey, Timestamps):
    """E-48 RoundUpCapture — one computed round-up on a settled card
    transaction (US-10.2). Whole-unit transactions produce a 0 round-up. The
    transfer is a batched ROUND_UP_TRANSFER with clearly labeled ledger entries
    linking purchase and Round-Up (posted by the ledger service, not here)."""

    __tablename__ = "roundup_capture"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    card_transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id"), unique=True
    )
    base_amount = mapped_column(MoneyMinor)  # money
    roundup_amount = mapped_column(MoneyMinor)  # money; whole-unit purchase → 0
    multiplier_applied: Mapped[int] = mapped_column(Integer)
    capped: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[RoundUpCaptureStatus] = mapped_column(
        Enum(RoundUpCaptureStatus, name="roundup_capture_status")
    )
    transfer_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    captured_at: Mapped[Optional[datetime.datetime]]
