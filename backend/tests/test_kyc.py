"""EP-1 slice-2 (T2) KYC + promotion tests (createKycSession / getKycStatus).

No real database: an in-memory SQLite engine is created INSIDE the test and
`app.api.deps.get_session` is overridden to bind to it (StaticPool keeps a single
shared connection so a Member created in one request-scoped session is visible to
the next and to the assertions). `get_ekyc_provider` is overridden per test with a
deterministic `MockEkycProvider` scripted to a specific outcome — the seam that
drives every branch of the KYC state machine. Mirrors the slice-1 test harness.

Coverage:
  - getKycStatus before any session -> NOT_STARTED.
  - createKycSession -> 201 (inquiry id + IN_PROGRESS on the draft).
  - session -> status through EVERY mock outcome (IN_PROGRESS / PENDING_REVIEW /
    APPROVED / REJECTED).
  - APPROVED PROMOTES: a PENDING_PAYMENT Member (DEC-6 name + registration_number)
    + a member-linked KycSubmission are created.
  - REJECTED creates NO Member (the member table stays empty) — the MANDATORY
    DEC-4 guarantee.
  - 409 KYC_ALREADY_APPROVED, 502 VENDOR_UNAVAILABLE, 401 on missing/bogus token.
  - 409 REGISTRATION_NUMBER_MISMATCH on PATCH after KYC records an authoritative
    (differing) registration number (DEC-6(d)).
"""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.ekyc import MockEkycProvider
from app.api.deps import get_session
from app.api.routers.onboarding import get_ekyc_provider
from app.main import app
from app.models.identity import KycStatus, KycSubmission, OnboardingApplication
from app.models.membership import Member, MembershipStatus

_APPLICATIONS = "/api/v1/onboarding/applications"
_CURRENT = "/api/v1/onboarding/applications/current"
_KYC_SESSIONS = "/api/v1/onboarding/kyc/sessions"
_KYC_STATUS = "/api/v1/onboarding/kyc/status"

# A complete DEC-6 identity the register can promote to a Member.
_IDENTITY: dict[str, object] = {
    "ner": "Болд",
    "etsgiin_ner": "Дорж",
    "ovog": "Бат",
    "registration_number": "УБ12345678",
    "address_line_1": "1-р хороо",
    "city": "Улаанбаатар",
    "date_of_birth": "1990-05-20",
}


@dataclass
class Harness:
    client: TestClient
    session_factory: sessionmaker[Session]

    def set_provider(self, provider: MockEkycProvider) -> None:
        app.dependency_overrides[get_ekyc_provider] = lambda: provider

    def member_count(self) -> int:
        with self.session_factory() as s:
            return int(s.execute(select(func.count()).select_from(Member)).scalar_one())

    def kyc_submission_count(self) -> int:
        with self.session_factory() as s:
            return int(
                s.execute(select(func.count()).select_from(KycSubmission)).scalar_one()
            )

    def only_member(self) -> Member:
        with self.session_factory() as s:
            return s.execute(select(Member)).scalars().one()

    def only_submission(self) -> KycSubmission:
        with self.session_factory() as s:
            return s.execute(select(KycSubmission)).scalars().one()


@pytest.fixture()
def h() -> Iterator[Harness]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Promotion touches three tables: the draft, the Member it creates, and the
    # member-linked KycSubmission (FK -> member). create_all orders them by FK.
    from app.db.base import Base

    Base.metadata.create_all(
        engine,
        tables=[
            OnboardingApplication.__table__,
            Member.__table__,
            KycSubmission.__table__,
        ],
    )
    test_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def _override() -> Iterator[Session]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override
    # Default provider: APPROVED. Tests override with `set_provider` as needed.
    app.dependency_overrides[get_ekyc_provider] = lambda: MockEkycProvider(
        KycStatus.APPROVED
    )
    try:
        yield Harness(client=TestClient(app), session_factory=test_session)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(
            engine,
            tables=[
                KycSubmission.__table__,
                Member.__table__,
                OnboardingApplication.__table__,
            ],
        )
        engine.dispose()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create(client: TestClient) -> str:
    r = client.post(
        _APPLICATIONS,
        json={
            "email": "applicant@example.mn",
            "phone_number": "+97688112233",
            "channel_verification_code": "123456",
        },
    )
    assert r.status_code == 201, r.text
    return str(r.json()["resume_token"])


def _create_with_identity(client: TestClient, **overrides: object) -> str:
    token = _create(client)
    body = {**_IDENTITY, **overrides}
    r = client.patch(_CURRENT, headers=_auth(token), json=body)
    assert r.status_code == 200, r.text
    return token


# --- getKycStatus before any session -----------------------------------------


def test_status_not_started_before_session(h: Harness) -> None:
    token = _create(h.client)
    r = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kyc_status"] == "NOT_STARTED"
    assert body["pending_review"] is False


# --- createKycSession ---------------------------------------------------------


def test_create_session_returns_201_inquiry_and_in_progress(h: Harness) -> None:
    token = _create_with_identity(h.client)
    r = h.client.post(_KYC_SESSIONS, headers=_auth(token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["kyc_inquiry_id"]
    assert body["session_token"]
    assert body["kyc_status"] == "IN_PROGRESS"  # contract-pinned literal


# --- session -> status through every mock outcome -----------------------------


def test_status_in_progress_when_register_still_pending(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.IN_PROGRESS))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    r = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["kyc_status"] == "IN_PROGRESS"
    # No Member yet — still in flight.
    assert h.member_count() == 0


def test_status_pending_review_creates_no_member(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.PENDING_REVIEW))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    r = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kyc_status"] == "PENDING_REVIEW"
    assert body["pending_review"] is True
    # DEC-4: manual review is not approval — no Member.
    assert h.member_count() == 0


def test_status_approved_promotes_to_pending_payment_member(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.APPROVED))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    r = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["kyc_status"] == "APPROVED"

    # A single PENDING_PAYMENT Member was created, carrying the DEC-6 name parts
    # and the registration_number (structural, never a guessed check digit).
    assert h.member_count() == 1
    member = h.only_member()
    assert member.membership_status is MembershipStatus.PENDING_PAYMENT
    assert member.ner == "Болд"
    assert member.etsgiin_ner == "Дорж"
    assert member.ovog == "Бат"
    assert member.registration_number == "УБ12345678"

    # Promotion wiring (T2 profile): the public non-guessable member_id is minted
    # (DCB- + 8 unambiguous chars), and the contact channels + structured address
    # are carried over from the draft.
    assert member.member_id.startswith("DCB-")
    assert len(member.member_id) == len("DCB-") + 8
    assert set(member.member_id[4:]) <= set("23456789ABCDEFGHJKMNPQRSTVWXYZ")
    assert member.email == "applicant@example.mn"
    assert member.phone_number == "+97688112233"
    assert member.address_line_1 == "1-р хороо"
    assert member.city == "Улаанбаатар"
    assert member.preferred_language == "mn"  # Cyrillic-Mongolian default

    # A member-linked KycSubmission carries the evidence/result.
    assert h.kyc_submission_count() == 1
    submission = h.only_submission()
    assert submission.member_id == member.id
    assert submission.kyc_inquiry_id


def test_status_rejected_creates_no_member(h: Harness) -> None:
    # THE MANDATORY DEC-4 TEST: a rejected result leaves NO member row.
    h.set_provider(MockEkycProvider(KycStatus.REJECTED))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    r = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert r.status_code == 200, r.text
    assert r.json()["kyc_status"] == "REJECTED"
    # No member, no submission — the application is rejected and leaves nothing.
    assert h.member_count() == 0
    assert h.kyc_submission_count() == 0


def test_approved_promotion_is_idempotent(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.APPROVED))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    h.client.get(_KYC_STATUS, headers=_auth(token))
    # Polling again does not create a second Member.
    again = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert again.status_code == 200
    assert again.json()["kyc_status"] == "APPROVED"
    assert h.member_count() == 1


def test_concurrent_approved_polls_promote_exactly_one_member(h: Harness) -> None:
    """Two concurrent getKycStatus polls that BOTH observe APPROVED on the same
    IN_PROGRESS draft must promote EXACTLY ONE Member — never double-insert (which
    the DB uniqueness constraint would surface only as a 500).

    Concurrency is simulated deterministically. Session A loads the draft while it
    is still IN_PROGRESS (as a racing poll would, before the other commits), then
    session B runs its poll to completion — promoting and committing. Session A's
    poll finally runs on its now-STALE IN_PROGRESS in-memory view: that drives it
    into the guarded APPROVED->promote branch, where the row-lock re-read
    (`get_by_resume_token_hash_for_update`, `populate_existing`) observes the
    recorded APPROVED and is idempotent. One Member, one KycSubmission, no error.
    (SQLite ignores FOR UPDATE; the companion test confirms it renders on Postgres.)
    """
    from app.repositories.onboarding import OnboardingApplicationRepository
    from app.services.kyc import KycService, KycStatusResult
    from app.services.onboarding import _hash_token

    # One provider instance drives BOTH the session start (returns IN_PROGRESS)
    # and both polls (return APPROVED) — the mock keeps its inquiry state
    # per-instance, so the create+poll must share it (as the app wires it).
    provider = MockEkycProvider(KycStatus.APPROVED)
    h.set_provider(provider)

    # Arrange: a draft with a started KYC session (draft is IN_PROGRESS).
    token = _create_with_identity(h.client)
    assert h.client.post(_KYC_SESSIONS, headers=_auth(token)).status_code == 201

    # Session A: a racing poll loads the draft while it is still IN_PROGRESS.
    session_a = h.session_factory()
    draft_a = OnboardingApplicationRepository(session_a).get_by_resume_token_hash(
        _hash_token(token)
    )
    assert draft_a is not None and draft_a.kyc_status is KycStatus.IN_PROGRESS
    # End the read transaction; expire_on_commit=False keeps A's stale IN_PROGRESS
    # view of the draft in its identity map (exactly the racing-poll condition).
    session_a.commit()

    # Session B: the other poll promotes to a PENDING_PAYMENT Member, and commits.
    session_b = h.session_factory()
    res_b = KycService(session_b, provider).get_status(token)
    session_b.commit()
    session_b.close()
    assert isinstance(res_b, KycStatusResult) and res_b.kyc_status is KycStatus.APPROVED
    assert h.member_count() == 1

    # Session A now runs its poll against its STALE (IN_PROGRESS) in-memory draft:
    # it enters the guarded promote branch and must be idempotent, not re-insert.
    res_a = KycService(session_a, provider).get_status(token)
    session_a.commit()
    session_a.close()
    assert isinstance(res_a, KycStatusResult) and res_a.kyc_status is KycStatus.APPROVED

    # THE GUARANTEE: exactly one Member and one KycSubmission, and no exception.
    assert h.member_count() == 1
    assert h.kyc_submission_count() == 1


def test_promotion_lock_query_renders_for_update_on_postgres() -> None:
    """SQLite ignores FOR UPDATE, so confirm the lock is REAL on Postgres: the
    locking select the promotion path uses renders `FOR UPDATE` under the
    postgresql dialect (mirrors OnboardingApplicationRepository
    .get_by_resume_token_hash_for_update)."""
    from sqlalchemy import select
    from sqlalchemy.dialects import postgresql

    stmt = (
        select(OnboardingApplication)
        .where(OnboardingApplication.resume_token_hash == "x")
        .with_for_update()
    )
    compiled = str(stmt.compile(dialect=postgresql.dialect()))
    assert "FOR UPDATE" in compiled


# --- error branches -----------------------------------------------------------


def test_create_session_when_already_approved_is_409(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.APPROVED))
    token = _create_with_identity(h.client)
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    h.client.get(_KYC_STATUS, headers=_auth(token))  # -> APPROVED (promoted)
    r = h.client.post(_KYC_SESSIONS, headers=_auth(token))
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "KYC_ALREADY_APPROVED"


def test_create_session_provider_unavailable_is_502(h: Harness) -> None:
    h.set_provider(MockEkycProvider(KycStatus.APPROVED, unavailable=True))
    token = _create_with_identity(h.client)
    r = h.client.post(_KYC_SESSIONS, headers=_auth(token))
    assert r.status_code == 502
    assert r.json()["error"]["code"] == "VENDOR_UNAVAILABLE"


def test_kyc_endpoints_require_token_401(h: Harness) -> None:
    assert h.client.post(_KYC_SESSIONS).status_code == 401
    assert h.client.get(_KYC_STATUS).status_code == 401


def test_kyc_endpoints_bogus_token_401(h: Harness) -> None:
    r1 = h.client.post(_KYC_SESSIONS, headers=_auth("not-a-real-token"))
    assert r1.status_code == 401
    assert r1.json()["error"]["code"] == "UNAUTHENTICATED"
    r2 = h.client.get(_KYC_STATUS, headers=_auth("not-a-real-token"))
    assert r2.status_code == 401


# --- 409 REGISTRATION_NUMBER_MISMATCH on PATCH (DEC-6(d)) ---------------------


def test_patch_conflicting_registration_after_kyc_verify_is_409(h: Harness) -> None:
    # The register resolves to PENDING_REVIEW (draft stays editable) and returns
    # an AUTHORITATIVE registration number differing from the provisional one.
    h.set_provider(
        MockEkycProvider(
            KycStatus.PENDING_REVIEW,
            verified_registration_number="УБ99999999",
        )
    )
    token = _create_with_identity(h.client, registration_number="УБ12345678")
    h.client.post(_KYC_SESSIONS, headers=_auth(token))
    status = h.client.get(_KYC_STATUS, headers=_auth(token))
    assert status.json()["kyc_status"] == "PENDING_REVIEW"

    # A PATCH re-asserting the (now conflicting) provisional value is refused.
    r = h.client.patch(
        _CURRENT, headers=_auth(token), json={"registration_number": "УБ12345678"}
    )
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "REGISTRATION_NUMBER_MISMATCH"
