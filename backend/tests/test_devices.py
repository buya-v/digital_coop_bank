"""Member device self-service tests — listDevices (T1).

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral
in-memory RSA keypair) MINTS member tokens, an in-memory SQLite engine holds two
seeded members (A and B) each with their OWN device bindings, and the REAL
devices router is mounted. `app.api.deps.get_session` and
`app.auth.deps.get_token_verifier` are overridden so the verifier trusts the dev
signer's public key.

Covered:
- GET returns ONLY the caller's ACTIVE (trusted) devices, ordered.
- A REVOKED binding is excluded ("trusted devices" = ACTIVE only).
- No / malformed token -> 401.
- IDOR (NON-VACUOUS): B is seeded with a distinct device; A's token never returns
  B's device, and vice versa.
- revokeDevice (DELETE /auth/devices/{id}) is DEFERRED (step-up) — the route is
  not mounted in this slice, so it does not resolve to a 2xx.
"""
from __future__ import annotations

import datetime
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")
pytest.importorskip("jwt", reason="PyJWT not installed on this machine; CI runs it")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.api.errors import register_error_handlers
from app.api.routers.devices import router as devices_router
from app.auth.deps import get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.models.identity import DeviceBinding, DevicePlatform, DeviceStatus
from app.models.membership import Member, MembershipStatus

SIGNER = DevRsaSigner()

BASE = datetime.datetime(2026, 1, 1, 8, 0, 0, tzinfo=datetime.timezone.utc)  # noqa: UP017


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_member(session: Session, **overrides: object) -> Member:
    fields: dict[str, object] = {
        "member_id": "DCB-AAAA1111",
        "ovog": "Бат",
        "etsgiin_ner": "Болд",
        "ner": "Түвшин",
        "mrz_name_latin": "BOLD TUVSHIN",
        "registration_number": "УБ11111111",
        "membership_status": MembershipStatus.PENDING_PAYMENT,
        "email": "a@example.mn",
        "phone_number": "+97688110001",
        "preferred_language": "mn",
    }
    fields.update(overrides)
    member = Member(**fields)
    session.add(member)
    session.flush()
    return member


def _seed_device(
    session: Session,
    member: Member,
    *,
    fingerprint: str,
    platform: DevicePlatform,
    status: DeviceStatus,
    offset_minutes: int,
) -> DeviceBinding:
    bound = BASE + datetime.timedelta(minutes=offset_minutes)
    device = DeviceBinding(
        member_id=member.id,
        device_fingerprint=fingerprint,
        platform=platform,
        push_token=None,
        biometric_enabled=False,
        status=status,
        bound_at=bound,
        last_seen_at=bound,
        revoked_at=(
            bound if status is DeviceStatus.REVOKED else None
        ),
    )
    session.add(device)
    session.flush()
    return device


@pytest.fixture()
def ctx() -> Iterator[SimpleNamespace]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Member.__table__.create(engine)
    DeviceBinding.__table__.create(engine)
    test_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    seed = test_session()
    member_a = _seed_member(
        seed,
        member_id="DCB-AAAA1111",
        registration_number="УБ11111111",
        email="a@example.mn",
        phone_number="+97688110001",
    )
    member_b = _seed_member(
        seed,
        member_id="DCB-BBBB2222",
        ovog="Цог",
        etsgiin_ner="Ганбат",
        ner="Оюун",
        registration_number="УБ22222222",
        email="b@example.mn",
        phone_number="+97688110002",
    )
    # A: two ACTIVE devices + one REVOKED (must be excluded).
    _seed_device(
        seed,
        member_a,
        fingerprint="A-ios",
        platform=DevicePlatform.IOS,
        status=DeviceStatus.ACTIVE,
        offset_minutes=1,
    )
    _seed_device(
        seed,
        member_a,
        fingerprint="A-web",
        platform=DevicePlatform.WEB,
        status=DeviceStatus.ACTIVE,
        offset_minutes=2,
    )
    _seed_device(
        seed,
        member_a,
        fingerprint="A-old",
        platform=DevicePlatform.ANDROID,
        status=DeviceStatus.REVOKED,
        offset_minutes=3,
    )
    # B: one DISTINCT ACTIVE device (so IDOR assertions are non-vacuous).
    _seed_device(
        seed,
        member_b,
        fingerprint="B-android",
        platform=DevicePlatform.ANDROID,
        status=DeviceStatus.ACTIVE,
        offset_minutes=1,
    )
    seed.commit()
    a_id, b_id = str(member_a.id), str(member_b.id)
    seed.close()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(devices_router)

    def _override_session() -> Iterator[Session]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_token_verifier] = lambda: SIGNER.verifier()

    try:
        yield SimpleNamespace(
            client=TestClient(app),
            a_id=a_id,
            b_id=b_id,
            token_a=SIGNER.mint(subject=a_id),
            token_b=SIGNER.mint(subject=b_id),
        )
    finally:
        app.dependency_overrides.clear()
        DeviceBinding.__table__.drop(engine)
        Member.__table__.drop(engine)
        engine.dispose()


# --- listDevices -------------------------------------------------------------


def test_list_returns_only_callers_active_devices(ctx: SimpleNamespace) -> None:
    r = ctx.client.get("/api/v1/auth/devices", headers=_auth(ctx.token_a))
    assert r.status_code == 200, r.text
    devices = r.json()["devices"]
    # Two ACTIVE, ordered by bound_at; the REVOKED one is excluded.
    assert [d["platform"] for d in devices] == ["IOS", "WEB"]
    assert len(devices) == 2


def test_list_no_token_is_401(ctx: SimpleNamespace) -> None:
    assert ctx.client.get("/api/v1/auth/devices").status_code == 401


def test_list_malformed_scheme_is_401(ctx: SimpleNamespace) -> None:
    r = ctx.client.get(
        "/api/v1/auth/devices", headers={"Authorization": f"Token {ctx.token_a}"}
    )
    assert r.status_code == 401


# --- IDOR: the token subject is the ONLY identity ----------------------------


def test_list_is_scoped_per_member(ctx: SimpleNamespace) -> None:
    a = ctx.client.get(
        "/api/v1/auth/devices", headers=_auth(ctx.token_a)
    ).json()["devices"]
    b = ctx.client.get(
        "/api/v1/auth/devices", headers=_auth(ctx.token_b)
    ).json()["devices"]
    # B sees only their own single distinct device; A never sees it.
    assert [d["platform"] for d in b] == ["ANDROID"]
    assert len(b) == 1
    a_ids = {d["id"] for d in a}
    assert b[0]["id"] not in a_ids


# --- revokeDevice is DEFERRED (step-up) --------------------------------------


def test_revoke_device_is_not_implemented_here(ctx: SimpleNamespace) -> None:
    # revokeDevice requires a stepUpAssertion (a later slice); the DELETE route
    # is intentionally NOT mounted, so it never resolves to a 2xx.
    r = ctx.client.delete(
        f"/api/v1/auth/devices/{ctx.a_id}", headers=_auth(ctx.token_a)
    )
    assert r.status_code in (404, 405)
    assert not (200 <= r.status_code < 300)
