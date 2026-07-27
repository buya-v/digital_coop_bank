"""Generic repository base over a SQLAlchemy `Session`.

Deliberately tiny: `get` / `add` / `flush` are the only primitives every
aggregate needs. A repository never commits — transaction boundaries are owned
by the request-scoped session (`app.api.deps.get_session`); a `flush` only
surfaces DB-assigned values (PK, server defaults) within the open transaction.
"""
from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Session-backed data access for a single mapped model.

    Concrete subclasses bind `model` to the ORM class they manage and add
    query methods specific to that aggregate.
    """

    #: The mapped model this repository manages (set by each subclass).
    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, id_: uuid.UUID) -> ModelT | None:
        """Return the row by primary key, or None. No row lock."""
        return self.session.get(self.model, id_)

    def add(self, instance: ModelT) -> ModelT:
        """Stage a new instance for INSERT on the next flush/commit."""
        self.session.add(instance)
        return instance

    def flush(self) -> None:
        """Flush pending changes so DB-assigned values populate. Never commits."""
        self.session.flush()
