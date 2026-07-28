"""JWT verification behind a port (04 §5.1 Authentication; root.yaml `memberOAuth2`).

This backend **verifies** member access tokens; it never issues them. Tokens are
RS256-signed JWTs minted by an external, operator-chosen OIDC/OAuth2 IdP
(endpoints are operator config — data residency, 04 §5.3), presented as
`Authorization: Bearer <JWT>`. Verification is expressed as a PORT
(`TokenVerifier`) so the concrete IdP key source (a static PEM here; a JWKS URL /
`kid` selection later) is a swappable seam, exactly like the eKYC provider port.

SECURITY POSTURE (this component is adversarially reviewed):

- The allowed signature algorithm is the module constant `ALLOWED_ALGORITHMS =
  ("RS256",)`. It is **not** configurable and is passed **explicitly** to every
  `jwt.decode` call. This single fact defeats two attacks at once:
    * `alg: none` — the unsigned-token forgery — because "none" is not allowed.
    * HS256 / algorithm-confusion (a.k.a. key-confusion) — where an attacker
      signs `alg: HS256` using the server's RSA **public** key as the HMAC
      secret — because "HS256" is not allowed, so the header can never select a
      symmetric algorithm or a different key class.
  The token HEADER never chooses the algorithm or the key.
- `exp` is REQUIRED and enforced (reject expired). `nbf`/`iat` are enforced when
  present (reject not-yet-valid). `iss` and `aud` are enforced **only when
  configured** (reject wrong issuer / wrong audience).
- All PyJWT failures collapse to one opaque `TokenInvalid` so callers map every
  verification failure to a single 401 without leaking which check failed. The
  token and its claims are NEVER logged.
- Crypto is delegated to PyJWT + `cryptography` (the `PyJWT[crypto]` extra). No
  hand-rolled signature verification.
"""
from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

import jwt

#: The ONLY signature algorithm this service accepts. Deliberately a hard
#: constant, not configuration: widening it (e.g. to HS256) would re-open the
#: algorithm-confusion attack, so it must not be an operator-tunable value.
ALLOWED_ALGORITHMS: tuple[str, ...] = ("RS256",)


class TokenInvalid(Exception):
    """A token failed verification (bad signature, expired, wrong alg, wrong
    iss/aud, malformed, ...). Deliberately carries no detail about *which* check
    failed — callers render a single opaque 401."""


class AuthConfigurationError(Exception):
    """The verifier cannot operate because the IdP public key is not configured.

    Raised at construction/verify time so an unconfigured deployment fails
    CLOSED (it cannot verify, therefore cannot admit anyone) rather than open.
    """


@runtime_checkable
class TokenVerifier(Protocol):
    """Port: verify a bearer JWT and return its (already-validated) claims.

    Implementations MUST raise `TokenInvalid` on any verification failure and
    MUST NOT return unverified claims.
    """

    def verify(self, token: str) -> dict[str, Any]:
        ...


class JwtTokenVerifier:
    """RS256 JWT verifier bound to a configured IdP public key.

    `public_key_pem` is the operator-supplied IdP signing public key in PEM
    (SubjectPublicKeyInfo / X.509) form. `issuer` / `audience` are enforced only
    when set. `leeway_seconds` tolerates small clock skew on `exp`/`nbf`.
    """

    def __init__(
        self,
        *,
        public_key_pem: Optional[str],  # noqa: UP045 — runtime-evaluated by callers
        issuer: Optional[str] = None,  # noqa: UP045
        audience: Optional[str] = None,  # noqa: UP045
        leeway_seconds: int = 0,
    ) -> None:
        self._public_key_pem = public_key_pem
        self._issuer = issuer
        self._audience = audience
        self._leeway_seconds = leeway_seconds

    def verify(self, token: str) -> dict[str, Any]:
        if not self._public_key_pem:
            # No IdP key configured -> cannot verify -> admit no one.
            raise AuthConfigurationError(
                "No IdP public key configured; cannot verify member tokens."
            )
        try:
            claims: dict[str, Any] = jwt.decode(
                token,
                key=self._public_key_pem,
                # The allow-list is passed EXPLICITLY on every call. This is the
                # line that rejects alg:none and HS256/key-confusion.
                algorithms=list(ALLOWED_ALGORITHMS),
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._leeway_seconds,
                options={
                    "require": ["exp"],  # a token with no expiry is never accepted
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_iat": True,
                    # iss / aud are enforced ONLY when the operator configured them.
                    "verify_iss": self._issuer is not None,
                    "verify_aud": self._audience is not None,
                },
            )
        except jwt.InvalidTokenError as exc:
            # One opaque failure: bad signature, expired, not-yet-valid, wrong
            # alg, wrong iss/aud, malformed — all collapse here. Never log the
            # token or the exception detail into any member-visible surface.
            raise TokenInvalid("access token failed verification") from exc
        return claims
