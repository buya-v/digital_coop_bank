"""Health/readiness endpoint tests. Requires fastapi + httpx (CI installs them)."""
import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_mnt():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["currency"] == "MNT"


def test_no_feature_routes_yet():
    # The scaffold must not have quietly grown feature endpoints.
    paths = {route.path for route in app.routes}
    assert paths >= {"/health", "/ready"}
    feature_ish = [p for p in paths if p.startswith("/api/")]
    assert feature_ish == [], f"unexpected feature routes in scaffold: {feature_ish}"
