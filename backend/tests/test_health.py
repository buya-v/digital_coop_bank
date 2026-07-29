"""Health/readiness endpoint tests. Requires fastapi + httpx (CI installs them)."""
import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_mnt():
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["currency"] == "MNT"


def test_only_expected_feature_routes():
    # EP-1 onboarding + member self-service are the current feature surface.
    # Guard against any OTHER feature endpoint being wired in without its
    # contract/legal clearance. Slice 2 (T1) adds the US-1.3 config-driven
    # common-bond eligibility check; slice 2 (T2) adds the ХУР/XYP KYC
    # session/status endpoints; the profile slice (T2) adds getMyProfile /
    # updateMyProfile (the first post-auth endpoints). The consents+devices
    # slice (T1) adds listMyConsents / upsertMyConsent (member consent history)
    # and listDevices (trusted-device listing) — all memberOAuth2-only;
    # revokeDevice is DEFERRED (step-up) and intentionally NOT mounted.
    paths = {route.path for route in app.routes}
    assert paths >= {"/health", "/ready"}
    feature_ish = {p for p in paths if p.startswith("/api/")}
    expected = {
        "/api/v1/onboarding/applications",
        "/api/v1/onboarding/applications/current",
        "/api/v1/onboarding/eligibility-check",
        "/api/v1/onboarding/kyc/sessions",
        "/api/v1/onboarding/kyc/status",
        "/api/v1/members/me",
        "/api/v1/members/me/profile",
        "/api/v1/members/me/consents",
        "/api/v1/members/me/consents/{consent_type}",
        "/api/v1/auth/devices",
        "/api/v1/auth/mfa/enrollments",
    }
    assert feature_ish == expected, f"unexpected feature routes: {feature_ish - expected}"
