"""EP-1 member device self-service router (04 §3.1).

Operations against the existing OpenAPI contract:

- listDevices   GET    /api/v1/auth/devices       -> 200 DeviceListResponse
- revokeDevice  DELETE /api/v1/auth/devices/{id}   -> 200 DeviceRevokeResponse

Both depend on `get_current_member` (the member-auth foundation). That dependency
IS the identity: the authenticated member is resolved from the verified token
subject, and NO member id is ever read from the path, query or body. A member can
therefore only ever list or revoke their OWN devices — the IDOR class is excluded
by construction (a foreign device id resolves to 404, never a cross-member reveal).
"Trusted" is ACTIVE bindings only; a revoked binding is not returned by list.

`revokeDevice` is additionally gated by `require_step_up`: the contract marks the
delete as step-up (04 §3.1 / US-1.4), so it requires a FRESH single-use
`X-Step-Up-Token` (minted by `POST /auth/step-up`) IN ADDITION to the session. No
money / ledger here.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import ApiError
from app.auth.deps import get_current_member, require_step_up
from app.models.identity import DeviceBinding, StepUpToken
from app.models.membership import Member
from app.services.identity import DevicePage, DeviceService, IdentityServiceError

router = APIRouter(prefix="/api/v1/auth", tags=["EP-1"])

# The step-up dependency for revokeDevice, built once at import (a module-level
# singleton, not a call in an argument default). A token minted with a scoped
# `requested_action` must equal "revokeDevice"; a general (unscoped) token also
# passes.
_require_revoke_step_up = require_step_up("revokeDevice")


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class DeviceOut(BaseModel):
    """Mirrors the contract's `Device` (E-3 DeviceBinding summary)."""

    id: uuid.UUID
    platform: str
    bound_at: datetime.datetime
    last_seen_at: datetime.datetime


class DeviceListResponse(BaseModel):
    """Mirrors the contract's `DeviceListResponse`."""

    devices: list[DeviceOut]
    next_cursor: Optional[str] = None  # noqa: UP045


class DeviceRevokeResponse(BaseModel):
    """Mirrors the contract's `DeviceRevokeResponse` (status pinned to REVOKED)."""

    status: str = "REVOKED"


def _to_out(device: DeviceBinding) -> DeviceOut:
    return DeviceOut(
        id=device.id,
        platform=device.platform.value,
        bound_at=device.bound_at,
        last_seen_at=device.last_seen_at,
    )


def _to_response(page: DevicePage) -> DeviceListResponse:
    return DeviceListResponse(
        devices=[_to_out(d) for d in page.devices],
        next_cursor=page.next_cursor,
    )


# --- Routes ------------------------------------------------------------------


@router.get(
    "/devices",
    response_model=DeviceListResponse,
    summary="List the authenticated member's trusted devices.",
)
def list_devices(
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
    cursor: Optional[str] = Query(default=None),  # noqa: UP045
    limit: Optional[int] = Query(default=None, ge=1, le=100),  # noqa: UP045
) -> DeviceListResponse:
    # No path/body member id: `get_current_member` is the sole identity source.
    try:
        page = DeviceService(session).list_devices(
            member.id, cursor=cursor, limit=limit
        )
    except IdentityServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    return _to_response(page)


@router.delete(
    "/devices/{id}",
    response_model=DeviceRevokeResponse,
    summary="Revoke one of the authenticated member's trusted devices (step-up required).",
)
def revoke_device(
    id: uuid.UUID,
    member: Member = Depends(get_current_member),
    # Step-up is REQUIRED and consumed here: the dependency verifies + spends a
    # single-use X-Step-Up-Token bound to this member before the body runs. It also
    # re-uses `get_current_member`, which FastAPI resolves once per request, so
    # `member` below is the same authenticated member.
    _step_up: StepUpToken = Depends(_require_revoke_step_up),
    session: Session = Depends(get_session),
) -> DeviceRevokeResponse:
    # The device id comes from the path but is ALWAYS scoped to `member.id` in the
    # service — another member's id yields 404, never a cross-member revoke.
    try:
        device = DeviceService(session).revoke_device(member.id, id)
    except IdentityServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    # Router owns the transaction boundary (service flushes; router commits).
    session.commit()
    return DeviceRevokeResponse(status=device.status.value)
