"""FastAPI dependencies shared across routers.

`get_session` is the one DB dependency every future feature route will use
(`Depends(get_session)`). It deliberately does NOT translate a missing DB into
an HTTP status here — at the scaffold stage there are no routes to decide that
for, and different routes may want different codes (503 vs 500). Mapping
`DatabaseNotConfigured` to a response is the calling route's job.
"""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy.orm import Session

from app.db.session import DatabaseNotConfigured, engine_configured, get_sessionmaker


def get_session() -> Iterator[Session]:
    """Yield a request-scoped `Session`, closed unconditionally afterwards.

    Raises `DatabaseNotConfigured` (uncaught here) if DATABASE_URL is empty.
    """
    if not engine_configured():
        raise DatabaseNotConfigured()
    session = get_sessionmaker()()
    try:
        yield session
    finally:
        session.close()
