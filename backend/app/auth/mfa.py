"""MFA cryptography + TOTP helpers — the security core of the enrollment feature.

Two responsibilities, both delegated to well-known libraries (never hand-rolled):

1. SECRET AT REST (`SecretCipher`). The TOTP shared secret MUST NOT be stored in
   plaintext. This wraps `cryptography.fernet.Fernet` — AUTHENTICATED symmetric
   encryption (AES-128-CBC + HMAC-SHA256, integrity-checked on decrypt) — so the
   `mfa_factor.secret_ciphertext` column only ever holds ciphertext. The plaintext
   seed is decrypted in-memory solely to verify a submitted code and is never
   logged, returned, or persisted after the one-time enrollment challenge.

2. TOTP (`generate_totp_secret` / `totp_provisioning_uri` / `verify_totp`). RFC-6238
   TOTP via `pyotp` — the authenticator generates codes from the shared secret; the
   server verifies within a SMALL time window (±1 step by default; no wide drift).

KEY MANAGEMENT (operator + production caveat):
- The encryption key is read from the environment (`DCB_MFA_ENC_KEY`) — a urlsafe
  base64-encoded 32-byte Fernet key. It is OPERATOR-SUPPLIED and is NEVER committed,
  hard-coded, or logged. A missing/invalid key fails CLOSED (`MfaCryptoNotConfigured`)
  — the feature admits no enrollment rather than storing a weakly-protected secret.
- This app-level key is a PRAGMATIC baseline, not the production end state. In
  production the key belongs in a KMS / HSM (envelope encryption: a KMS-held master
  key wraps per-record or per-tenant data keys; the app never sees raw key material,
  and key rotation re-wraps without re-encrypting every row). `get_secret_cipher`
  is the single seam a KMS-backed provider replaces — callers only ever see the
  `SecretCipher` interface. Data-residency (CLAUDE.md blocking question #3) means
  the KMS is operator-chosen/in-Mongolia; nothing here assumes a cloud KMS.

NOTHING in this module logs the secret or the key.
"""
from __future__ import annotations

import os

import pyotp
from cryptography.fernet import Fernet, InvalidToken

# TOTP verification window: ±1 time step (30s each) tolerates minor clock skew
# without opening a wide guessing window. Deliberately small (the brief: no wide
# drift); the step-up slice reuses this bound.
TOTP_VALID_WINDOW = 1
# Issuer label shown in the authenticator app (otpauth `issuer`). Cosmetic; carries
# no secret.
TOTP_ISSUER = "Digital Coop Bank"

# Environment variable carrying the operator-supplied Fernet key. Never committed.
MFA_ENC_KEY_ENV = "DCB_MFA_ENC_KEY"


class MfaCryptoNotConfigured(Exception):
    """The MFA encryption key is absent or malformed — fail closed.

    Raised instead of silently storing an unprotected secret. The router maps it
    to a 500-class failure (never a partial enrollment). The exception message
    NEVER contains key material.
    """


class SecretCipher:
    """Authenticated encryption for the TOTP secret at rest (Fernet).

    `encrypt` returns URL-safe base64 ciphertext (an authenticated token);
    `decrypt` verifies integrity and returns the plaintext, raising
    `MfaCryptoNotConfigured` on any tampering/wrong-key. The plaintext is handled
    in-memory only and is never logged.
    """

    def __init__(self, key: str) -> None:
        # `Fernet(key)` validates the key is a well-formed 32-byte urlsafe-b64 key
        # and raises otherwise; we surface that as a fail-closed config error.
        try:
            self._fernet = Fernet(key.encode("ascii"))
        except (ValueError, TypeError) as exc:
            # Do NOT include the key or the underlying value in the message.
            raise MfaCryptoNotConfigured(
                "MFA encryption key is malformed (expected a urlsafe base64 "
                "32-byte Fernet key)."
            ) from exc

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a plaintext secret; return authenticated ciphertext (str)."""
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt + integrity-check ciphertext; return the plaintext secret.

        A tampered token or wrong key raises `MfaCryptoNotConfigured` — never a
        silent wrong value.
        """
        try:
            return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
        except InvalidToken as exc:
            raise MfaCryptoNotConfigured(
                "MFA secret could not be decrypted (tampered ciphertext or wrong key)."
            ) from exc


def get_secret_cipher() -> SecretCipher:
    """Build the `SecretCipher` from the operator-supplied key (the KMS seam).

    Reads `DCB_MFA_ENC_KEY` from the environment. Missing key -> fail closed. This
    is the FastAPI dependency the enrollment router depends on; tests override it
    with a cipher built from an ephemeral test key so no key is ever committed.
    """
    key = os.environ.get(MFA_ENC_KEY_ENV, "").strip()
    if not key:
        raise MfaCryptoNotConfigured(
            f"{MFA_ENC_KEY_ENV} is not set; MFA enrollment is disabled (fail closed)."
        )
    return SecretCipher(key)


def generate_totp_secret() -> str:
    """Generate a fresh random base32 TOTP shared secret (via pyotp)."""
    return pyotp.random_base32()


def totp_provisioning_uri(secret: str, *, account_name: str, issuer: str = TOTP_ISSUER) -> str:
    """Build the `otpauth://totp/...` provisioning URI for an authenticator app.

    This is the one-time binding challenge handed to the client at enrollment; it
    embeds the shared secret (that is its purpose — the seed must reach the
    authenticator exactly once). It is returned only in the enrollment response and
    is never logged.
    """
    return pyotp.TOTP(secret).provisioning_uri(name=account_name, issuer_name=issuer)


def verify_totp(secret: str, code: str, *, valid_window: int = TOTP_VALID_WINDOW) -> bool:
    """Verify a submitted TOTP `code` against `secret` within ±`valid_window` steps.

    `pyotp`'s `verify` performs the constant-time digest comparison internally.
    """
    return bool(pyotp.TOTP(secret).verify(code, valid_window=valid_window))
