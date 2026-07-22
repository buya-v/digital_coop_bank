"""Declarative base and shared column mixins for all ORM models.

Every entity model (derived from 04_technical_architecture.md §2) inherits from
`Base`. The metadata naming convention gives every constraint a deterministic
name, which Alembic needs to emit stable, reviewable migrations — and which the
ledger design needs so its integrity constraints can be referred to by name.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import MetaData, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Deterministic constraint names (Alembic-friendly, ledger integrity by name).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UUIDPrimaryKey:
    """Mixin: a UUID primary key. 04 §2 uses `id UUID PK` on nearly every entity."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class Timestamps:
    """Mixin: created/updated timestamps. 04 §2 uses *_at fields widely."""

    created_at: Mapped[datetime.datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )


# Convenience: a short string type for the deferred-enum columns. Where 04 or
# the (defective) ledger addendum leave an enum's value set undecided — most
# importantly LedgerEntry.entry_type and the internal-account discriminator —
# a model uses `DeferredEnum` (a String) with a comment, rather than inventing
# the value set. The enum is pinned later, from the CORRECTED ledger design.
DeferredEnum = String(64)
