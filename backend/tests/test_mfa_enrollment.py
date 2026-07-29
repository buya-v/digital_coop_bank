"""MFA enrollment tests — createMfaEnrollment (T1).

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral RSA
keypair) mints member tokens, an in-memory SQLite engine holds two seeded members
(A and B), the REAL mfa router is mounted, and `get_session` /
`get_token_verifier` / `get_secret_cipher` / `get_sms_sender` are overridden.

Each test names the SECURITY property it proves:

- TOTP enroll returns a binding challenge (otpauth URI) AND the stored secret
  column holds CIPHERTEXT != the plaintext seed (secret-at-rest).
- The ciphertext decrypts (with the same key) back to the seed embedded in the
  challenge — so it is genuinely the encrypted seed, not an unrelated blob
  (non-vacuous).
- A duplicate of an already-ACTIVE factor is refused 409 (no silent overwrite of a
  confirmed factor).
- SMS enroll drives the mock sender (the code goes out-of-band) and the raw code is
  NOT echoed in the response (out-of-band property).
- BIOMETRIC / unknown factor types are refused 422 (only server-verifiable factors
  persist).
- No token -> 401 (auth required).
- A freshly enrolled factor is PENDING and owned by the caller (binding + IDOR).
"""
from __future__ import annotations

import datetime
import urllib.parse
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")
pytest.importorskip("jwt", reason="PyJWT not installed on this machine; CI runs it")
pytest.importorskip("pyotp", reason="pyotp not installed on this machine; CI runs it")

from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.adapters.sms.mock import MockSmsSender
from app.api.deps import get_session
from app.api.errors import register_error_handlers
from app.api.routers.mfa import get_sms_sender
from app.api.routers.mfa import router as mfa_router
from app.auth.deps import get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.auth.mfa import SecretCipher, get_secret_cipher, verify_totp
from app.models.identity import MfaFactor, MfaFactorStatus, MfaFactorType
from app.models.membership import Member, MembershipStatus

SIGNER = DevRsaSigner()
# A test-only Fernet key + cipher. Never a committed production key — generated
# per test session in-memory; the SAME cipher is injected into the app and used by
# the test to decrypt what the app stored.
TEST_CIPHER = SecretCipher(Fernet.generate_key().decode("ascii"))


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _secret_from_otpauth(uri: str) -> str:
    """Extract the base32 `secret` query param from an otpauth:// provisioning URI."""
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


@pytest.fixture()
def ctx() -> Iterator[SimpleNamespace]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Member.__table__.create(engine)
    MfaFactor.__table__.create(engine)
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
    seed.close()

    sms = MockSmsSender()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(mfa_router)

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
            sms=sms,
            a_id=a_id,
            b_id=b_id,
            token_a=SIGNER.mint(subject=a_id),
            token_b=SIGNER.mint(subject=b_id),
        )
    finally:
        app.dependency_overrides.clear()
        MfaFactor.__table__.drop(engine)
        Member.__table__.drop(engine)
        engine.dispose()


def _factor(ctx: SimpleNamespace, member_id: str, ftype: MfaFactorType) -> MfaFactor:
    session = ctx.session_factory()
    try:
        import uuid

        row = session.execute(
            select(MfaFactor).where(
                MfaFactor.member_id == uuid.UUID(member_id),
                MfaFactor.factor_type == ftype,
            )
        ).scalar_one()
        return row
    finally:
        session.close()


# --- TOTP: binding challenge + secret encrypted at rest ----------------------


def test_totp_enroll_returns_challenge_and_stores_ciphertext(ctx: SimpleNamespace) -> None:
    """PROVES: enroll returns an otpauth binding challenge, and the stored secret
    column is CIPHERTEXT distinct from the plaintext seed (secret-at-rest)."""
    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["enrollment_id"]
    challenge = body["binding_challenge"]
    assert challenge.startswith("otpauth://totp/")

    plaintext_secret = _secret_from_otpauth(challenge)

    row = _factor(ctx, ctx.a_id, MfaFactorType.TOTP)
    assert row.status is MfaFactorStatus.PENDING  # never auto-confirmed
    stored = row.secret_ciphertext
    assert stored is not None
    # The core assertion: what is stored is NOT the plaintext seed.
    assert stored != plaintext_secret
    assert plaintext_secret not in stored
    # ...and it is genuinely the ENCRYPTED seed (decrypts back) — non-vacuous.
    assert TEST_CIPHER.decrypt(stored) == plaintext_secret
    # The challenge secret is a working TOTP seed.
    import pyotp

    assert verify_totp(plaintext_secret, pyotp.TOTP(plaintext_secret).now())


def test_totp_enroll_owned_by_caller_only(ctx: SimpleNamespace) -> None:
    """PROVES: the enrolled factor is bound to the caller (IDOR — token subject is
    the only identity), created PENDING."""
    ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    import uuid

    row = _factor(ctx, ctx.a_id, MfaFactorType.TOTP)
    assert str(row.member_id) == ctx.a_id
    assert row.member_id != uuid.UUID(ctx.b_id)


# --- Duplicate active factor -> 409 ------------------------------------------


def test_duplicate_active_factor_is_409(ctx: SimpleNamespace) -> None:
    """PROVES: a duplicate of an already-ACTIVE factor is refused (no overwrite of
    a confirmed credential)."""
    import uuid

    seed = ctx.session_factory()
    try:
        seed.add(
            MfaFactor(
                member_id=uuid.UUID(ctx.a_id),
                factor_type=MfaFactorType.TOTP,
                status=MfaFactorStatus.ACTIVE,
                secret_ciphertext=TEST_CIPHER.encrypt("JBSWY3DPEHPK3PXP"),
                confirmed_at=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc),  # noqa: UP017
            )
        )
        seed.commit()
    finally:
        seed.close()

    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "FACTOR_EXISTS"


def test_reenroll_pending_totp_reissues_same_row(ctx: SimpleNamespace) -> None:
    """PROVES: re-enrolling a still-PENDING factor re-issues on the SAME row
    (per-(member,type) uniqueness holds) with a rotated secret."""
    first = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    ).json()
    second = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    ).json()
    assert first["enrollment_id"] == second["enrollment_id"]  # same row
    assert first["binding_challenge"] != second["binding_challenge"]  # rotated seed


# --- SMS: drives the mock sender; code stays out-of-band ---------------------


def test_sms_enroll_drives_mock_sender(ctx: SimpleNamespace) -> None:
    """PROVES: SMS enroll sends a code via the port, and the raw code is NOT echoed
    in the response (out-of-band); no TOTP secret is stored at rest for SMS."""
    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "SMS", "device_fingerprint": "fp-a", "platform": "ANDROID"},
    )
    assert r.status_code == 201, r.text
    # Exactly one code delivered, to the member's phone, 6 digits.
    assert len(ctx.sms.sent) == 1
    sent = ctx.sms.sent[0]
    assert sent.phone_number == "+97688110001"
    assert len(sent.code) == 6 and sent.code.isdigit()
    # The raw code is NOT in the HTTP response (it travels out-of-band only).
    body = r.json()
    assert sent.code not in body["binding_challenge"]
    assert body["binding_challenge"].startswith("SMS_CODE_SENT:")

    row = _factor(ctx, ctx.a_id, MfaFactorType.SMS)
    assert row.status is MfaFactorStatus.PENDING
    assert row.secret_ciphertext is None  # no TOTP seed persisted for SMS


# --- Bad input / auth --------------------------------------------------------


def test_biometric_factor_type_is_422(ctx: SimpleNamespace) -> None:
    """PROVES: an unsupported (BIOMETRIC) factor type is refused 422 — only
    server-verifiable factors persist."""
    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        headers=_auth(ctx.token_a),
        json={"factor_type": "BIOMETRIC", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_enroll_requires_auth(ctx: SimpleNamespace) -> None:
    """PROVES: enrollment requires an authenticated member (401 without a token)."""
    r = ctx.client.post(
        "/api/v1/auth/mfa/enrollments",
        json={"factor_type": "TOTP", "device_fingerprint": "fp-a", "platform": "IOS"},
    )
    assert r.status_code == 401
