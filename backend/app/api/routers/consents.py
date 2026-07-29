"""EP-1 member consent self-service router (04 §3.1).

Operations against the existing OpenAPI contract:

- listMyConsents   GET /api/v1/members/me/consents
                       -> 200 ConsentListResponse
- upsertMyConsent  PUT /api/v1/members/me/consents/{consent_type}
                       -> 200 ConsentListResponse

Both depend on `get_current_member` (the member-auth foundation). That dependency
IS the identity: the authenticated member is resolved from the verified token
subject, and NO member id is ever read from the path or the body. `consent_type`
comes from the path but only names WHICH consent document — never WHOSE. A member
can therefore only read or append to their OWN consent history — the IDOR class is
excluded by construction.

`ConsentRecord` is an APPEND-ONLY audit row (E-4): a grant or a withdrawal appends
a new immutable row, so `upsertMyConsent` never mutates history — it appends the
new state and returns the (now updated) history, exactly as the contract's `200
ConsentListResponse` prescribes. Withdrawing a service-required consent is refused
`409 CONSENT_REQUIRED_FOR_SERVICE`.

SECURITY: both operations are `memberOAuth2`-only in the contract (no step-up).
No money / ledger here.
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
from app.models.identity import ConsentRecord
from app.models.membership import Member
from app.services.identity import (
    ConsentService,
    IdentityServiceError,
    Page,
    parse_consent_action,
    parse_consent_type,
)

router = APIRouter(prefix="/api/v1/members", tags=["EP-1"])


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class ConsentRecordOut(BaseModel):
    """Mirrors the contract's append-only `ConsentRecord`."""

    id: uuid.UUID
    consent_type: str
    action: str
    version: str
    recorded_at: datetime.datetime
    channel: str


class ConsentListResponse(BaseModel):
    """Mirrors the contract's `ConsentListResponse` (GET + PUT share it)."""

    consent_records: list[ConsentRecordOut]
    next_cursor: Optional[str] = None  # noqa: UP045


class ConsentUpsertRequest(BaseModel):
    """Mirrors the contract's `ConsentUpsertRequest` (action + version).

    `channel` is not in the contract request schema but the ConsentRecord audit
    row requires one; a caller MAY supply it, otherwise the service defaults it.
    """

    action: str
    version: str
    channel: Optional[str] = None  # noqa: UP045


def _to_out(record: ConsentRecord) -> ConsentRecordOut:
    return ConsentRecordOut(
        id=record.id,
        consent_type=record.consent_type.value,
        action=record.action.value,
        version=record.version,
        recorded_at=record.recorded_at,
        channel=record.channel,
    )


def _to_response(page: Page) -> ConsentListResponse:
    return ConsentListResponse(
        consent_records=[_to_out(r) for r in page.records],
        next_cursor=page.next_cursor,
    )


# --- Routes ------------------------------------------------------------------


@router.get(
    "/me/consents",
    response_model=ConsentListResponse,
    summary="List the authenticated member's append-only consent history.",
)
def list_my_consents(
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
    cursor: Optional[str] = Query(default=None),  # noqa: UP045
    limit: Optional[int] = Query(default=None, ge=1, le=100),  # noqa: UP045
) -> ConsentListResponse:
    # No path/body member id: `get_current_member` is the sole identity source.
    try:
        page = ConsentService(session).list_history(
            member.id, cursor=cursor, limit=limit
        )
    except IdentityServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    return _to_response(page)


@router.put(
    "/me/consents/{consent_type}",
    response_model=ConsentListResponse,
    summary="Grant or withdraw a consent (appends an immutable record).",
)
def upsert_my_consent(
    consent_type: str,
    body: ConsentUpsertRequest,
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
) -> ConsentListResponse:
    if not body.version.strip():
        raise ApiError(422, "VALIDATION_FAILED", "`version` must be non-empty.")
    try:
        parsed_type = parse_consent_type(consent_type)
        parsed_action = parse_consent_action(body.action)
        page = ConsentService(session).upsert(
            member.id,
            consent_type=parsed_type,
            action=parsed_action,
            version=body.version,
            channel=body.channel,
        )
    except IdentityServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    # Router owns the transaction boundary (slice-1/2 convention: repos flush,
    # routers commit on mutation).
    session.commit()
    return _to_response(page)
