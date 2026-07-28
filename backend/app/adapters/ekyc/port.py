"""eKYC provider PORT — the interface the onboarding service depends on.

A ХУР/XYP STATE-REGISTER lookup (CLAUDE.md blocking question #2, DEC-5): the
provider is handed the applicant's identity (the national `registration_number`
is the register key, DEC-6) and returns a verification outcome. This is NOT a
biometric face-match/liveness flow — no image, selfie, or liveness payload
crosses this boundary.

Two calls model the real async flow:

- `start_verification` opens an inquiry and returns its handle
  (`inquiry_id` + `session_token`) with status IN_PROGRESS.
- `get_result` polls that inquiry and returns its current status, plus — once
  the register resolves — the authoritative fields the state register returned.

The response surface is deliberately confined to what the OpenAPI contract and
04 §2.2 already name (KycSessionResponse / KycStatusResponse; E-2 KycSubmission:
`ocr_extracted_fields`, `result_reasons`, `evidence_refs`) plus the
KYC-verified `registration_number` DEC-6(d) makes authoritative. No ХУР/XYP
wire-format field is invented here.
"""
from __future__ import annotations

import abc
import dataclasses

from app.models.identity import KycStatus


@dataclasses.dataclass(frozen=True)
class EkycApplicant:
    """Identity handed to the state register for lookup.

    Role-neutral and biometric-free. `registration_number` (2 Cyrillic + 8
    digits, DEC-6) is the register key; the name parts and DOB let the register
    corroborate the record. Every field is Optional because the pre-auth draft
    may hand off a partially-filled identity (the register decides sufficiency).
    """

    registration_number: str | None
    ner: str | None
    etsgiin_ner: str | None
    ovog: str | None
    date_of_birth: str | None  # ISO-8601 date string (no float, no tz math)


@dataclasses.dataclass(frozen=True)
class EkycSession:
    """Handle returned by `start_verification` (backs KycSessionResponse)."""

    inquiry_id: str
    session_token: str
    status: KycStatus  # IN_PROGRESS at creation (contract pins the literal)


@dataclasses.dataclass(frozen=True)
class EkycResult:
    """Outcome returned by `get_result` (backs getKycStatus + promotion).

    `verified_*` / `verified_fields` / `evidence` / `reasons` are populated only
    once the register RESOLVES (APPROVED / PENDING_REVIEW); while IN_PROGRESS they
    are empty. `verified_registration_number` is the register-authoritative value
    (DEC-6(d)) — it drives the E-1 Member's identity key at promotion and the
    409 REGISTRATION_NUMBER_MISMATCH guard.
    """

    inquiry_id: str
    status: KycStatus
    verified_registration_number: str | None
    verified_fields: dict[str, object]  # -> E-2 KycSubmission.ocr_extracted_fields
    evidence: dict[str, object]  # -> E-2 KycSubmission.evidence_refs
    reasons: dict[str, object]  # -> E-2 KycSubmission.result_reasons
    retry_guidance: str | None  # -> KycStatusResponse.retry_guidance


class EkycProviderError(Exception):
    """The eKYC provider is unreachable / errored (maps to 502 VENDOR_UNAVAILABLE).

    Kept provider-neutral: the contract's 502 is VENDOR_UNAVAILABLE, the vendor
    being the TBD state-register provider.
    """


class EkycProvider(abc.ABC):
    """Port: an eKYC state-register verification provider."""

    @abc.abstractmethod
    def start_verification(self, applicant: EkycApplicant) -> EkycSession:
        """Open an inquiry for `applicant`; return its handle (IN_PROGRESS)."""

    @abc.abstractmethod
    def get_result(self, inquiry_id: str) -> EkycResult:
        """Poll `inquiry_id`; return its current status and (once resolved) fields."""
