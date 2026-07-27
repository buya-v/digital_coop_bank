"""Onboarding application service — business logic for EP-1 slice 1.

Owns the create/get/update rules for the pre-auth onboarding DRAFT:

- Bootstrap token: `create` mints a high-entropy, application-scoped token,
  returns the RAW token exactly once, and persists only its SHA-256 hash. This
  is a minimal capability credential, NOT the full OAuth2/OIDC + MFA/step-up
  stack (a later slice).
- Status: a draft is created DRAFT. `update_step` refuses to edit a non-DRAFT
  application (the DRAFT->SUBMITTED transition is the KYC hand-off, a later
  slice — the guard is present so a resumed, already-submitted draft is frozen).
- DEC-6 identity fields are mirrored onto the draft's columns AND into
  `onboarding_state.saved_data` (which backs the Current view).
- `registration_number` is validated STRUCTURALLY only (2 Cyrillic letters + 8
  digits). The check-digit algorithm is unpublished (CLAUDE.md / DEC-6) and is
  NEVER guessed here.

No money, no ledger, no ХУР/state-register call — later slices.
"""
from __future__ import annotations

import datetime
import hashlib
import re
import secrets

from sqlalchemy.orm import Session

from app.models.identity import OnboardingApplication, OnboardingApplicationStatus
from app.repositories.onboarding import OnboardingApplicationRepository

# 2 Cyrillic letters + 8 digits. STRUCTURAL only (CLAUDE.md / DEC-6): nothing
# beyond shape is asserted. The Cyrillic block U+0400-U+04FF covers the
# Mongolian-specific letters Ө/Ү that appear in registration numbers.
_REGISTRATION_NUMBER_RE = re.compile(r"^[Ѐ-ӿ]{2}[0-9]{8}$")

# DEC-6 identity fields a PATCH may set on the draft. `mrz_name_latin` is
# deliberately absent: it is KYC-populated verbatim from the document MRZ, never
# client-supplied (DEC-6).
_PATCHABLE_FIELDS = (
    "ner",
    "etsgiin_ner",
    "ovog",
    "registration_number",
    "address_line_1",
    "address_line_2",
    "city",
    "region",
    "postal_code",
    "country",
    "date_of_birth",
)

# Fields that constitute a "complete" identity step, used only for progress_pct
# (a presentation percentage — NOT money; float is fine here).
_IDENTITY_REQUIRED = (
    "ner",
    "etsgiin_ner",
    "registration_number",
    "address_line_1",
    "city",
    "date_of_birth",
)

_IDENTITY_STEP = "IDENTITY"


class OnboardingError(Exception):
    """Base for onboarding domain errors (mapped to HTTP by the router)."""


class ChannelUnverified(OnboardingError):
    """The contact channel was not verified (maps to 422 CHANNEL_UNVERIFIED)."""


class RegistrationNumberInvalid(OnboardingError):
    """registration_number failed STRUCTURAL validation (maps to 422)."""

    def __init__(self) -> None:
        super().__init__(
            "registration_number must be 2 Cyrillic letters followed by 8 digits"
        )


class ApplicationNotDraft(OnboardingError):
    """A non-DRAFT application cannot accept step edits (maps to 409)."""


def _hash_token(raw_token: str) -> str:
    """SHA-256 hex of the bootstrap token.

    The raw token is high-entropy random (`secrets.token_urlsafe`), so a single
    fast hash is appropriate — this is a capability token, not a low-entropy
    password (no salt/KDF needed). Only the hash is ever persisted, so a leaked
    row does not yield a usable token.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _now_iso() -> str:
    """UTC instant, ISO-8601. UTC is the storage standard; no Mongolia offset is
    hardcoded (the two-timezone / no-DST rule is a display concern, CLAUDE.md)."""
    # `datetime.timezone.utc` (not the 3.11 `datetime.UTC` alias UP017 suggests):
    # the documented dev machine runs 3.9 (see main.py / backend/README.md).
    return datetime.datetime.now(datetime.timezone.utc).isoformat()  # noqa: UP017


class OnboardingService:
    def __init__(self, session: Session) -> None:
        self._repo = OnboardingApplicationRepository(session)

    def create_application(
        self, *, email: str, phone_number: str, channel_verification_code: str
    ) -> tuple[OnboardingApplication, str]:
        """Create a DRAFT and return (application, raw_resume_token).

        The raw token is returned to the caller ONCE; only its hash is stored.
        Channel verification is a stub for this slice: a present, non-blank code
        is accepted as proof of channel control (a blank code is rejected). Real
        OTP verification is deferred — documented, not silently assumed.
        """
        if not channel_verification_code or not channel_verification_code.strip():
            raise ChannelUnverified()
        raw_token = secrets.token_urlsafe(32)
        state: dict[str, object] = {
            "current_step": _IDENTITY_STEP,
            "saved_data": {},
            "progress_pct": 0.0,
            "kpi_timestamps": {"application_started_at": _now_iso()},
        }
        application = self._repo.create(
            email=email,
            phone_number=phone_number,
            resume_token_hash=_hash_token(raw_token),
            status=OnboardingApplicationStatus.DRAFT,
            onboarding_state=state,
        )
        return application, raw_token

    def get_current(self, resume_token: str) -> OnboardingApplication | None:
        """Resolve the draft the bootstrap token identifies, or None."""
        return self._repo.get_by_resume_token_hash(_hash_token(resume_token))

    def update_step(
        self, resume_token: str, patch: dict[str, object]
    ) -> OnboardingApplication | None:
        """Save DEC-6 step data onto the draft. Returns None if the token
        matches no draft; raises on a non-DRAFT status or invalid registration
        number.
        """
        application = self._repo.get_by_resume_token_hash(_hash_token(resume_token))
        if application is None:
            return None
        if application.status is not OnboardingApplicationStatus.DRAFT:
            raise ApplicationNotDraft()

        reg = patch.get("registration_number")
        if isinstance(reg, str) and _REGISTRATION_NUMBER_RE.match(reg) is None:
            raise RegistrationNumberInvalid()

        state = dict(application.onboarding_state or {})
        saved: dict[str, object] = dict(state.get("saved_data") or {})
        for field in _PATCHABLE_FIELDS:
            if field in patch:
                value = patch[field]
                setattr(application, field, value)
                saved[field] = (
                    value.isoformat() if isinstance(value, datetime.date) else value
                )
        state["saved_data"] = saved
        state["current_step"] = _IDENTITY_STEP
        state["progress_pct"] = self._progress_pct(saved)
        kpi: dict[str, object] = dict(state.get("kpi_timestamps") or {})
        kpi["identity_step_saved_at"] = _now_iso()
        state["kpi_timestamps"] = kpi
        application.onboarding_state = state
        return self._repo.update(application)

    @staticmethod
    def _progress_pct(saved: dict[str, object]) -> float:
        present = sum(1 for f in _IDENTITY_REQUIRED if saved.get(f))
        return round(present / len(_IDENTITY_REQUIRED) * 100, 1)
