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
from app.models.membership import Member
from app.repositories.membership import MemberRepository


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
