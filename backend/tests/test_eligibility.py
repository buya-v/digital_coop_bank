"""EP-1 config-driven common-bond eligibility tests (US-1.3, checkOnboardingEligibility).

No real database: an in-memory SQLite engine is created INSIDE the test and
`app.api.deps.get_session` is overridden to bind to it (StaticPool keeps a single
shared connection so the recorded outcome survives across request-scoped
sessions). Mirrors the slice-1 test harness in `test_onboarding.py`.

Covers the pure engine directly and the endpoint end-to-end: the eligible path,
the ineligible path (with failed criteria + remediation), and malformed answers
(a type mismatch -> uniform 422). Also the already-passed 409 and the 401 the
contract declares.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient
from sqlalchemy import Table, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.config import get_common_bond_rules
from app.main import app
from app.models.identity import OnboardingApplication
from app.services.eligibility import (
    EligibilityAnswersInvalid,
    evaluate,
)

_APPLICATIONS = "/api/v1/onboarding/applications"
_ELIGIBILITY = "/api/v1/onboarding/eligibility-check"

# A complete, passing answer bag for the shipped default rule set.
_ELIGIBLE_ANSWERS: dict[str, object] = {
    "age": 30,
    "bond_type": "EMPLOYER",
    "bond_affirmation": True,
}


@pytest.fixture()
def client() -> Iterator[TestClient]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# --- Pure engine (no DB, no HTTP) --------------------------------------------


def test_engine_eligible_when_all_rules_pass() -> None:
    outcome = evaluate(_ELIGIBLE_ANSWERS, get_common_bond_rules())
    assert outcome.eligible is True
    assert outcome.failed_criteria == []
    assert outcome.remediation == []
    assert outcome.ruleset_version == "common-bond-default-v1"


def test_engine_reports_each_failed_criterion_with_remediation() -> None:
    outcome = evaluate(
        {"age": 16, "bond_type": "SOMETHING_ELSE", "bond_affirmation": False},
        get_common_bond_rules(),
    )
    assert outcome.eligible is False
    assert set(outcome.failed_criteria) == {
        "AGE_OF_CAPACITY",
        "BOND_TYPE_DECLARED",
        "COMMON_BOND_AFFIRMED",
    }
    # One remediation string per failed rule.
    assert len(outcome.remediation) == 3


def test_engine_missing_answer_fails_criterion_not_malformed() -> None:
    # A missing field is ineligible, NOT a malformed-answer error.
    outcome = evaluate({"age": 30, "bond_type": "EMPLOYER"}, get_common_bond_rules())
    assert outcome.eligible is False
    assert outcome.failed_criteria == ["COMMON_BOND_AFFIRMED"]


def test_engine_malformed_age_raises() -> None:
    with pytest.raises(EligibilityAnswersInvalid) as exc:
        evaluate({**_ELIGIBLE_ANSWERS, "age": "eighteen"}, get_common_bond_rules())
    assert exc.value.field == "age"


def test_engine_float_age_is_malformed_no_float() -> None:
    # The no-float non-negotiable: a float age is rejected as malformed.
    with pytest.raises(EligibilityAnswersInvalid):
        evaluate({**_ELIGIBLE_ANSWERS, "age": 18.5}, get_common_bond_rules())


def test_engine_bool_age_is_malformed() -> None:
    # bool is an int subclass; True must not sneak through the gte comparison.
    with pytest.raises(EligibilityAnswersInvalid):
        evaluate({**_ELIGIBLE_ANSWERS, "age": True}, get_common_bond_rules())


# --- Endpoint (contract conformance) -----------------------------------------


def test_eligible_path_returns_200_eligible_true(client: TestClient) -> None:
    token = _create(client)
    r = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["eligible"] is True
    assert body["failed_criteria"] == []
    assert body["remediation"] == []


def test_ineligible_path_returns_reasons(client: TestClient) -> None:
    token = _create(client)
    r = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": {"age": 15, "bond_affirmation": False},
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["eligible"] is False
    assert "AGE_OF_CAPACITY" in body["failed_criteria"]
    assert "COMMON_BOND_AFFIRMED" in body["failed_criteria"]
    assert body["remediation"]  # remediation guidance is surfaced


def test_malformed_answers_are_422(client: TestClient) -> None:
    token = _create(client)
    r = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": {**_ELIGIBLE_ANSWERS, "age": "not-a-number"},
    })
    assert r.status_code == 422
    error = r.json()["error"]
    assert error["code"] == "VALIDATION_FAILED"
    assert error["details"][0]["field"] == "age"


def test_outcome_is_recorded_on_the_draft(client: TestClient) -> None:
    token = _create(client)
    client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    # The recorded outcome is visible on the resumed draft state.
    g = client.get("/api/v1/onboarding/applications/current", headers=_auth(token))
    assert g.status_code == 200
    kpi = g.json()["kpi_timestamps"]
    assert "eligibility_checked_at" in kpi


def test_second_passed_check_is_409_already_checked(client: TestClient) -> None:
    token = _create(client)
    first = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    assert first.json()["eligible"] is True
    second = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ALREADY_CHECKED_PASSED"


def test_failed_check_may_be_retried(client: TestClient) -> None:
    token = _create(client)
    fail = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": {"age": 15},
    })
    assert fail.json()["eligible"] is False
    # A failed check does not lock the applicant out — they may correct and retry.
    retry = client.post(_ELIGIBILITY, headers=_auth(token), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    assert retry.status_code == 200
    assert retry.json()["eligible"] is True


def test_missing_token_is_401(client: TestClient) -> None:
    r = client.post(_ELIGIBILITY, json={"eligibility_answers": _ELIGIBLE_ANSWERS})
    assert r.status_code == 401


def test_bogus_token_is_401(client: TestClient) -> None:
    r = client.post(_ELIGIBILITY, headers=_auth("not-a-real-token"), json={
        "eligibility_answers": _ELIGIBLE_ANSWERS,
    })
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHENTICATED"
