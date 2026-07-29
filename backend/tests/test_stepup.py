"""Step-up token issuance + verification tests — createStepUpToken, require_step_up,
revokeDevice (T2). The backend ISSUES a security credential here, so every test
names the attack it makes NON-VACUOUS.

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral RSA
keypair) mints member tokens, an in-memory SQLite engine holds two seeded members
(A and B), the REAL mfa + step-up + devices routers are mounted, and
`get_session` / `get_token_verifier` / `get_secret_cipher` / `get_sms_sender` are
overridden.

Security properties proved:
- enroll (PENDING) -> confirm-via-step-up with the correct TOTP code -> the factor
  flips ACTIVE and a token is minted (happy path + binding activation).
- A wrong TOTP code never mints a token (401 STEP_UP_FAILED).
- N wrong codes lock the factor (423 FACTOR_LOCKED) — no unlimited guessing.
- A minted token is SINGLE-USE: the second `require_step_up` presentation fails.
- An EXPIRED token is refused even though never consumed.
- A token minted for member A is refused when presented by member B (binding).
- revokeDevice requires a step-up assertion (401/403 without X-Step-Up-Token; 200
  with a valid one) and is IDOR-safe (A cannot revoke B's device -> 404).
"""
from __future__ import annotations

import datetime
import urllib.parse
import uuid
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")
pytest.importorskip("jwt", reason="PyJWT not installed on this machine; CI runs it")
pytest.importorskip("pyotp", reason="pyotp not installed on this machine; CI runs it")

import pyotp
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.sms.mock import MockSmsSender
from app.api.deps import get_session
from app.api.errors import register_error_handlers
from app.api.routers.devices import router as devices_router
from app.api.routers.mfa import get_sms_sender
from app.api.routers.mfa import router as mfa_router
from app.api.routers.stepup import router as stepup_router
from app.auth.deps import get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.auth.mfa import SecretCipher, get_secret_cipher
from app.models.identity import (
    DeviceBinding,
    DevicePlatform,
    DeviceStatus,
    MfaFactor,
    MfaFactorStatus,
    MfaFactorType,
    StepUpToken,
)
from app.models.membership import Member, MembershipStatus
from app.services.stepup import (
    MAX_FAILED_ATTEMPTS,
    hash_step_up_token,
)

SIGNER = DevRsaSigner()
# A test-only Fernet key + cipher (never a committed production key). The SAME
# cipher is injected into the app and used by the test to build TOTP codes.
TEST_CIPHER = SecretCipher(Fernet.generate_key().decode("ascii"))


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _secret_from_otpauth(uri: str) -> str:
    """Extract the base32 `secret` from an otpauth:// provisioning URI."""
    query = urllib.parse.urlparse(uri).query
    return urllib.parse.parse_qs(query)["secret"][0]


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


def _seed_device(session: Session, member_id: str) -> str:
    """Seed one ACTIVE device for a member; return its id (str)."""
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)  # noqa: UP017
    device = DeviceBinding(
        member_id=uuid.UUID(member_id),
        device_fingerprint="fp-seed",
        platform=DevicePlatform.IOS,
        push_token=None,
        biometric_enabled=False,
        status=DeviceStatus.ACTIVE,
        bound_at=now,
        last_seen_at=now,
        revoked_at=None,
    )
    session.add(device)
    session.flush()
    return str(device.id)


@pytest.fixture()
def ctx() -> Iterator[SimpleNamespace]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Member.__table__.create(engine)
    MfaFactor.__table__.create(engine)
    StepUpToken.__table__.create(engine)
    DeviceBinding.__table__.create(engine)
    test_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    seed = test_session()
    member_a = _seed_member(seed)
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
    seed.commit()
    a_id, b_id = str(member_a.id), str(member_b.id)
    b_device_id = _seed_device(seed, b_id)
    seed.commit()
    seed.close()

    sms = MockSmsSender()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(mfa_router)
    app.include_router(stepup_router)
    app.include_router(devices_router)

    def _override_session() -> Iterator[Session]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[get_token_verifier] = lambda: SIGNER.verifier()
    app.dependency_overrides[get_secret_cipher] = lambda: TEST_CIPHER
    app.dependency_overrides[get_sms_sender] = lambda: sms

    try:
        yield SimpleNamespace(
            client=TestClient(app),
            session_factory=test_session,
            a_id=a_id,
            b_id=b_id,
            b_device_id=b_device_id,
            token_a=SIGNER.mint(subject=a_id),
            token_b=SIGNER.mint(subject=b_id),
        )
    finally:
        app.dependency_overrides.clear()
        DeviceBinding.__table__.drop(engine)
        StepUpToken.__table__.drop(engine)
        MfaFactor.__table__.drop(engine)
        Member.__table__.drop(engine)
        engine.dispose()


# --- helpers -----------------------------------------------------------------


def _enroll_totp(ctx: SimpleNamespace, token: str) -> str:
    """Enroll a TOTP factor via the real endpoint; return the plaintext seed."""
    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(token),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    assert r.status_code == 201, r.text
    return _secret_from_otpauth(r.json()["binding_challenge"])


def _factor(ctx: SimpleNamespace, member_id: str) -> MfaFactor:
    session = ctx.session_factory()
    try:
        return session.execute(
            select(MfaFactor).where(
                MfaFactor.member_id == uuid.UUID(member_id),
                MfaFactor.factor_type == MfaFactorType.TOTP,
            )
        ).scalar_one()
    finally:
        session.close()


def _mint_token(ctx: SimpleNamespace, token: str, secret: str) -> str:
    """Enroll (if needed) then mint a step-up token with the current TOTP code."""
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(token),
        json={"factor_response": pyotp.TOTP(secret).now(), "action_context": {}},
    )
    assert r.status_code == 200, r.text
    return str(r.json()["step_up_token"])


# --- createStepUpToken: happy path + binding activation ----------------------


def test_enroll_then_confirm_via_step_up_happy_path(ctx: SimpleNamespace) -> None:
    """PROVES: a PENDING factor confirms via the first correct step-up code — the
    factor flips ACTIVE and a token + expiry are returned (the binding decision)."""
    secret = _enroll_totp(ctx, ctx.token_a)
    assert _factor(ctx, ctx.a_id).status is MfaFactorStatus.PENDING  # not yet confirmed

    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={"factor_response": pyotp.TOTP(secret).now(), "action_context": {}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["step_up_token"]
    assert body["expires_at"]

    # The factor is now ACTIVE (binding via first successful step-up) and only its
    # HASH is stored — the returned plaintext token appears in NO token row.
    factor = _factor(ctx, ctx.a_id)
    assert factor.status is MfaFactorStatus.ACTIVE
    assert factor.confirmed_at is not None
    session = ctx.session_factory()
    try:
        rows = session.execute(select(StepUpToken)).scalars().all()
        assert len(rows) == 1
        assert rows[0].token_hash != body["step_up_token"]
        assert rows[0].token_hash == hash_step_up_token(body["step_up_token"])
        assert rows[0].consumed_at is None  # freshly minted, not yet used
    finally:
        session.close()


def test_wrong_totp_is_rejected_and_mints_nothing(ctx: SimpleNamespace) -> None:
    """PROVES: a wrong challenge response is refused (401) and mints NO token —
    an attacker guessing codes never obtains a step-up credential."""
    _enroll_totp(ctx, ctx.token_a)
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={"factor_response": "000000", "action_context": {}},
    )
    assert r.status_code == 401, r.text
    assert r.json()["error"]["code"] == "STEP_UP_FAILED"
    session = ctx.session_factory()
    try:
        assert session.execute(select(StepUpToken)).scalars().first() is None
    finally:
        session.close()


def test_absent_factor_cannot_mint(ctx: SimpleNamespace) -> None:
    """PROVES: a member with NO enrolled factor cannot mint a step-up (401) — a
    never-enrolled credential authorizes nothing."""
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={"factor_response": "123456", "action_context": {}},
    )
    assert r.status_code == 401, r.text
    assert r.json()["error"]["code"] == "STEP_UP_FAILED"


def test_lockout_after_n_failures_returns_423(ctx: SimpleNamespace) -> None:
    """PROVES: after MAX_FAILED_ATTEMPTS wrong codes the factor LOCKS (423) — no
    unlimited TOTP guessing. Even a subsequently-correct code is refused 423."""
    secret = _enroll_totp(ctx, ctx.token_a)
    # Wrong codes below the threshold are 401...
    for _ in range(MAX_FAILED_ATTEMPTS - 1):
        r = ctx.client.post(
            "/api/v1/auth/step-up",
            headers=_auth(ctx.token_a),
            json={"factor_response": "000000", "action_context": {}},
        )
        assert r.status_code == 401, r.text
    # ...the threshold-crossing attempt LOCKS the factor (423).
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={"factor_response": "000000", "action_context": {}},
    )
    assert r.status_code == 423, r.text
    assert r.json()["error"]["code"] == "FACTOR_LOCKED"
    # While locked, even the CORRECT code is refused (423) — lockout is real.
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={"factor_response": pyotp.TOTP(secret).now(), "action_context": {}},
    )
    assert r.status_code == 423, r.text
    assert r.json()["error"]["code"] == "FACTOR_LOCKED"


# --- require_step_up via revokeDevice: single-use / expiry / binding ----------


def test_revoke_device_without_step_up_is_rejected(ctx: SimpleNamespace) -> None:
    """PROVES: revokeDevice needs a step-up assertion — no X-Step-Up-Token -> 401,
    and the device is NOT revoked."""
    device_id = _own_device(ctx, ctx.a_id)
    r = ctx.client.delete(
        f"/api/v1/auth/devices/{device_id}", headers=_auth(ctx.token_a)
    )
    assert r.status_code in (401, 403), r.text
    assert r.json()["error"]["code"] == "STEP_UP_REQUIRED"
    assert _device_status(ctx, device_id) is DeviceStatus.ACTIVE  # untouched


def test_revoke_device_with_valid_step_up_succeeds(ctx: SimpleNamespace) -> None:
    """PROVES: with a valid step-up token revokeDevice returns 200 REVOKED and the
    device is actually revoked."""
    secret = _enroll_totp(ctx, ctx.token_a)
    device_id = _own_device(ctx, ctx.a_id)
    step_up = _mint_token(ctx, ctx.token_a, secret)

    r = ctx.client.delete(
        f"/api/v1/auth/devices/{device_id}",
        headers={**_auth(ctx.token_a), "X-Step-Up-Token": step_up},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "REVOKED"
    assert _device_status(ctx, device_id) is DeviceStatus.REVOKED


def test_step_up_token_is_single_use(ctx: SimpleNamespace) -> None:
    """PROVES: a step-up token is consumed on first use — a REPLAY of the same
    token is refused (401), so it cannot authorize a second sensitive action."""
    secret = _enroll_totp(ctx, ctx.token_a)
    device_id = _own_device(ctx, ctx.a_id)
    step_up = _mint_token(ctx, ctx.token_a, secret)
    headers = {**_auth(ctx.token_a), "X-Step-Up-Token": step_up}

    first = ctx.client.delete(f"/api/v1/auth/devices/{device_id}", headers=headers)
    assert first.status_code == 200, first.text
    # Reuse the SAME token — it is already consumed.
    second = ctx.client.delete(f"/api/v1/auth/devices/{device_id}", headers=headers)
    assert second.status_code == 401, second.text
    assert second.json()["error"]["code"] == "STEP_UP_FAILED"


def test_expired_step_up_token_is_rejected(ctx: SimpleNamespace) -> None:
    """PROVES: an EXPIRED token is refused even though never consumed — short-lived
    is enforced, not merely advertised."""
    device_id = _own_device(ctx, ctx.a_id)
    plaintext = "expired-token-value"
    past = datetime.datetime.now(datetime.timezone.utc).replace(  # noqa: UP017
        tzinfo=None
    ) - datetime.timedelta(minutes=10)
    session = ctx.session_factory()
    try:
        session.add(
            StepUpToken(
                member_id=uuid.UUID(ctx.a_id),
                token_hash=hash_step_up_token(plaintext),
                requested_action=None,
                expires_at=past,
                consumed_at=None,
            )
        )
        session.commit()
    finally:
        session.close()

    r = ctx.client.delete(
        f"/api/v1/auth/devices/{device_id}",
        headers={**_auth(ctx.token_a), "X-Step-Up-Token": plaintext},
    )
    assert r.status_code == 401, r.text
    assert r.json()["error"]["code"] == "STEP_UP_FAILED"
    assert _device_status(ctx, device_id) is DeviceStatus.ACTIVE  # untouched


def test_token_minted_for_a_rejected_for_b(ctx: SimpleNamespace) -> None:
    """PROVES: member-binding — a token minted by A does NOT authorize B's action.
    B presents A's valid token against B's own device and is refused (401)."""
    secret = _enroll_totp(ctx, ctx.token_a)
    a_token = _mint_token(ctx, ctx.token_a, secret)
    b_device_id = _own_device(ctx, ctx.b_id)  # B's own device

    r = ctx.client.delete(
        f"/api/v1/auth/devices/{b_device_id}",
        headers={**_auth(ctx.token_b), "X-Step-Up-Token": a_token},
    )
    assert r.status_code == 401, r.text
    assert r.json()["error"]["code"] == "STEP_UP_FAILED"
    assert _device_status(ctx, b_device_id) is DeviceStatus.ACTIVE  # untouched
    # A's token is still unconsumed — B's foreign presentation did not spend it.
    session = ctx.session_factory()
    try:
        row = session.execute(
            select(StepUpToken).where(
                StepUpToken.token_hash == hash_step_up_token(a_token)
            )
        ).scalar_one()
        assert row.consumed_at is None
    finally:
        session.close()


def test_step_up_token_scoped_to_other_action_is_rejected(ctx: SimpleNamespace) -> None:
    """PROVES: action-binding — a token minted scoped to a DIFFERENT action does not
    authorize revokeDevice (403 STEP_UP_ACTION_MISMATCH), and the device is
    untouched. A general (unscoped) token still works (covered elsewhere)."""
    secret = _enroll_totp(ctx, ctx.token_a)
    device_id = _own_device(ctx, ctx.a_id)
    # Mint a token SCOPED to a different sensitive action.
    r = ctx.client.post(
        "/api/v1/auth/step-up",
        headers=_auth(ctx.token_a),
        json={
            "factor_response": pyotp.TOTP(secret).now(),
            "action_context": {"action": "updateProfile"},
        },
    )
    assert r.status_code == 200, r.text
    scoped = r.json()["step_up_token"]

    resp = ctx.client.delete(
        f"/api/v1/auth/devices/{device_id}",
        headers={**_auth(ctx.token_a), "X-Step-Up-Token": scoped},
    )
    assert resp.status_code == 403, resp.text
    assert resp.json()["error"]["code"] == "STEP_UP_ACTION_MISMATCH"
    assert _device_status(ctx, device_id) is DeviceStatus.ACTIVE  # untouched


def test_revoke_device_idor_returns_404(ctx: SimpleNamespace) -> None:
    """PROVES: IDOR — A holds a VALID step-up token but tries to revoke B's device;
    scoped by (member, id) it is a 404 (never a cross-member revoke). B's device
    stays ACTIVE."""
    secret = _enroll_totp(ctx, ctx.token_a)
    a_token = _mint_token(ctx, ctx.token_a, secret)

    r = ctx.client.delete(
        f"/api/v1/auth/devices/{ctx.b_device_id}",
        headers={**_auth(ctx.token_a), "X-Step-Up-Token": a_token},
    )
    assert r.status_code == 404, r.text
    assert r.json()["error"]["code"] == "NOT_FOUND"
    # B's device is untouched despite A holding a valid assertion.
    assert _device_status(ctx, ctx.b_device_id) is DeviceStatus.ACTIVE


# --- small DB helpers --------------------------------------------------------


def _own_device(ctx: SimpleNamespace, member_id: str) -> str:
    session = ctx.session_factory()
    try:
        device_id = _seed_device(session, member_id)
        session.commit()
        return device_id
    finally:
        session.close()


def _device_status(ctx: SimpleNamespace, device_id: str) -> DeviceStatus:
    session = ctx.session_factory()
    try:
        row = session.execute(
            select(DeviceBinding).where(DeviceBinding.id == uuid.UUID(device_id))
        ).scalar_one()
        return row.status
    finally:
        session.close()
