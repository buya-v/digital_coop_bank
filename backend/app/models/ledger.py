"""Ledger-core tables (E-6 Account, E-7 LedgerEntry, E-8 Transaction).

THESE THREE ARE THE LEDGER CORE, and they carry the project's known unresolved
design. This module models the TABLE STRUCTURE only. It deliberately does NOT
encode any of the following — all of which are LOGIC or DATA decisions blocked on
a controller-reviewed CORRECTED ledger design (see CLAUDE.md / patterns.md;
06_ledger_addendum.md is do-not-implement, carrying five confirmed defects
including the inverted available-balance formula):

  - No posting logic, no double-entry enforcement, no balance derivation.
  - `balance` / `available_balance` are MATERIALIZED columns maintained by a
    ledger service that does not exist yet. Nothing may write them directly; the
    "available = balance − holds" rule (which 06 inverted) lives in that service,
    not here.
  - `entry_type` and the internal-account discriminator have UNDECIDED value sets
    (04's single `SYSTEM` enum and 06's chart-of-accounts are both incomplete),
    so they are modelled as `DeferredEnum` (String), NOT invented enums.
  - The 26-value `Transaction.type` is likewise deferred to String until the
    corrected design pins it.

Direction (DEBIT/CREDIT) and amount (MoneyMinor) ARE well-defined, so they are typed.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import BigInteger, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DeferredEnum, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


class AccountType(enum.Enum):
    """E-6 account_type. NOTE: 04 collapses every internal GL account into one
    `SYSTEM` value — a known gap (no chart of accounts). Member-facing types are
    sound; the internal breakdown is pending the corrected ledger design."""

    MEMBERSHIP_SHARE = "MEMBERSHIP_SHARE"
    PRIMARY_SAVINGS = "PRIMARY_SAVINGS"
    TRANSACTION = "TRANSACTION"
    GROUP_POT = "GROUP_POT"
    SYSTEM = "SYSTEM"  # PLACEHOLDER — see corrected chart of accounts (held)


class LedgerDirection(enum.Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"


class Account(Base, UUIDPrimaryKey, Timestamps):
    """E-6 Account. balance/available_balance are MATERIALIZED — maintained by
    the (not-yet-built) ledger service, never written directly."""

    __tablename__ = "account"

    owner_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    account_number: Mapped[str] = mapped_column(String(64), unique=True)
    account_type: Mapped[AccountType] = mapped_column(Enum(AccountType, name="account_type"))
    # Materialized, derived from ledger entries — DO NOT write directly (held).
    balance = mapped_column(MoneyMinor)
    available_balance = mapped_column(MoneyMinor)
    status: Mapped[str] = mapped_column(String(16))  # ACTIVE|FROZEN|CLOSED
    opened_at: Mapped[datetime.datetime]
    closed_at: Mapped[Optional[datetime.datetime]]


class Transaction(Base, UUIDPrimaryKey, Timestamps):
    """E-8 Transaction — the business-level money movement. `type` has ~26 values
    whose final set is pending the corrected design → DeferredEnum (String)."""

    __tablename__ = "transaction"

    idempotency_key: Mapped[Optional[str]] = mapped_column(String(128), unique=True)
    type: Mapped[str] = mapped_column(DeferredEnum)  # value set HELD
    status: Mapped[str] = mapped_column(String(16))  # PENDING|SETTLED|FAILED|...
    amount = mapped_column(MoneyMinor)
    external_ref: Mapped[Optional[str]] = mapped_column(String(128))
    settled_at: Mapped[Optional[datetime.datetime]]


class LedgerEntry(Base, UUIDPrimaryKey):
    """E-7 LedgerEntry — the double-entry posting line. Append-only by design;
    the append-only ENFORCEMENT and the ≥2-entries-sum-to-zero invariant live in
    the ledger service (held). `entry_type` is self-referential in 04 (~30 values)
    → DeferredEnum. `sequence` is per-account monotonic."""

    __tablename__ = "ledger_entry"

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    direction: Mapped[LedgerDirection] = mapped_column(
        Enum(LedgerDirection, name="ledger_direction")
    )
    amount = mapped_column(MoneyMinor)  # always positive; direction carries sign
    entry_type: Mapped[str] = mapped_column(DeferredEnum)  # value set HELD
    sequence: Mapped[int] = mapped_column(BigInteger)  # per-account monotonic
    posted_at: Mapped[datetime.datetime]
