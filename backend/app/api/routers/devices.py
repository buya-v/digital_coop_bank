"""EP-1 member device self-service router (04 §3.1).

Operation against the existing OpenAPI contract:

- listDevices  GET /api/v1/auth/devices  -> 200 DeviceListResponse

Depends on `get_current_member` (the member-auth foundation). That dependency IS
the identity: the authenticated member is resolved from the verified token
subject, and NO member id is ever read from the path, query or body. A member can
therefore only ever list their OWN trusted devices — the IDOR class is excluded by
construction. "Trusted" is ACTIVE bindings only; a revoked binding is not returned.

DEFERRED: `revokeDevice` (DELETE /api/v1/auth/devices/{id}) is NOT built here. Its
contract `security` requires a `stepUpAssertion` in addition to the session
(04 §3.1 / US-1.4), and step-up is a later slice. Only the `memberOAuth2`-only
listDevices operation is implemented in this slice. No money / ledger here.
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
from app.auth.deps import get_current_member
from app.models.identity import DeviceBinding
from app.models.membership import Member
from app.services.identity import DevicePage, DeviceService, IdentityServiceError

router = APIRouter(prefix="/api/v1/auth", tags=["EP-1"])


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
