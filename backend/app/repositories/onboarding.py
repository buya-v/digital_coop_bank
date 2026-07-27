"""Repository for the pre-auth onboarding DRAFT (`OnboardingApplication`).

Lookup by `resume_token_hash` is the pre-auth access path: the applicant holds
the raw bootstrap token, the server stores only its hash, and the repository
resolves a draft from the hash. No business rules here — the service validates
and mutates; this layer only reads and writes rows.
"""
from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.identity import OnboardingApplication, OnboardingApplicationStatus
from app.repositories.base import BaseRepository


class OnboardingApplicationRepository(BaseRepository[OnboardingApplication]):
    model = OnboardingApplication

    def create(
        self,
        *,
        email: str,
        phone_number: str,
        resume_token_hash: str,
        status: OnboardingApplicationStatus,
        onboarding_state: dict[str, object],
    ) -> OnboardingApplication:
        """Insert a new draft and flush so its UUID PK is populated."""
        application = OnboardingApplication(
            email=email,
            phone_number=phone_number,
            resume_token_hash=resume_token_hash,
            status=status,
            onboarding_state=onboarding_state,
        )
        self.add(application)
        self.flush()
        return application

    def get_by_id(self, application_id: uuid.UUID) -> OnboardingApplication | None:
        return self.get(application_id)

    def get_by_resume_token_hash(
        self, resume_token_hash: str
    ) -> OnboardingApplication | None:
        """Resolve the draft an applicant's bootstrap token identifies."""
        stmt = select(OnboardingApplication).where(
            OnboardingApplication.resume_token_hash == resume_token_hash
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def update(self, application: OnboardingApplication) -> OnboardingApplication:
        """Persist mutations to an already-tracked draft (flush, no commit)."""
        self.flush()
        return application
