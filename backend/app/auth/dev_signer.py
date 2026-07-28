"""DEV/TEST-ONLY RS256 token signer.

    ##########################################################################
    #  WARNING — THIS IS NOT A PRODUCTION COMPONENT.                          #
    #  It mints signed member tokens using an EPHEMERAL RSA keypair that is   #
    #  generated in memory at construction time. It exists SOLELY so the      #
    #  test suite (and local manual pokes) can produce tokens the verifier    #
    #  will accept, WITHOUT this repo issuing real tokens or committing any   #
    #  key material. The keypair is never persisted, never committed, and     #
    #  never leaves the process.                                              #
    ##########################################################################

Two guardrails keep this out of any production path:

1. `DevRsaSigner()` refuses to construct when `DCB_ENV == "production"`.
2. It is imported only by the test suite. No application module, router, or
   dependency imports it — the production verifier only ever receives an
   operator-supplied PUBLIC key (`app.auth.config`), never this signer.

The real IdP is operator-chosen and is NOT pinned here; this signer stands in for
"some RS256 IdP" only well enough to exercise verification.
"""
from __future__ import annotations

import datetime
import os
import uuid
from typing import Any, Optional

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth.verifier import JwtTokenVerifier


def _utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)  # noqa: UP017


class DevRsaSigner:
    """A throwaway RSA keypair that mints RS256 JWTs for tests only."""

    def __init__(self) -> None:
        if os.environ.get("DCB_ENV", "development") == "production":
            raise RuntimeError(
                "DevRsaSigner is a DEV/TEST-ONLY component and must never be "
                "constructed in a production environment."
            )
        self._private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )

    @property
    def private_key_pem(self) -> str:
        """PEM of the ephemeral PRIVATE key (test signing only)."""
        return self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("ascii")

    @property
    def public_key_pem(self) -> str:
        """PEM of the ephemeral PUBLIC key — feed this to the verifier config.

        A test's algorithm-confusion probe also (mis)uses this exact PEM as an
        HMAC secret to prove HS256 is rejected.
        """
        return (
            self._private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode("ascii")
        )

    def verifier(
        self,
        *,
        issuer: Optional[str] = None,  # noqa: UP045
        audience: Optional[str] = None,  # noqa: UP045
        leeway_seconds: int = 0,
    ) -> JwtTokenVerifier:
        """Build a `JwtTokenVerifier` bound to this signer's public key."""
        return JwtTokenVerifier(
            public_key_pem=self.public_key_pem,
            issuer=issuer,
            audience=audience,
            leeway_seconds=leeway_seconds,
        )

    def mint(
        self,
        *,
        subject: str,
        issuer: Optional[str] = None,  # noqa: UP045
        audience: Optional[str] = None,  # noqa: UP045
        expires_in_seconds: int = 900,  # <= 15 min per memberOAuth2
        issued_at: Optional[datetime.datetime] = None,  # noqa: UP045
        not_before: Optional[datetime.datetime] = None,  # noqa: UP045
        extra_claims: Optional[dict[str, Any]] = None,  # noqa: UP045
    ) -> str:
        """Mint an RS256 JWT with the given subject and standard claims.

        `expires_in_seconds` may be negative to forge an already-expired token
        for the expiry-rejection test.
        """
        now = issued_at or _utc_now()
        claims: dict[str, Any] = {
            "sub": subject,
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(seconds=expires_in_seconds)).timestamp()),
            "jti": str(uuid.uuid4()),
        }
        if issuer is not None:
            claims["iss"] = issuer
        if audience is not None:
            claims["aud"] = audience
        if not_before is not None:
            claims["nbf"] = int(not_before.timestamp())
        if extra_claims:
            claims.update(extra_claims)
        return jwt.encode(claims, self.private_key_pem, algorithm="RS256")
