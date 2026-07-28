"""Member-auth configuration (the IdP verification key + claim expectations).

The real identity provider is operator-chosen (self-host / data residency, 04
§5.3) and is NOT pinned by the contract. So the IdP signing **public** key, its
issuer, and the token audience are supplied by the environment, never committed
and never hard-coded here. The signature ALGORITHM is deliberately absent — it is
the non-negotiable constant `verifier.ALLOWED_ALGORITHMS` and must not be
operator-tunable (widening it re-opens the algorithm-confusion attack).

Environment:
  DCB_AUTH_JWT_PUBLIC_KEY          IdP signing public key, PEM (SPKI/X.509).
                                   `\\n` escapes are unescaped so the key can
                                   live on a single env line.
  DCB_AUTH_JWT_ISSUER              expected `iss`; enforced only when set.
  DCB_AUTH_JWT_AUDIENCE            expected `aud`; enforced only when set.
  DCB_AUTH_JWT_LEEWAY_SECONDS      clock-skew tolerance for exp/nbf (default 0).

JWKS note: a production IdP typically publishes a JWKS URL with key rotation and
`kid` selection. That is the natural extension of this seam (fetch + cache JWKS,
pick the key by header `kid`, build a `JwtTokenVerifier`-equivalent). It is left
to operator integration; the no-network foundation verifies against a supplied
PEM. The algorithm allow-list stays fixed either way.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AuthSettings:
    """Resolved member-auth settings. Never holds a private key."""

    public_key_pem: Optional[str]  # noqa: UP045
    issuer: Optional[str]  # noqa: UP045
    audience: Optional[str]  # noqa: UP045
    leeway_seconds: int = 0


def _read_leeway() -> int:
    raw = os.environ.get("DCB_AUTH_JWT_LEEWAY_SECONDS", "").strip()
    if not raw:
        return 0
    try:
        value = int(raw)
    except ValueError:
        return 0
    return max(value, 0)


def get_auth_settings() -> AuthSettings:
    """Read member-auth settings from the environment (nothing committed)."""
    raw_key = os.environ.get("DCB_AUTH_JWT_PUBLIC_KEY", "").strip()
    # Allow a single-line env var to carry a multi-line PEM.
    public_key_pem = raw_key.replace("\\n", "\n") if raw_key else None
    issuer = os.environ.get("DCB_AUTH_JWT_ISSUER", "").strip() or None
    audience = os.environ.get("DCB_AUTH_JWT_AUDIENCE", "").strip() or None
    return AuthSettings(
        public_key_pem=public_key_pem,
        issuer=issuer,
        audience=audience,
        leeway_seconds=_read_leeway(),
    )
