"""FastAPI application entrypoint — scaffold only.

This is the skeleton the architecture-of-record hangs on. It exposes health and
readiness endpoints and NOTHING else: no member, account, ledger or payment
routes exist yet. Feature routers are added only after the OpenAPI contract
(derived from 04_technical_architecture.md) is in place and the entity/legal
questions in CLAUDE.md are resolved for each epic.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterator
from typing import Optional

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import register_error_handlers
from app.api.routers.consents import router as consents_router
from app.api.routers.devices import router as devices_router
from app.api.routers.members import router as members_router
from app.api.routers.mfa import router as mfa_router
from app.api.routers.onboarding import router as onboarding_router
from app.api.routers.stepup import router as stepup_router
from app.auth.mfa import MfaCryptoNotConfigured
from app.config import get_settings
from app.db.session import DatabaseNotConfigured, engine_configured, get_engine
from app.money import CURRENCY_CODE

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Scaffold + EP-1 onboarding slice 1. Currency is MNT (integer minor "
        "units). See docs/adr/0001-technology-stack.md."
    ),
)

# Uniform error envelope (04 §3.0) + the EP-1 feature routers: pre-auth onboarding
# and the post-auth member self-service (getMyProfile / updateMyProfile, plus
# consent history and trusted-device listing).
register_error_handlers(app)
app.include_router(onboarding_router)
app.include_router(members_router)
app.include_router(consents_router)
app.include_router(devices_router)
app.include_router(mfa_router)
app.include_router(stepup_router)


async def _mfa_crypto_unavailable_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Fail closed when the MFA encryption key is missing/malformed.

    Returns the uniform Error envelope with a GENERIC message — the exception's
    text (which references configuration, never key material) is not leaked to the
    client. This makes a misconfigured key a clean "MFA unavailable", never a
    partial enrollment that stores an unprotected secret.
    """
    assert isinstance(exc, MfaCryptoNotConfigured)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "MFA_UNAVAILABLE",
                "message": "MFA enrollment is temporarily unavailable.",
                "correlation_id": str(uuid.uuid4()),
            }
        },
    )


app.add_exception_handler(MfaCryptoNotConfigured, _mfa_crypto_unavailable_handler)


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health() -> dict[str, str]:
    """Liveness: the process is up. No dependencies checked."""
    return {"status": "ok", "service": settings.app_name, "version": settings.version}


class _EngineUnavailable:
    """Sentinel yielded by `ready_session` when the DB is configured but its
    engine cannot even be BUILT — e.g. a non-empty-but-malformed DATABASE_URL,
    where `create_engine()` raises `ArgumentError` before any connection is made.

    Its `execute()` raises, so `/ready` reports the failure through its EXISTING
    error path (503 `{status: unready, db: error}`, exception text never leaked) —
    exactly as it does for a runtime liveness failure — instead of letting the
    build error escape during dependency resolution as an uncaught 500.
    """

    def execute(self, *_args: object, **_kwargs: object) -> object:
        raise DatabaseNotConfigured()


def ready_session() -> Iterator["Session | _EngineUnavailable | None"]:
    """Session dependency for `/ready` ONLY — not for feature routes.

    Yields `None` when no DB is configured instead of raising
    `DatabaseNotConfigured`, so the unconfigured branch of `/ready` never
    touches DB machinery and the whole check is a single dependency that
    tests can swap with `app.dependency_overrides[ready_session] = ...`.

    When a DB IS configured but building its engine fails (e.g. a malformed
    DATABASE_URL -> `ArgumentError`), yields an `_EngineUnavailable` sentinel so
    the route renders 503 via its normal error path rather than 500 — the build
    error is caught here, never during dependency resolution.

    Real feature routes must keep using `Depends(app.api.deps.get_session)`
    directly, which stays strict (raises on a missing DB) — that strictness
    is deliberate there; `/ready`'s job is precisely to report "unconfigured"
    as a normal state instead of an error.
    """
    if not engine_configured():
        yield None
        return
    try:
        # Build (once, cached) the engine up front. A non-empty-but-malformed
        # DATABASE_URL raises ArgumentError HERE rather than mid-request, so it is
        # caught instead of escaping during dependency resolution as a 500.
        get_engine()
    except Exception:  # noqa: BLE001 — a readiness probe never lets a build error
        # (malformed URL, driver import failure, ...) escape as a 500; it reports
        # "unready" and lets the route own the 503 + no-leak envelope.
        yield _EngineUnavailable()
        return
    yield from get_session()


@app.get("/ready", tags=["ops"], summary="Readiness probe")
def ready(
    response: Response,
    # `Optional[...]` not `X | None`: this parameter's annotation is evaluated
    # at runtime by FastAPI/pydantic to build the route's dependant. The PEP
    # 604 `|` union needs `type.__or__`, added in 3.10 — the documented local
    # dev machine here runs 3.9 (see backend/README.md "Local limits"), where
    # evaluating that string raises. `Optional[Session]` works on 3.9 and
    # 3.11+ (CI) alike.
    session: Optional[Session] = Depends(ready_session),  # noqa: UP045
) -> dict[str, str]:
    """Readiness: DB liveness check.

    - No DB configured (scaffold/dev without Postgres): HTTP 200,
      `{"status": "degraded", "db": "unconfigured"}` — a valid state, not an
      outage.
    - DB configured and reachable: HTTP 200, `{"status": "ready", "db": "ok"}`
      after a `SELECT 1` round trip.
    - DB configured but unreachable (or any other error running the check):
      HTTP 503, `{"status": "unready", "db": "error"}`. The underlying
      exception is caught and never included in the response body.
    """
    if session is None:
        return {"status": "degraded", "db": "unconfigured", "currency": CURRENCY_CODE}
    try:
        session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — deliberately broad: a liveness probe
        # must turn ANY failure (driver error, closed pool, a leaked
        # DatabaseNotConfigured, ...) into 503 without ever leaking the
        # exception's text into the response body.
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "db": "error", "currency": CURRENCY_CODE}
    return {"status": "ready", "db": "ok", "currency": CURRENCY_CODE}
