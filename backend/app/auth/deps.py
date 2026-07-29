"""Member-auth FastAPI dependencies — `get_current_member`.

This is the authenticated-member counterpart to the pre-auth bootstrap-token
dependency (`app.api.routers.onboarding.resume_token`). BOTH exist on purpose:
onboarding stays pre-auth (an applicant is not yet a member), while every future
member-facing route depends on `get_current_member`.

Flow:
  Authorization: Bearer <JWT>
    -> `bearer_token`        extract the raw token (missing/malformed -> 401)
    -> `TokenVerifier`       verify RS256 signature + exp/nbf + iss/aud
                             (any failure -> 401; see app.auth.verifier)
    -> claim `sub`           resolve to a Member row via the repo
                             (unknown/invalid subject -> 401)
    -> Member                returned to the route

The token subject is the ONLY claim trusted as a member fact, and only as a key
into the members table — every other member attribute is read from the DB row,
never from the token. The token and its claims are never logged.
"""
from __future__ import annotations

import datetime
from collections.abc import Callable
from typing import Optional

from fastapi import Depends, Header, status
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import ApiError
from app.auth.config import get_auth_settings
from app.auth.verifier import (
    AuthConfigurationError,
    JwtTokenVerifier,
    TokenInvalid,
    TokenVerifier,
)
from app.models.identity import StepUpToken
from app.models.membership import Member
from app.repositories.identity import StepUpTokenRepository
from app.repositories.membership import MemberRepository
from app.services.stepup import hash_step_up_token


def bearer_token(
    authorization: Optional[str] = Header(default=None),  # noqa: UP045
) -> str:
    """Extract the member access token from `Authorization: Bearer <JWT>`.

    Missing or malformed header -> 401 UNAUTHENTICATED (the contract's universal
    401). The token value itself is never logged.
    """
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "Missing or malformed bearer token "
            "(expected 'Authorization: Bearer <access token>').",
        )
    return token.strip()


def get_token_verifier() -> TokenVerifier:
    """Provide the configured member-token verifier (the swappable IdP seam).

    Built from the operator-supplied IdP public key (`app.auth.config`). Tests
    override this dependency to inject a verifier bound to the dev signer's
    public key. The allowed algorithm is fixed (`RS256`) inside the verifier and
    is not configurable here.
    """
    settings = get_auth_settings()
    return JwtTokenVerifier(
        public_key_pem=settings.public_key_pem,
        issuer=settings.issuer,
        audience=settings.audience,
        leeway_seconds=settings.leeway_seconds,
    )


def get_current_member(
    token: str = Depends(bearer_token),
    session: Session = Depends(get_session),
    verifier: TokenVerifier = Depends(get_token_verifier),
) -> Member:
    """Resolve the authenticated Member from a verified Bearer JWT.

    401 on a missing/invalid/expired token or an unknown subject. Nothing about
    the member is trusted from the token beyond `sub` -> DB lookup.
    """
    try:
        claims = verifier.verify(token)
    except TokenInvalid as exc:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "Invalid or expired access token.",
        ) from exc
    except AuthConfigurationError as exc:
        # Fail closed: an unconfigured verifier admits no one. Surfaced as 401
        # (not 500) so the outcome is "no access", never a partial admit.
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "Invalid or expired access token.",
        ) from exc

    subject = claims.get("sub")
    member = (
        MemberRepository(session).get_by_subject(subject)
        if isinstance(subject, str) and subject
        else None
    )
    if member is None:
        # A validly-signed token whose subject is not a known member is still an
        # authentication failure here (uniform 401, no member enumeration).
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "The access token subject does not identify a known member.",
        )
    return member


def _utc_now() -> datetime.datetime:
    """Naive UTC now — matches the `TIMESTAMP WITHOUT TIME ZONE` token columns."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)  # noqa: UP017


def require_step_up(action: str | None = None) -> Callable[..., StepUpToken]:
    """Build a dependency that verifies + CONSUMES a step-up assertion (US-1.4).

    This is the `stepUpAssertion` scheme (root.yaml: apiKey header
    `X-Step-Up-Token`), composed IN ADDITION TO `get_current_member` for sensitive
    operations (e.g. revokeDevice). The returned dependency:

    1. reads `X-Step-Up-Token` (missing -> 401 STEP_UP_REQUIRED);
    2. hashes it and looks the row up by hash (the plaintext is never stored);
    3. verifies it EXISTS, is UNEXPIRED, is NOT consumed, and BELONGS to the
       authenticated member — any failure is a uniform 401 STEP_UP_FAILED (a token
       minted for member A is refused for member B: the binding guarantee);
    4. if the token was minted for a specific `requested_action`, that must match
       this operation's `action` (else 403);
    5. CONSUMES it atomically — a conditional UPDATE guarded by
       `consumed_at IS NULL AND member_id = ... AND expires_at > now` — so a replay
       (or a race) matches zero rows and is refused. Consumption is committed here,
       so the token is spent single-use regardless of whether the guarded operation
       then succeeds.

    `action` is optional: a token minted without a `requested_action` (NULL) is a
    general assertion accepted by any step-up-gated operation; when both the token
    and the operation name an action, they must agree.
    """

    def _require_step_up(
        member: Member = Depends(get_current_member),
        session: Session = Depends(get_session),
        x_step_up_token: Optional[str] = Header(default=None),  # noqa: UP045
    ) -> StepUpToken:
        presented = (x_step_up_token or "").strip()
        if not presented:
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "STEP_UP_REQUIRED",
                "This action requires a step-up assertion (X-Step-Up-Token).",
            )
        repo = StepUpTokenRepository(session)
        token = repo.get_by_hash(hash_step_up_token(presented))
        now = _utc_now()
        # Uniform 401 for absent / foreign / expired / already-consumed — never
        # distinguish them to the caller (no token enumeration, no owner leak).
        if (
            token is None
            or token.member_id != member.id
            or token.consumed_at is not None
            or token.expires_at <= now
        ):
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "STEP_UP_FAILED",
                "Invalid or expired step-up assertion.",
            )
        # Action binding: a token scoped to one action must match this operation.
        if (
            action is not None
            and token.requested_action is not None
            and token.requested_action != action
        ):
            raise ApiError(
                status.HTTP_403_FORBIDDEN,
                "STEP_UP_ACTION_MISMATCH",
                "This step-up assertion is not valid for this action.",
            )
        # Atomic single-use consume — the race-safe final gate. If another request
        # spent it first, rowcount is 0 and we refuse.
        if not repo.consume(token.id, member.id, now=now):
            raise ApiError(
                status.HTTP_401_UNAUTHORIZED,
                "STEP_UP_FAILED",
                "Invalid or expired step-up assertion.",
            )
        # Persist the consumption immediately: the token is spent even if the
        # guarded operation below later fails (single-use is not conditional on
        # the action succeeding).
        session.commit()
        return token

    return _require_step_up
