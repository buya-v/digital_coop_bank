"""EP-1 MFA enrollment + SMS-challenge router (04 §3.1).

Operations against the OpenAPI contract:

- createMfaEnrollment  POST /api/v1/auth/mfa/enrollments  -> 201 MfaEnrollmentResponse
- createMfaChallenge   POST /api/v1/auth/mfa/challenges   -> 201 MfaChallengeResponse

`createMfaChallenge` (ADDED contract surface) issues a fresh out-of-band SMS
one-time code for an ENROLLED SMS factor: TOTP derives codes client-side, but SMS
must be SENT before each step-up, so this is the minimal issuance step the base
contract lacked. The code is delivered ONLY over the SMS port and stored hash-only
+ short-lived; the step-up slice verifies a submitted code against it.

Depends on `get_current_member` (the member-auth foundation): the factor is always
enrolled for the AUTHENTICATED member, whose id comes from the verified token
subject — never from the path or body. A member can therefore only ever enroll a
factor for THEMSELVES; the IDOR class is excluded by construction.

The TOTP secret is encrypted at rest by the service (`SecretCipher`); SMS delivery
goes through the `SmsSender` port (a deterministic mock in dev/test). Both the
cipher and the sender are FastAPI dependencies so a real KMS-backed cipher / SMS
gateway swaps in without touching this router, and tests override them.

SCOPE: this creates the MFA FACTOR (PENDING). Binding it to ACTIVE (proving a
code) and device-binding are separate concerns — the request's
`device_fingerprint`/`platform` are accepted per the contract but a DeviceBinding
row is not created here. No money / ledger. The router owns the transaction
(repos flush; the router commits on a mutation).
"""
from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.adapters.sms.mock import MockSmsSender
from app.adapters.sms.port import SmsSender
from app.api.deps import get_session
from app.api.errors import ApiError
from app.auth.deps import get_current_member
from app.auth.mfa import SecretCipher, get_secret_cipher
from app.models.membership import Member
from app.services.mfa import (
    MfaChallengeService,
    MfaEnrollmentService,
    MfaServiceError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["EP-1"])


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class MfaEnrollmentRequest(BaseModel):
    """Mirrors the contract's `MfaEnrollmentRequest` (all three fields required).

    `factor_type` is accepted as a free string and validated in the service, so an
    unsupported value (e.g. BIOMETRIC) yields the uniform 422 Error envelope rather
    than FastAPI's default request-validation shape.
    """

    factor_type: str
    device_fingerprint: str
    platform: str


class MfaEnrollmentResponse(BaseModel):
    """Mirrors the contract's `MfaEnrollmentResponse`."""

    enrollment_id: uuid.UUID
    binding_challenge: str


class MfaChallengeRequest(BaseModel):
    """Mirrors the contract's `MfaChallengeRequest` (factor_type to challenge).

    Validated in the service so an unsupported value (TOTP/BIOMETRIC) yields the
    uniform 422 Error envelope. Only SMS is challengeable.
    """

    factor_type: str


class MfaChallengeResponse(BaseModel):
    """Mirrors the contract's `MfaChallengeResponse`.

    Carries only NON-secret fields — the one-time code travels solely over the SMS
    channel and never appears here.
    """

    challenge_id: uuid.UUID
    delivery: str
    expires_at: datetime.datetime


# --- Dependencies ------------------------------------------------------------


def get_sms_sender() -> SmsSender:
    """Provide the SMS delivery port.

    The concrete gateway is an operator procurement decision (no vendor pinned);
    this slice returns the deterministic no-network `MockSmsSender`. This is the
    seam a real gateway swaps into, and the seam tests override
    (`app.dependency_overrides[get_sms_sender]`) to read back the sent code.
    """
    return MockSmsSender()


# --- Routes ------------------------------------------------------------------


@router.post(
    "/mfa/enrollments",
    response_model=MfaEnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll an MFA factor for the authenticated member.",
)
def create_mfa_enrollment(
    body: MfaEnrollmentRequest,
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
    cipher: SecretCipher = Depends(get_secret_cipher),
    sms_sender: SmsSender = Depends(get_sms_sender),
) -> MfaEnrollmentResponse:
    # No path/body member id: `get_current_member` is the sole identity source.
    service = MfaEnrollmentService(session, cipher=cipher, sms_sender=sms_sender)
    try:
        result = service.enroll(member, factor_type=body.factor_type)
    except MfaServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    # Router owns the transaction boundary (repos flush; router commits on mutation).
    session.commit()
    return MfaEnrollmentResponse(
        enrollment_id=result.enrollment_id,
        binding_challenge=result.binding_challenge,
    )


@router.post(
    "/mfa/challenges",
    response_model=MfaChallengeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a fresh out-of-band SMS challenge code for the member's SMS factor.",
)
def create_mfa_challenge(
    body: MfaChallengeRequest,
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
    sms_sender: SmsSender = Depends(get_sms_sender),
) -> MfaChallengeResponse:
    # No path/body member id: `get_current_member` is the sole identity source, so a
    # member can only ever challenge their OWN factor (IDOR excluded by construction).
    service = MfaChallengeService(session, sms_sender=sms_sender)
    try:
        result = service.issue(member, factor_type=body.factor_type)
    except MfaServiceError as exc:
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    # Router owns the transaction boundary (repos flush; router commits on mutation).
    session.commit()
    return MfaChallengeResponse(
        challenge_id=result.challenge_id,
        delivery=result.delivery,
        expires_at=result.expires_at,
    )
