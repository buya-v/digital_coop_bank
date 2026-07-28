"""EP-1 member self-service router (04 §3.1) — the first POST-AUTH feature router.

Operations against the existing OpenAPI contract:

- getMyProfile     GET   /api/v1/members/me          -> 200 MemberProfile
- updateMyProfile  PATCH /api/v1/members/me/profile  -> 200 ProfilePatchResponse

Both depend on `get_current_member` (the member-auth foundation). That dependency
IS the identity: the authenticated member is resolved from the verified token
subject, and NO member id is ever read from the path or the body. A member can
therefore only read or write their OWN profile — the IDOR class is excluded by
construction, not by a check that could be forgotten.

`legal_name` is DERIVED (from the Cyrillic name parts) and read-only; the editable
set is the DEC-6 name parts + structured address + contact channels. Supplying
`legal_name` / `mrz_name_latin` / `registration_number` / `member_id` (KYC /
derived / system-owned) is rejected 422. No money / ledger / share here.
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import ApiError
from app.auth.deps import get_current_member
from app.models.membership import Member
from app.services.profile import (
    ProfileFieldNotEditable,
    ProfileFieldUnknown,
    ProfileService,
)

router = APIRouter(prefix="/api/v1/members", tags=["EP-1"])


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class MemberProfile(BaseModel):
    """The member-facing profile (a populatable subset of the contract's
    MemberProfile; unmodelled optional fields are simply omitted). `legal_name`
    is DERIVED read-only."""

    id: uuid.UUID
    member_id: str
    ner: str
    etsgiin_ner: str
    ovog: Optional[str] = None  # noqa: UP045
    legal_name: str
    mrz_name_latin: Optional[str] = None  # noqa: UP045
    registration_number: Optional[str] = None  # noqa: UP045
    address_line_1: Optional[str] = None  # noqa: UP045
    address_line_2: Optional[str] = None  # noqa: UP045
    city: Optional[str] = None  # noqa: UP045
    region: Optional[str] = None  # noqa: UP045
    postal_code: Optional[str] = None  # noqa: UP045
    country: Optional[str] = None  # noqa: UP045
    email: str
    phone_number: str
    membership_status: str


class ProfilePatchRequest(BaseModel):
    # Mirrors the contract's ProfilePatchRequest. `extra="allow"` so a client that
    # tries to set a read-only/derived field (`legal_name`, `mrz_name_latin`,
    # `member_id`) is DETECTED and rejected 422 — rather than the field being
    # silently ignored. Declared fields keep their types; the service decides
    # which are actually editable.
    model_config = ConfigDict(extra="allow")

    ner: Optional[str] = None  # noqa: UP045
    etsgiin_ner: Optional[str] = None  # noqa: UP045
    ovog: Optional[str] = None  # noqa: UP045
    registration_number: Optional[str] = None  # noqa: UP045
    address_line_1: Optional[str] = None  # noqa: UP045
    address_line_2: Optional[str] = None  # noqa: UP045
    city: Optional[str] = None  # noqa: UP045
    region: Optional[str] = None  # noqa: UP045
    postal_code: Optional[str] = None  # noqa: UP045
    country: Optional[str] = None  # noqa: UP045
    email: Optional[str] = None  # noqa: UP045
    phone_number: Optional[str] = None  # noqa: UP045


class ProfilePatchResponse(BaseModel):
    profile: MemberProfile
    reverification_required: bool


def _to_profile(member: Member) -> MemberProfile:
    """Project a Member row onto the profile response (legal_name derived)."""
    return MemberProfile(
        id=member.id,
        member_id=member.member_id,
        ner=member.ner,
        etsgiin_ner=member.etsgiin_ner,
        ovog=member.ovog,
        legal_name=member.legal_name,
        mrz_name_latin=member.mrz_name_latin,
        registration_number=member.registration_number,
        address_line_1=member.address_line_1,
        address_line_2=member.address_line_2,
        city=member.city,
        region=member.region,
        postal_code=member.postal_code,
        country=member.country,
        email=member.email,
        phone_number=member.phone_number,
        membership_status=member.membership_status.value,
    )


# --- Routes ------------------------------------------------------------------


@router.get(
    "/me",
    response_model=MemberProfile,
    summary="Get the authenticated member's profile.",
)
def get_my_profile(
    member: Member = Depends(get_current_member),
) -> MemberProfile:
    # No path/body member id: `get_current_member` is the sole identity source.
    return _to_profile(member)


@router.patch(
    "/me/profile",
    response_model=ProfilePatchResponse,
    summary="Update the authenticated member's editable profile fields.",
)
def update_my_profile(
    body: ProfilePatchRequest,
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
) -> ProfilePatchResponse:
    provided = body.model_dump(exclude_unset=True)
    service = ProfileService()
    try:
        reverification_required = service.apply_update(member, provided)
    except ProfileFieldNotEditable as exc:
        raise ApiError(
            422,  # status.HTTP_422_* constant is deprecated in this starlette
            exc.code,
            str(exc),
            details=[
                {
                    "field": exc.field,
                    "code": exc.code,
                    "message": str(exc),
                }
            ],
        ) from exc
    except ProfileFieldUnknown as exc:
        raise ApiError(
            422,
            "VALIDATION_FAILED",
            str(exc),
            details=[
                {
                    "field": exc.field,
                    "code": "UNKNOWN_FIELD",
                    "message": str(exc),
                }
            ],
        ) from exc
    # Router owns the transaction boundary (slice-1/2 convention: repos flush,
    # routers commit on mutation).
    session.commit()
    return ProfilePatchResponse(
        profile=_to_profile(member),
        reverification_required=reverification_required,
    )
