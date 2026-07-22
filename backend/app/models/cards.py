"""Card Management model (EP-5): E-18 Card.

ENTITY-GATED — DO NOT BUILD THE FEATURE. EP-5 (Cards) is very likely UNLAWFUL
for an SCC: SCCs have no payment-service power and none appears on the Bank of
Mongolia PSP register (CLAUDE.md, "Known defects"). Card issuing/authorization
is blocked until the entity decision.

This module therefore exists for SCHEMA COMPLETENESS ONLY. The E-18 table is a
faithful transcription of 04 §2.5 so the schema is whole and reviewable, but the
card FEATURE (issuance, Lithic authorization, controls evaluation, round-up
emission) is NOT implemented and must not be. Defining the table is fine;
wiring any behaviour to it is not, until Cards is cleared.

MARKET NOTE: `issuer_card_ref` is a Lithic vendor token in 04; the Mongolia
market clears cards through NETC (a Bank of Mongolia entity), not Lithic — the
vendor reference is modelled as 04 states it and flagged for the migration.
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


class CardType(enum.Enum):
    """E-18 card_type. Values verbatim from 04 §2.5."""

    VIRTUAL = "VIRTUAL"
    PHYSICAL = "PHYSICAL"


class CardStatus(enum.Enum):
    """E-18 status. Values verbatim from 04 §2.5."""

    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    ACTIVE = "ACTIVE"
    FROZEN = "FROZEN"
    REPORTED_LOST = "REPORTED_LOST"
    TERMINATED = "TERMINATED"


class Card(Base, UUIDPrimaryKey, Timestamps):
    """E-18 Card — virtual/physical debit card on the Transaction Account
    (US-5.1..US-5.3). PAN/CVV are never stored — issuer tokens only (PCI scope
    reduction). SCHEMA ONLY: see module docstring (EP-5 is entity-gated)."""

    __tablename__ = "card"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # funding_account_id references an Account of type TRANSACTION (04 §2.5).
    funding_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    card_type: Mapped[CardType] = mapped_column(Enum(CardType, name="card_type"))
    issuer_card_ref: Mapped[str] = mapped_column(String(255), unique=True)  # vendor token
    masked_pan: Mapped[Optional[str]] = mapped_column(String(32))  # display only
    expiry_month: Mapped[Optional[int]] = mapped_column(Integer)  # display only
    expiry_year: Mapped[Optional[int]] = mapped_column(Integer)  # display only
    # Physical only; copied VERBATIM from Member.mrz_name_latin (DEC-6) — never
    # transliterated from the Cyrillic name fields. No mrz_name_latin → no card.
    embossed_name: Mapped[Optional[str]] = mapped_column(String(120))
    status: Mapped[CardStatus] = mapped_column(Enum(CardStatus, name="card_status"))
    # Physical fulfilment {shipped_at?, carrier?, tracking_ref?, delivered_at?,
    # stage: ORDERED|PRINTED|SHIPPED|DELIVERED} (US-5.2).
    fulfilment = mapped_column(JSONB, nullable=True)
    # Authorization-time controls {per_period_limits[], channel_toggles{},
    # mcc_blocks[]} — evaluated by the (gated) card service, not here.
    controls = mapped_column(JSONB, nullable=True)
    # Apple Pay / Google Pay provisioning records (US-5.1).
    wallet_tokens = mapped_column(JSONB, nullable=True)
    # PIN itself lives at the issuer-processor only.
    pin_set: Mapped[bool] = mapped_column(Boolean, default=False)
    activated_at: Mapped[Optional[datetime.datetime]]
    terminated_at: Mapped[Optional[datetime.datetime]]
