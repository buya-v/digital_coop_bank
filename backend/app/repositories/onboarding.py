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

    def get_by_resume_token_hash_for_update(
        self, resume_token_hash: str
    ) -> OnboardingApplication | None:
        """Resolve the draft AND take a row-level lock on it (`SELECT ... FOR
        UPDATE`) for a read-modify-write that must serialize.

        Used by the KYC service to serialize the APPROVED->promote transition:
        two concurrent getKycStatus polls that both observe APPROVED would
        otherwise both create a Member (only backstopped by a DB uniqueness
        violation -> 500). With the lock, the second poll blocks until the first
        commits, then re-reads the now-frozen APPROVED draft and is idempotent.

        `populate_existing=True` forces the already-identity-mapped instance to be
        REFRESHED from the freshly-locked row (rather than returning stale
        in-memory column values) — essential so the caller re-reads the committed
        APPROVED status, not the pre-lock IN_PROGRESS it may have loaded earlier.

        NOTE: Postgres honours `FOR UPDATE`; SQLite (tests) silently ignores it,
        so the block-and-serialize behaviour is Postgres-only, but the caller's
        re-read idempotency guard yields exactly one Member on either backend.
        """
        stmt = (
            select(OnboardingApplication)
            .where(OnboardingApplication.resume_token_hash == resume_token_hash)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def update(self, application: OnboardingApplication) -> OnboardingApplication:
        """Persist mutations to an already-tracked draft (flush, no commit)."""
        self.flush()
        return application
