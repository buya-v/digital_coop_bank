"""FastAPI application entrypoint — scaffold only.

This is the skeleton the architecture-of-record hangs on. It exposes health and
readiness endpoints and NOTHING else: no member, account, ledger or payment
routes exist yet. Feature routers are added only after the OpenAPI contract
(derived from 04_technical_architecture.md) is in place and the entity/legal
questions in CLAUDE.md are resolved for each epic.
"""
from __future__ import annotations

from fastapi import FastAPI

from app.config import get_settings
from app.money import CURRENCY_CODE

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Scaffold. Currency is MNT (integer minor units). No feature endpoints "
        "yet — see docs/adr/0001-technology-stack.md."
    ),
)


@app.get("/health", tags=["ops"], summary="Liveness probe")
def health() -> dict:
    """Liveness: the process is up. No dependencies checked."""
    return {"status": "ok", "service": settings.app_name, "version": settings.version}


@app.get("/ready", tags=["ops"], summary="Readiness probe")
def ready() -> dict:
    """Readiness: the process is ready to serve.

    Currently trivial. When persistence lands, this checks the DB connection —
    and, per the ledger design, that the ledger is reachable before accepting
    money-movement traffic.
    """
    return {"status": "ready", "currency": CURRENCY_CODE}
