"""MFA enrollment service (EP-1, 04 §3.1 `POST /auth/mfa/enrollments`, US-1.4).

Creates a PENDING MFA factor for the AUTHENTICATED member and returns a one-time
binding challenge. The member id is always the caller's own (`get_current_member`),
never a path/body value — IDOR excluded by construction, like the consent/device
services. Repos flush; the router owns the commit.

SECURITY properties enforced here:
- The TOTP secret is generated, then ENCRYPTED before it ever reaches the DB
  (`SecretCipher`); only the ciphertext is stored. The plaintext exists in-memory
  only long enough to build the one-time provisioning URI and is never logged.
- BINDING: a factor is created PENDING and becomes ACTIVE only when the member
  proves a correct code (the step-up slice performs that promotion). A
  never-confirmed factor therefore cannot authorize a step-up.
- Uniqueness is per-(member, factor_type). Re-enrolling a still-PENDING factor
  re-issues its challenge on the same row (a member who abandoned enrollment may
  retry); a duplicate of an already-ACTIVE factor is refused (409 FACTOR_EXISTS).
- SMS delivery is behind a PORT (`SmsSender`); the one-time code travels ONLY over
  that channel — it is NOT returned in the HTTP response (which would defeat the
  out-of-band factor). BIOMETRIC (a contract enum value) is device-local, not a
  server-stored secret, so it is rejected here (422).
"""
from __future__ import annotations

import datetime
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.sms.port import SmsDeliveryError, SmsSender
from app.auth.mfa import (
    SMS_CHALLENGE_TTL,
    SMS_RESEND_INTERVAL,
    SecretCipher,
    generate_sms_code,
    generate_totp_secret,
    hash_sms_code,
    totp_provisioning_uri,
)
from app.models.identity import MfaFactor, MfaFactorStatus, MfaFactorType
from app.models.membership import Member
from app.repositories.identity import MfaFactorRepository
# The SMS challenge lock mirrors the step-up brute-force lock exactly (same
# window), so re-issuing a code can never reset or bypass a lockout.
from app.services.stepup import LOCKOUT_DURATION


def _utc_now() -> datetime.datetime:
    """Naive UTC now — matches the TIMESTAMP WITHOUT TIME ZONE columns."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)  # noqa: UP017


class MfaServiceError(Exception):
    """Base for MFA enrollment domain errors (mapped to HTTP by the router)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class UnsupportedFactorType(MfaServiceError):
    """A factor_type outside the supported set (TOTP/SMS) was requested (422)."""

    def __init__(self, value: str) -> None:
        super().__init__(
            422,
            "VALIDATION_FAILED",
            f"Unsupported MFA factor type '{value}'. Supported: TOTP, SMS.",
        )


class FactorAlreadyEnrolled(MfaServiceError):
    """The member already has an ACTIVE factor of this type (409 FACTOR_EXISTS)."""

    def __init__(self, factor_type: MfaFactorType) -> None:
        super().__init__(
            409,
            "FACTOR_EXISTS",
            f"An active {factor_type.value} factor is already enrolled.",
        )


class SmsDeliveryFailed(MfaServiceError):
    """The SMS one-time code could not be delivered (502)."""

    def __init__(self) -> None:
        super().__init__(
            502,
            "SMS_DELIVERY_FAILED",
            "Could not deliver the SMS verification code; please retry.",
        )


class SmsRateLimited(MfaServiceError):
    """A resend was requested inside `SMS_RESEND_INTERVAL` of the prior send (429).

    The cost/bombing control: SMS delivery is a per-message carrier cost, and
    neither the enroll re-arm path nor the challenge path otherwise bounds how
    often a code is sent. This does NOT touch `failed_attempts`/`locked_at` — a
    refused resend must never look like (or clear) a brute-force lock.
    """

    def __init__(self) -> None:
        super().__init__(
            429,
            "RATE_LIMITED",
            "An SMS code was sent too recently; please wait before requesting another.",
        )


class ChallengeNotSupported(MfaServiceError):
    """A challenge was requested for a factor that needs none, e.g. TOTP (422).

    Only SMS requires a server-issued challenge; TOTP codes are derived by the
    authenticator from the shared seed, so there is nothing to issue.
    """

    def __init__(self, factor_type: MfaFactorType) -> None:
        super().__init__(
            422,
            "VALIDATION_FAILED",
            f"MFA challenge issuance is only supported for SMS factors, "
            f"not {factor_type.value}.",
        )


class FactorNotEnrolled(MfaServiceError):
    """A challenge was requested for a factor the member has not enrolled (404)."""

    def __init__(self, factor_type: MfaFactorType) -> None:
        super().__init__(
            404,
            "NOT_FOUND",
            f"No enrolled {factor_type.value} factor to challenge.",
        )


class ChallengeFactorLocked(MfaServiceError):
    """The factor is locked, so no new challenge may be issued (423).

    The SAME lockout as step-up: refusing issuance while locked stops an attacker
    from re-arming a fresh code to reset or side-step the brute-force lock.
    """

    def __init__(self) -> None:
        super().__init__(
            423,
            "FACTOR_LOCKED",
            "Too many failed attempts; the MFA factor is temporarily locked.",
        )


@dataclass(frozen=True)
class EnrollmentResult:
    """The enrollment outcome projected onto the contract's response fields."""

    enrollment_id: uuid.UUID
    binding_challenge: str


@dataclass(frozen=True)
class ChallengeResult:
    """A freshly issued SMS challenge, projected onto the contract's fields.

    Carries only NON-secret fields: the factor id (a handle), a masked delivery
    confirmation, and the expiry. The code itself travels ONLY over the SMS port.
    """

    challenge_id: uuid.UUID
    delivery: str
    expires_at: datetime.datetime


def _parse_factor_type(value: str) -> MfaFactorType:
    """Resolve the request factor_type to a SUPPORTED enum, or raise 422.

    Accepts only TOTP/SMS. BIOMETRIC (a valid contract value) and any unknown
    string are rejected — BIOMETRIC is device-local, not a server-stored secret.
    """
    try:
        return MfaFactorType(value)
    except ValueError as exc:
        raise UnsupportedFactorType(value) from exc


def _enforce_sms_resend_interval(
    prior_expires_at: datetime.datetime | None, now: datetime.datetime
) -> None:
    """Refuse an SMS (re)send inside `SMS_RESEND_INTERVAL` of the prior one (429).

    MIGRATION-FREE by design: there is no dedicated `last_sent_at` column. Every
    send sets `sms_challenge_expires_at = last_sent_at + SMS_CHALLENGE_TTL`, so the
    last-send instant is recovered by subtracting the (fixed) TTL back out of
    whatever expiry the previous send left behind — no new column, no migration.

    `prior_expires_at is None` (never sent before: a brand-new factor, or an
    enrolled SMS factor with no outstanding/prior challenge) ALWAYS passes — the
    first send for a factor is never rate-limited.
    """
    if prior_expires_at is None:
        return
    last_sent_at = prior_expires_at - SMS_CHALLENGE_TTL
    if now - last_sent_at < SMS_RESEND_INTERVAL:
        raise SmsRateLimited()


def _mask_phone(phone_number: str) -> str:
    """Mask a phone number for a NON-secret confirmation string (last 4 kept)."""
    tail = phone_number[-4:] if len(phone_number) >= 4 else phone_number
    return f"***{tail}"


class MfaEnrollmentService:
    """Enroll a PENDING MFA factor for the authenticated member."""

    def __init__(
        self,
        session: Session,
        *,
        cipher: SecretCipher,
        sms_sender: SmsSender,
    ) -> None:
        self._session = session
        self._repo = MfaFactorRepository(session)
        self._cipher = cipher
        self._sms = sms_sender

    def enroll(self, member: Member, *, factor_type: str) -> EnrollmentResult:
        """Create/re-issue a PENDING factor and return its one-time binding challenge."""
        ftype = _parse_factor_type(factor_type)
        existing = self._repo.get_for_member_and_type(member.id, ftype)
        if existing is not None and existing.status is MfaFactorStatus.ACTIVE:
            # A confirmed factor of this type already exists — do not clobber it.
            raise FactorAlreadyEnrolled(ftype)

        if ftype is MfaFactorType.TOTP:
            factor, challenge = self._prepare_totp(member, existing)
        else:  # MfaFactorType.SMS
            factor, challenge = self._prepare_sms(member, existing)

        return EnrollmentResult(enrollment_id=factor.id, binding_challenge=challenge)

    # --- factor-specific preparation ----------------------------------------

    def _prepare_totp(
        self, member: Member, existing: MfaFactor | None
    ) -> tuple[MfaFactor, str]:
        """Generate + encrypt a TOTP seed, (re)store it PENDING, return (row, otpauth URI)."""
        secret = generate_totp_secret()
        ciphertext = self._cipher.encrypt(secret)
        if existing is not None:
            # Re-issue on the still-PENDING row: rotate to a fresh secret.
            existing.secret_ciphertext = ciphertext
            existing.status = MfaFactorStatus.PENDING
            existing.confirmed_at = None
            self._repo.flush()
            factor = existing
        else:
            factor = self._repo.create_pending(
                member_id=member.id,
                factor_type=MfaFactorType.TOTP,
                secret_ciphertext=ciphertext,
            )
        # The provisioning URI carries the plaintext seed to the authenticator
        # exactly once (its purpose); the plaintext is not persisted or logged.
        return factor, totp_provisioning_uri(secret, account_name=member.email)

    def _prepare_sms(
        self, member: Member, existing: MfaFactor | None
    ) -> tuple[MfaFactor, str]:
        """Send an out-of-band code via the SMS port; store a PENDING (secret-less) row.

        The code is NOT returned in the response — only a masked confirmation is.
        The mock records the code so tests can drive the (step-up) binding.

        The sent code is ARMED as a one-time CHALLENGE on the row (hash-only, short
        expiry) so the step-up slice can verify the member's first response and bind
        the factor ACTIVE — the same challenge machinery `createMfaChallenge`
        re-issues later. The lockout counters are NOT reset here (matching TOTP
        re-enroll): re-issuing must never clear a brute-force lock.

        RATE LIMIT: a resend within `SMS_RESEND_INTERVAL` of the prior send is
        refused (429) BEFORE the SMS port is called — the cost/bombing control. The
        very first send for a factor (`existing is None`, or an existing row with no
        prior challenge) is never limited.
        """
        now = _utc_now()
        if existing is not None:
            _enforce_sms_resend_interval(existing.sms_challenge_expires_at, now)

        code = generate_sms_code()
        try:
            self._sms.send_verification_code(
                phone_number=member.phone_number, code=code
            )
        except SmsDeliveryError as exc:
            raise SmsDeliveryFailed() from exc

        challenge_hash = hash_sms_code(code)
        expires_at = now + SMS_CHALLENGE_TTL
        if existing is not None:
            existing.status = MfaFactorStatus.PENDING
            existing.confirmed_at = None
            existing.sms_challenge_hash = challenge_hash
            existing.sms_challenge_expires_at = expires_at
            self._repo.flush()
            factor = existing
        else:
            factor = self._repo.create_pending(
                member_id=member.id,
                factor_type=MfaFactorType.SMS,
                secret_ciphertext=None,
            )
            factor.sms_challenge_hash = challenge_hash
            factor.sms_challenge_expires_at = expires_at
            self._repo.flush()
        return factor, f"SMS_CODE_SENT:{_mask_phone(member.phone_number)}"


class MfaChallengeService:
    """Issue a fresh out-of-band SMS one-time code for an ENROLLED SMS factor.

    Backs `POST /auth/mfa/challenges` (createMfaChallenge). It exists because an SMS
    factor — unlike TOTP — cannot produce a code client-side: before each step-up
    the server must SEND a new code and remember it. This is that send-and-remember
    step, decoupled from enrollment so an ACTIVE factor can be re-challenged and an
    expired binding code can be re-issued.

    SECURITY:
    - TOTP is refused (422) — it needs no server challenge.
    - A factor the member has not enrolled is a 404 (never reveals another
      member's factor: the id comes from `get_current_member`, never the request).
    - A LOCKED factor is refused (423) with the SAME lockout as step-up, so
      re-issuing a code cannot reset or bypass the brute-force lock. Issuance does
      NOT touch `failed_attempts`/`locked_at`.
    - A resend inside `SMS_RESEND_INTERVAL` of the prior send is refused (429
      RATE_LIMITED) BEFORE the SMS port is called — the cost/bombing control. This
      also does NOT touch `failed_attempts`/`locked_at`; it is a distinct, much
      shorter, non-punitive cooldown layered in front of the lockout, checked
      strictly AFTER the lockout so a locked factor always reads 423.
    - The issued code is delivered ONLY through the SMS port and stored HASH-ONLY
      with a short expiry; it is never returned in the response. Issuing overwrites
      any prior outstanding challenge (at most one live code per factor).
    Repos flush; the router owns the commit.
    """

    def __init__(self, session: Session, *, sms_sender: SmsSender) -> None:
        self._session = session
        self._repo = MfaFactorRepository(session)
        self._sms = sms_sender

    def issue(self, member: Member, *, factor_type: str) -> ChallengeResult:
        """Send + arm a fresh SMS challenge for the member's OWN SMS factor."""
        ftype = _parse_factor_type(factor_type)
        if ftype is not MfaFactorType.SMS:
            raise ChallengeNotSupported(ftype)
        factor = self._repo.get_for_member_and_type(member.id, MfaFactorType.SMS)
        if factor is None:
            raise FactorNotEnrolled(MfaFactorType.SMS)

        now = _utc_now()
        if factor.locked_at is not None and now - factor.locked_at < LOCKOUT_DURATION:
            # Still inside the lockout window — refuse rather than hand out a fresh
            # code (which would let an attacker keep guessing indefinitely). This
            # check stays FIRST: a locked factor must surface 423, never 429, even
            # when both conditions would otherwise apply.
            raise ChallengeFactorLocked()

        # RATE LIMIT: refuse a resend inside SMS_RESEND_INTERVAL of the prior send
        # (429) BEFORE the SMS port is called — the cost/bombing control. A factor
        # with no outstanding/prior challenge (`sms_challenge_expires_at is None`)
        # is never limited on its first send.
        _enforce_sms_resend_interval(factor.sms_challenge_expires_at, now)

        code = generate_sms_code()
        try:
            self._sms.send_verification_code(
                phone_number=member.phone_number, code=code
            )
        except SmsDeliveryError as exc:
            raise SmsDeliveryFailed() from exc

        expires_at = now + SMS_CHALLENGE_TTL
        factor.sms_challenge_hash = hash_sms_code(code)
        factor.sms_challenge_expires_at = expires_at
        self._repo.flush()
        return ChallengeResult(
            challenge_id=factor.id,
            delivery=f"SMS_CODE_SENT:{_mask_phone(member.phone_number)}",
            expires_at=expires_at,
        )
