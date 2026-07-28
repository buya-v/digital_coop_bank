"""Member-authentication foundation (EP-1 / 04 §5.1).

Verifies external-IdP RS256 Bearer JWTs and resolves them to a `Member`
(`get_current_member`). This backend VERIFIES tokens; it does not issue them.

Public surface:
- `get_current_member`  FastAPI dependency for member-protected routes.
- `get_token_verifier`  the verifier seam (overridable in tests).
- `bearer_token`        `Authorization: Bearer` extraction.
- `TokenVerifier`       the verification PORT (Protocol).
- `JwtTokenVerifier`    the concrete RS256 verifier.
- `TokenInvalid` / `AuthConfigurationError`  verification / config failures.
- `ALLOWED_ALGORITHMS`  the fixed RS256-only allow-list.

`app.auth.dev_signer.DevRsaSigner` is DEV/TEST-ONLY and is intentionally NOT
exported here — nothing in the app depends on it.
"""
from __future__ import annotations

from app.auth.deps import bearer_token, get_current_member, get_token_verifier
from app.auth.verifier import (
    ALLOWED_ALGORITHMS,
    AuthConfigurationError,
    JwtTokenVerifier,
    TokenInvalid,
    TokenVerifier,
)

__all__ = [
    "ALLOWED_ALGORITHMS",
    "AuthConfigurationError",
    "JwtTokenVerifier",
    "TokenInvalid",
    "TokenVerifier",
    "bearer_token",
    "get_current_member",
    "get_token_verifier",
]
