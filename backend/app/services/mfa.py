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

import secrets
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.adapters.sms.port import SmsDeliveryError, SmsSender
from app.auth.mfa import (
    SecretCipher,
    generate_totp_secret,
    totp_provisioning_uri,
)
from app.models.identity import MfaFactor, MfaFactorStatus, MfaFactorType
from app.models.membership import Member
from app.repositories.identity import MfaFactorRepository

# Length of the out-of-band SMS one-time code (digits).
SMS_CODE_DIGITS = 6


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


@dataclass(frozen=True)
class EnrollmentResult:
    """The enrollment outcome projected onto the contract's response fields."""

    enrollment_id: uuid.UUID
    binding_challenge: str


def _parse_factor_type(value: str) -> MfaFactorType:
    """Resolve the request factor_type to a SUPPORTED enum, or raise 422.

    Accepts only TOTP/SMS. BIOMETRIC (a valid contract value) and any unknown
    string are rejected — BIOMETRIC is device-local, not a server-stored secret.
    """
    try:
        return MfaFactorType(value)
    except ValueError as exc:
        raise UnsupportedFactorType(value) from exc


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
        """
        code = "".join(secrets.choice("0123456789") for _ in range(SMS_CODE_DIGITS))
        try:
            self._sms.send_verification_code(
                phone_number=member.phone_number, code=code
            )
        except SmsDeliveryError as exc:
            raise SmsDeliveryFailed() from exc

        if existing is not None:
            existing.status = MfaFactorStatus.PENDING
            existing.confirmed_at = None
            self._repo.flush()
            factor = existing
        else:
            factor = self._repo.create_pending(
                member_id=member.id,
                factor_type=MfaFactorType.SMS,
                secret_ciphertext=None,
            )
        return factor, f"SMS_CODE_SENT:{_mask_phone(member.phone_number)}"
