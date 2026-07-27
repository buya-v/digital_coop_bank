"""EP-1 onboarding endpoint tests (create / get / update).

No real database: an in-memory SQLite engine is created INSIDE the test and
`app.api.deps.get_session` is overridden to bind to it. `StaticPool` keeps a
single shared connection so commits persist across the request-scoped sessions
(this is what makes the resume/get-after-patch assertions meaningful). Production
code stays Postgres/psycopg (app/db/session.py); SQLite lives ONLY here, which
the build brief explicitly permits.
"""
from __future__ import annotations

import uuid
from collections.abc import Iterator

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.main import app
from app.models.identity import OnboardingApplication

_CURRENT = "/api/v1/onboarding/applications/current"
_APPLICATIONS = "/api/v1/onboarding/applications"


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # Only the onboarding draft table is exercised; it has no FKs. Creating just
    # this table keeps SQLite away from the Postgres-specific DDL of other models.
    table = OnboardingApplication.__table__
    assert isinstance(table, Table)
    table.create(engine)
    test_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    def _override() -> Iterator[Session]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        table.drop(engine)
        engine.dispose()


def _create(client: TestClient, code: str = "123456") -> dict[str, object]:
    r = client.post(
        _APPLICATIONS,
        json={
            "email": "applicant@example.mn",
            "phone_number": "+97688112233",
            "channel_verification_code": code,
        },
    )
    assert r.status_code == 201, r.text
    body: dict[str, object] = r.json()
    return body


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_create_returns_201_application_id_and_resume_token(client: TestClient) -> None:
    body = _create(client)
    assert uuid.UUID(str(body["application_id"]))  # parses -> valid uuid
    assert body["resume_token"]
    assert body["kyc_status"] == "NOT_STARTED"  # contract-pinned literal
    assert isinstance(body["steps"], list)


def test_get_with_token_returns_draft(client: TestClient) -> None:
    token = str(_create(client)["resume_token"])
    r = client.get(_CURRENT, headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["current_step"] == "IDENTITY"
    assert body["saved_data"] == {}
    assert body["progress_pct"] == 0.0


def test_update_saves_dec6_field_and_get_reflects_it_resume(client: TestClient) -> None:
    token = str(_create(client)["resume_token"])
    headers = _auth(token)

    r = client.patch(
        _CURRENT,
        headers=headers,
        json={"ner": "Болд", "registration_number": "УБ12345678"},
    )
    assert r.status_code == 200
    assert {"field": "ner", "status": "VALID"} in r.json()["validation_results"]

    # Resume: a fresh GET (new request-scoped session) reflects the saved data.
    g = client.get(_CURRENT, headers=headers)
    assert g.status_code == 200
    saved = g.json()["saved_data"]
    assert saved["ner"] == "Болд"
    assert saved["registration_number"] == "УБ12345678"


def test_missing_token_is_rejected_401(client: TestClient) -> None:
    assert client.get(_CURRENT).status_code == 401
    assert client.patch(_CURRENT, json={"ner": "Болд"}).status_code == 401


def test_bogus_token_get_is_404_no_application(client: TestClient) -> None:
    r = client.get(_CURRENT, headers=_auth("not-a-real-token"))
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NO_APPLICATION"  # uniform Error envelope


def test_invalid_registration_number_shape_is_422(client: TestClient) -> None:
    token = str(_create(client)["resume_token"])
    r = client.patch(
        _CURRENT,
        headers=_auth(token),
        json={"registration_number": "12345678"},  # no 2-letter Cyrillic prefix
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"
