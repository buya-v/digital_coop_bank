"""EP-1 step-up router (04 §3.1) — `POST /auth/step-up` (createStepUpToken).

Mints the single-use step-up assertion the `stepUpAssertion` scheme requires on
sensitive operations. Depends on `get_current_member`: the token is always minted
for the AUTHENTICATED member (id from the verified token subject, never a
path/body value) — a member can only mint their OWN step-up (IDOR excluded by
construction).

The MFA `factor_response` is verified by the service against the member's factor
(constant-time TOTP, ±1 step); the plaintext token is returned exactly once and
is NEVER logged. The router owns the transaction (the service flushes; the router
commits on the successful mint). No money / ledger.
"""
from __future__ import annotations

import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import ApiError
from app.auth.deps import get_current_member
from app.auth.mfa import SecretCipher, get_secret_cipher
from app.models.membership import Member
from app.services.stepup import StepUpService, StepUpServiceError

router = APIRouter(prefix="/api/v1/auth", tags=["EP-1"])


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class StepUpRequest(BaseModel):
    """Mirrors the contract's `StepUpRequest` (factor_response + action_context)."""

    factor_response: str
    # The sensitive action the token will authorize (contract: free-form object).
    # A well-known `action` key, when present, scopes the token to that operation
    # (`require_step_up` enforces the match); otherwise the token is a general
    # step-up assertion. Optional[...] (not `X | None`): pydantic evaluates this
    # annotation at runtime and the documented dev machine runs 3.9, where PEP 604
    # `|` on a generic alias raises.
    action_context: Optional[dict[str, object]] = None  # noqa: UP045


class StepUpResponse(BaseModel):
    """Mirrors the contract's `StepUpResponse` (step_up_token + expires_at)."""

    step_up_token: str
    expires_at: datetime.datetime


def _requested_action(action_context: dict[str, object] | None) -> str | None:
    """Derive the optional action scope from `action_context.action`, if a string.

    The contract leaves `action_context` a free-form object; we read a single
    conventional `action` key to bind the token to one operation. Anything else
    (absent, non-string) yields a general (unscoped) token.
    """
    if not action_context:
        return None
    value = action_context.get("action")
    return value if isinstance(value, str) and value else None


# --- Routes ------------------------------------------------------------------


@router.post(
    "/step-up",
    response_model=StepUpResponse,
    summary="Mint a single-use step-up assertion token for the authenticated member.",
)
def create_step_up_token(
    body: StepUpRequest,
    member: Member = Depends(get_current_member),
    session: Session = Depends(get_session),
    cipher: SecretCipher = Depends(get_secret_cipher),
) -> StepUpResponse:
    # No path/body member id: `get_current_member` is the sole identity source.
    service = StepUpService(session, cipher=cipher)
    try:
        result = service.mint(
            member,
            factor_response=body.factor_response,
            requested_action=_requested_action(body.action_context),
        )
    except StepUpServiceError as exc:
        # Persist the lockout bookkeeping the service recorded (an incremented
        # `failed_attempts`, or a fresh `locked_at`) BEFORE surfacing the error.
        # Without this commit the counter rolls back with the request session and
        # lockout could never accumulate — brute-force protection would be moot.
        # No token was minted on this path, so only the lockout state is committed.
        session.commit()
        raise ApiError(exc.status_code, exc.code, exc.message) from exc
    # Router owns the transaction boundary (service flushes; router commits).
    session.commit()
    return StepUpResponse(
        step_up_token=result.step_up_token,
        expires_at=result.expires_at,
    )
