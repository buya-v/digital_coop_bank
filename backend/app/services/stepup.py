"""Step-up token issuance service (EP-1, 04 §3.1 `POST /auth/step-up`, US-1.4).

The backend ISSUES a security credential here — the single-use step-up assertion
token — so this is the highest-risk surface in EP-1. The flow:

    verify the member's MFA `factor_response`  (constant-time, ±1 TOTP step)
      -> on the FIRST correct code, promote a PENDING factor to ACTIVE (binding)
      -> mint an OPAQUE random token, store ONLY its SHA-256 hash, return the
         plaintext once + `expires_at`.

SECURITY controls enforced here (each has a test that proves it):

- **Opaque + hash-only.** The token is `secrets.token_urlsafe` (256-bit); only its
  SHA-256 hash is persisted (`StepUpToken.token_hash`). A leaked DB row yields no
  usable token, and nothing here logs the plaintext.
- **Member-bound.** The token row carries the minting member's id; `require_step_up`
  refuses it for any other member.
- **Short-lived.** `expires_at = now + STEP_UP_TTL` (a few minutes).
- **Binding.** A never-confirmed (PENDING) factor cannot mint a step-up until a
  correct code proves possession — that first success flips it ACTIVE. An absent
  factor cannot mint at all.
- **Lockout.** Consecutive wrong `factor_response` attempts increment
  `mfa_factor.failed_attempts`; at `MAX_FAILED_ATTEMPTS` the factor LOCKS (423)
  for `LOCKOUT_DURATION` — never unlimited TOTP guessing. A correct code resets
  the counter; the lock auto-expires so a member is never permanently locked out.

TOTP verification (window ±1 step) and the secret decryption are REUSED from
T1 (`app.auth.mfa`) — TOTP is never hand-rolled here. Repos flush; the router
owns the commit.

Time is handled as NAIVE UTC (`_utc_now`) throughout, matching the
`TIMESTAMP WITHOUT TIME ZONE` columns: a value read back from the store is naive,
so comparing it against a naive `now` avoids an aware/naive mismatch.
"""
from __future__ import annotations

import datetime
import hashlib
import secrets
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.auth.mfa import SecretCipher, verify_totp
from app.models.identity import MfaFactor, MfaFactorStatus, MfaFactorType
from app.models.membership import Member
from app.repositories.identity import MfaFactorRepository, StepUpTokenRepository

# Opaque token entropy (bytes) — 256-bit, well beyond brute-force reach.
TOKEN_BYTES = 32
# How long a minted step-up token is valid — deliberately short (single sensitive
# action, then discard).
STEP_UP_TTL = datetime.timedelta(minutes=5)
# Brute-force lockout: wrong attempts before the factor locks, and how long it
# stays locked before attempts resume.
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = datetime.timedelta(minutes=15)


def _utc_now() -> datetime.datetime:
    """Naive UTC now — matches the TIMESTAMP WITHOUT TIME ZONE columns."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)  # noqa: UP017


def hash_step_up_token(token: str) -> str:
    """SHA-256 hex of an opaque step-up token — the ONLY form ever persisted.

    SHA-256 (not a slow password hash) is appropriate because the token is a
    256-bit random value, not a low-entropy user secret: it is not guessable, so
    the store only needs to be non-reversible, not brute-force-hardened.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class StepUpServiceError(Exception):
    """Base for step-up domain errors (mapped to HTTP by the router)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class StepUpFailed(StepUpServiceError):
    """The step-up challenge response was invalid / no usable factor (401)."""

    def __init__(self) -> None:
        super().__init__(
            401,
            "STEP_UP_FAILED",
            "The step-up challenge response was invalid.",
        )


class FactorLocked(StepUpServiceError):
    """Too many failed attempts — the MFA factor is locked (423)."""

    def __init__(self) -> None:
        super().__init__(
            423,
            "FACTOR_LOCKED",
            "Too many failed attempts; the MFA factor is temporarily locked.",
        )


@dataclass(frozen=True)
class MintResult:
    """The minted token, returned to the client exactly once, plus its expiry."""

    step_up_token: str
    expires_at: datetime.datetime


class StepUpService:
    """Verify an MFA factor response and mint a single-use step-up token."""

    def __init__(self, session: Session, *, cipher: SecretCipher) -> None:
        self._session = session
        self._factor_repo = MfaFactorRepository(session)
        self._token_repo = StepUpTokenRepository(session)
        self._cipher = cipher

    def mint(
        self, member: Member, *, factor_response: str, requested_action: str | None
    ) -> MintResult:
        """Verify `factor_response` for the member's TOTP factor, then mint a token.

        Raises `FactorLocked` (423) when locked, `StepUpFailed` (401) on a wrong
        code or when the member has no verifiable factor.
        """
        # TOTP is the primary, server-verifiable factor (the SMS one-time code is
        # not persisted at rest — T1). Resolve the member's OWN factor; the id is
        # never taken from the request (IDOR excluded by construction).
        factor = self._factor_repo.get_for_member_and_type(
            member.id, MfaFactorType.TOTP
        )
        if factor is None or factor.secret_ciphertext is None:
            # Absent / never-enrolled factor cannot mint a step-up.
            raise StepUpFailed()

        now = _utc_now()
        if self._is_locked(factor, now):
            raise FactorLocked()

        secret = self._cipher.decrypt(factor.secret_ciphertext)
        if not verify_totp(secret, factor_response):
            factor.failed_attempts += 1
            if factor.failed_attempts >= MAX_FAILED_ATTEMPTS:
                factor.locked_at = now
                self._factor_repo.flush()
                raise FactorLocked()
            self._factor_repo.flush()
            raise StepUpFailed()

        # Correct code: clear the lockout counters.
        factor.failed_attempts = 0
        factor.locked_at = None
        # BINDING: the first correct code confirms a PENDING factor (ACTIVE).
        if factor.status is MfaFactorStatus.PENDING:
            factor.status = MfaFactorStatus.ACTIVE
            factor.confirmed_at = now

        plaintext = secrets.token_urlsafe(TOKEN_BYTES)
        expires_at = now + STEP_UP_TTL
        self._token_repo.create(
            member_id=member.id,
            token_hash=hash_step_up_token(plaintext),
            requested_action=requested_action,
            expires_at=expires_at,
        )
        return MintResult(step_up_token=plaintext, expires_at=expires_at)

    def _is_locked(self, factor: MfaFactor, now: datetime.datetime) -> bool:
        """True iff the factor is currently locked; auto-clears an expired lock.

        A lock older than `LOCKOUT_DURATION` is released here (counters reset) so
        the member can try again — no permanent lock-out with no unlock path.
        """
        if factor.locked_at is None:
            return False
        if now - factor.locked_at >= LOCKOUT_DURATION:
            factor.failed_attempts = 0
            factor.locked_at = None
            self._factor_repo.flush()
            return False
        return True
