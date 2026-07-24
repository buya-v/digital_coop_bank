"""Tests for /ready's DB liveness check.

Never touches a real database: the DB-facing dependency (`app.main.ready_session`)
is swapped via `app.dependency_overrides` for a fake/None session in every case.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient

from app.main import app, ready_session

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.clear()


def test_ready_unconfigured_is_degraded_200():
    """No DB configured is a valid scaffold/dev state: 200, not 503."""

    def override():
        yield None

    app.dependency_overrides[ready_session] = override

    r = client.get("/ready")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "degraded"
    assert body["db"] == "unconfigured"
    assert body["currency"] == "MNT"


def test_ready_ok_path_with_fake_session():
    """A configured, reachable DB: SELECT 1 succeeds -> 200 ready/ok."""

    class FakeSession:
        def execute(self, *_args, **_kwargs):
            return "fake-select-1-result"

    def override():
        yield FakeSession()

    app.dependency_overrides[ready_session] = override

    r = client.get("/ready")

    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ready"
    assert body["db"] == "ok"
    assert body["currency"] == "MNT"


def test_ready_error_path_returns_503_without_leaking_exception_text():
    """Any exception from the liveness check -> 503, and never leaked verbatim."""

    secret_marker = "super-secret-connection-detail-should-not-leak"

    class FailingSession:
        def execute(self, *_args, **_kwargs):
            raise RuntimeError(secret_marker)

    def override():
        yield FailingSession()

    app.dependency_overrides[ready_session] = override

    r = client.get("/ready")

    assert r.status_code == 503
    body = r.json()
    assert body["status"] == "unready"
    assert body["db"] == "error"
    assert body["currency"] == "MNT"
    assert secret_marker not in r.text
