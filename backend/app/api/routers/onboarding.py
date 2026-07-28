"""EP-1 onboarding router (04 §3.1) — first feature router.

Implements the following operations against the existing OpenAPI contract:

- createOnboardingApplication  POST  /api/v1/onboarding/applications          -> 201
- getCurrentOnboardingApplication  GET  /api/v1/onboarding/applications/current -> 200
- updateCurrentOnboardingApplication  PATCH /api/v1/onboarding/applications/current -> 200
- checkOnboardingEligibility  POST  /api/v1/onboarding/eligibility-check       -> 200

`checkOnboardingEligibility` (US-1.3) runs the CONFIG-DRIVEN common-bond
eligibility engine (`app.services.eligibility`) for the applicant behind the
bootstrap token and records the outcome on the draft. It does NOT choose a bond —
the rule set lives in configuration (`eligibility.common_bond_rules`).

Deferred (NOT built here): KYC, promotion, MFA/step-up, devices, profile,
consents.

Pydantic models mirror the OpenAPI OnboardingApplication* schemas EXACTLY
(property names, required fields, enums). The pinned literals are honoured:
create's `kyc_status` is fixed to "NOT_STARTED".

Bootstrap token (pre-auth). `create` mints an opaque, application-scoped
`resume_token` (returned once) and persists only its SHA-256 hash. `get`/`patch`
present it as `Authorization: Bearer <resume_token>` — the INFERRED transport the
contract's ep1 note pins as the applicant session (04 §3.0 requires a token; its
carrier is inferred). This is deliberately NOT the full OAuth2/OIDC + MFA/step-up
stack (memberOAuth2, stepUpAssertion) — that is a later slice.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_session
from app.api.errors import ApiError
from app.services.eligibility import (
    EligibilityAlreadyPassed,
    EligibilityAnswersInvalid,
    EligibilityService,
)
from app.services.onboarding import (
    ApplicationNotDraft,
    ChannelUnverified,
    OnboardingService,
    RegistrationNumberInvalid,
)

router = APIRouter(prefix="/api/v1/onboarding", tags=["EP-1"])

# The onboarding steps exposed to the applicant. Only IDENTITY is implemented in
# this slice; eligibility / KYC / MFA / consents are later slices and are NOT
# advertised here to avoid implying deferred features exist.
ONBOARDING_STEPS: tuple[dict[str, object], ...] = (
    {"key": "IDENTITY", "title": "Identity details", "status": "CURRENT"},
)


# --- I/O models (mirror openapi/schemas/ep1-identity.yaml) --------------------


class OnboardingApplicationCreateRequest(BaseModel):
    email: str
    phone_number: str
    channel_verification_code: str


class OnboardingApplicationCreateResponse(BaseModel):
    application_id: uuid.UUID
    resume_token: str
    steps: list[dict[str, object]]
    kyc_status: Literal["NOT_STARTED"] = "NOT_STARTED"


class OnboardingApplicationCurrent(BaseModel):
    application_id: uuid.UUID
    current_step: str
    saved_data: dict[str, object]
    progress_pct: float
    kpi_timestamps: dict[str, str]


class OnboardingApplicationPatchRequest(BaseModel):
    # All DEC-6 identity fields optional (a PATCH saves whatever step data it
    # has). `mrz_name_latin` is intentionally absent — KYC-populated, never
    # client-supplied (DEC-6).
    ner: Optional[str] = None  # noqa: UP045
    etsgiin_ner: Optional[str] = None  # noqa: UP045
    ovog: Optional[str] = None  # noqa: UP045
    registration_number: Optional[str] = None  # noqa: UP045
    address_line_1: Optional[str] = None  # noqa: UP045
    address_line_2: Optional[str] = None  # noqa: UP045
    city: Optional[str] = None  # noqa: UP045
    region: Optional[str] = None  # noqa: UP045
    postal_code: Optional[str] = None  # noqa: UP045
    country: Optional[str] = None  # noqa: UP045
    date_of_birth: Optional[datetime.date] = None  # noqa: UP045


class OnboardingApplicationPatchResponse(BaseModel):
    current_step: str
    validation_results: list[dict[str, object]]


class EligibilityCheckRequest(BaseModel):
    # `additionalProperties: true` in the contract — a free-form answer bag keyed
    # by the config rule set's `field`s. Defaults to empty so an absent body is a
    # (failing) check rather than a framework 422.
    eligibility_answers: dict[str, object] = {}


class EligibilityCheckResponse(BaseModel):
    eligible: bool
    failed_criteria: list[str]
    remediation: list[str]


# --- Pre-auth bootstrap-token dependency -------------------------------------


def resume_token(
    authorization: Optional[str] = Header(default=None),  # noqa: UP045
) -> str:
    """Extract the applicant's bootstrap token from `Authorization: Bearer ...`.

    Missing or malformed -> 401 UNAUTHENTICATED (the contract's universal 401).
    """
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "Missing or malformed bootstrap resume token "
            "(expected 'Authorization: Bearer <resume_token>').",
        )
    return token.strip()


# --- Routes ------------------------------------------------------------------


@router.post(
    "/applications",
    status_code=status.HTTP_201_CREATED,
    response_model=OnboardingApplicationCreateResponse,
    summary="Start an onboarding application (pre-auth bootstrap).",
)
def create_onboarding_application(
    body: OnboardingApplicationCreateRequest,
    session: Session = Depends(get_session),
) -> OnboardingApplicationCreateResponse:
    service = OnboardingService(session)
    try:
        application, token = service.create_application(
            email=body.email,
            phone_number=body.phone_number,
            channel_verification_code=body.channel_verification_code,
        )
    except ChannelUnverified as exc:
        raise ApiError(
            422,  # status.HTTP_422_* is deprecated in the installed starlette
            "CHANNEL_UNVERIFIED",
            "The contact channel was not verified.",
        ) from exc
    session.commit()
    return OnboardingApplicationCreateResponse(
        application_id=application.id,
        resume_token=token,
        steps=[dict(step) for step in ONBOARDING_STEPS],
        kyc_status="NOT_STARTED",
    )


@router.get(
    "/applications/current",
    response_model=OnboardingApplicationCurrent,
    summary="Get the applicant's in-progress application.",
)
def get_current_onboarding_application(
    token: str = Depends(resume_token),
    session: Session = Depends(get_session),
) -> OnboardingApplicationCurrent:
    service = OnboardingService(session)
    application = service.get_current(token)
    if application is None:
        raise ApiError(
            status.HTTP_404_NOT_FOUND,
            "NO_APPLICATION",
            "No in-progress onboarding application for this token.",
        )
    state = application.onboarding_state or {}
    return OnboardingApplicationCurrent(
        application_id=application.id,
        current_step=state.get("current_step", "IDENTITY"),
        saved_data=state.get("saved_data", {}),
        progress_pct=state.get("progress_pct", 0.0),
        kpi_timestamps=state.get("kpi_timestamps", {}),
    )


@router.patch(
    "/applications/current",
    response_model=OnboardingApplicationPatchResponse,
    summary="Save onboarding step data (DEC-6 identity fields).",
)
def update_current_onboarding_application(
    body: OnboardingApplicationPatchRequest,
    token: str = Depends(resume_token),
    session: Session = Depends(get_session),
) -> OnboardingApplicationPatchResponse:
    service = OnboardingService(session)
    patch = body.model_dump(exclude_unset=True)
    try:
        application = service.update_step(token, patch)
    except RegistrationNumberInvalid as exc:
        raise ApiError(
            422,  # status.HTTP_422_* is deprecated in the installed starlette
            "VALIDATION_FAILED",
            str(exc),
            details=[
                {
                    "field": "registration_number",
                    "code": "INVALID_FORMAT",
                    "message": str(exc),
                }
            ],
        ) from exc
    except ApplicationNotDraft as exc:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "STATE_CONFLICT",
            "Application is no longer a draft and cannot be edited.",
        ) from exc
    if application is None:
        # PATCH's contract has no 404; a token that resolves to nothing is an
        # unauthenticated applicant.
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "The resume token does not match an in-progress application.",
        )
    session.commit()
    state = application.onboarding_state or {}
    validation_results: list[dict[str, object]] = [
        {"field": field, "status": "VALID"} for field in patch
    ]
    return OnboardingApplicationPatchResponse(
        current_step=state.get("current_step", "IDENTITY"),
        validation_results=validation_results,
    )


@router.post(
    "/eligibility-check",
    response_model=EligibilityCheckResponse,
    summary="Run the data-driven common-bond eligibility check.",
)
def check_onboarding_eligibility(
    body: EligibilityCheckRequest,
    token: str = Depends(resume_token),
    session: Session = Depends(get_session),
) -> EligibilityCheckResponse:
    service = EligibilityService(session)
    try:
        application, outcome = service.check_eligibility(token, body.eligibility_answers)
    except EligibilityAnswersInvalid as exc:
        raise ApiError(
            422,  # status.HTTP_422_* is deprecated in the installed starlette
            "VALIDATION_FAILED",
            str(exc),
            details=[
                {
                    "field": exc.field,
                    "code": "INVALID_FORMAT",
                    "message": exc.message,
                }
            ],
        ) from exc
    except EligibilityAlreadyPassed as exc:
        raise ApiError(
            status.HTTP_409_CONFLICT,
            "ALREADY_CHECKED_PASSED",
            "Eligibility has already passed for this applicant.",
        ) from exc
    if application is None or outcome is None:
        # A token that resolves to no draft is an unauthenticated applicant
        # (the contract models eligibility-check's failure of the session as 401).
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED,
            "UNAUTHENTICATED",
            "The resume token does not match an in-progress application.",
        )
    session.commit()
    return EligibilityCheckResponse(
        eligible=outcome.eligible,
        failed_criteria=outcome.failed_criteria,
        remediation=outcome.remediation,
    )
