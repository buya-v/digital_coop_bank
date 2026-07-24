"""SYNC engine + session factory — the persistence entry point.

Deliberately synchronous. Async (`create_async_engine`/`AsyncSession`) is a
real architectural choice this scaffold has not made yet — introducing it here
would silently commit the whole codebase to it. This module stays plain
SQLAlchemy 2.0 + psycopg3 until that decision is made explicitly.

Both the engine and the sessionmaker are built LAZILY. `DATABASE_URL` is empty
on this dev machine (no Postgres here — see CLAUDE.md blocking question #3 on
data residency, which also means the eventual DB host is operator-chosen, not
assumed). Importing this module must never connect and never raise; only
calling `get_engine()` / `get_sessionmaker()` without a configured URL raises,
so `/health` and any DB-free code path stay import-safe.
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


class DatabaseNotConfigured(RuntimeError):
    """Raised when DB access is attempted but DATABASE_URL is unset/empty."""

    def __init__(self) -> None:
        super().__init__(
            "DATABASE_URL is not set — no database is configured. Set it to a "
            "psycopg3 URL, e.g. postgresql+psycopg://user:pass@host:5432/dbname "
            "(see backend/docker-compose.yml for the local convention)."
        )


_engine: Engine | None = None
_sessionmaker: sessionmaker[Session] | None = None


def engine_configured() -> bool:
    """True iff a non-empty DATABASE_URL is present. Never connects."""
    return bool(get_settings().database_url)


def get_engine() -> Engine:
    """Build (once) and return the module-level Engine.

    Raises `DatabaseNotConfigured` if DATABASE_URL is empty rather than let
    SQLAlchemy fail later with an opaque URL-parsing error.
    """
    global _engine
    if _engine is None:
        if not engine_configured():
            raise DatabaseNotConfigured()
        _engine = create_engine(get_settings().database_url)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    """Build (once) and return a `sessionmaker` bound to `get_engine()`.

    `expire_on_commit=False`: the ledger's append-only, request-scoped usage
    pattern reads committed values back without a second round trip.
    """
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(bind=get_engine(), class_=Session, expire_on_commit=False)
    return _sessionmaker
