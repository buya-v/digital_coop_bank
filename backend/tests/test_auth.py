"""Member-auth foundation tests (`get_current_member` + the RS256 verifier).

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral
in-memory RSA keypair) MINTS tokens, an in-memory SQLite engine holds a seeded
`Member`, and a tiny probe app mounts `get_current_member` on `GET /probe/me`.
`app.api.deps.get_session` and `app.auth.deps.get_token_verifier` are overridden
so the verifier is bound to the dev signer's PUBLIC key.

The attack tests are deliberately NON-VACUOUS: each asserts (or the shared valid
test establishes) that the very same token shape is admitted under a permissive
verifier, so a regression that weakened verification would turn the 401 into a
200 and fail the test.

Attacks covered: alg:none, HS256 algorithm/key-confusion (forged with the RSA
public key as the HMAC secret), expiry, bad signature (wrong key), unknown
subject, and missing/malformed Authorization header. Plus iss/aud enforcement
when configured.
"""
from __future__ import annotations

import base64
import datetime
import hashlib
import hmac
import json
import uuid
from collections.abc import Iterator
from types import SimpleNamespace

import pytest

pytest.importorskip("fastapi", reason="fastapi not installed on this machine; CI runs it")
pytest.importorskip("jwt", reason="PyJWT not installed on this machine; CI runs it")

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_session
from app.api.errors import register_error_handlers
from app.auth.deps import get_current_member, get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.models.membership import Member, MembershipStatus

ISSUER = "https://idp.example.invalid/"
AUDIENCE = "dcb-members"

# One ephemeral DEV/TEST keypair for the whole module (the IdP stand-in).
SIGNER = DevRsaSigner()


def _future(seconds: int = 900) -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(  # noqa: UP017
        seconds=seconds
    )


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _b64(b: bytes) -> bytes:
    return base64.urlsafe_b64encode(b).rstrip(b"=")


def _forge_hs256(payload: dict[str, object], secret: bytes) -> str:
    """Hand-forge an HS256 JWT (PyJWT's own encoder refuses an asymmetric key as
    an HMAC secret, so the classic confusion token must be built by hand)."""
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = (
        _b64(json.dumps(header, separators=(",", ":")).encode())
        + b"."
        + _b64(json.dumps(payload, separators=(",", ":")).encode())
    )
    sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
    return (signing_input + b"." + _b64(sig)).decode()


def _build_probe_app() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/probe/me")
    def _me(member: Member = Depends(get_current_member)) -> dict[str, str]:
        # Prove the dep returns the DB Member (only `sub` -> DB is trusted).
        return {"id": str(member.id), "ner": member.ner}

    return app


@pytest.fixture()
def ctx() -> Iterator[SimpleNamespace]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Member.__table__.create(engine)
    test_session = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)

    seed = test_session()
    member = Member(
        ovog="Бат",
        etsgiin_ner="Болд",
        ner="Түвшин",
        mrz_name_latin=None,
        registration_number="УБ12345678",
        membership_status=MembershipStatus.ACTIVE,
    )
    seed.add(member)
    seed.commit()
    member_id = str(member.id)
    seed.close()

    app = _build_probe_app()

    def _override_session() -> Iterator[Session]:
        session = test_session()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_session] = _override_session
    # Default: verify against the dev signer's public key, no iss/aud enforced.
    app.dependency_overrides[get_token_verifier] = lambda: SIGNER.verifier()

    try:
        yield SimpleNamespace(
            client=TestClient(app),
            app=app,
            member_id=member_id,
        )
    finally:
        app.dependency_overrides.clear()
        Member.__table__.drop(engine)
        engine.dispose()


# --- happy path --------------------------------------------------------------


def test_valid_token_resolves_to_member(ctx: SimpleNamespace) -> None:
    token = SIGNER.mint(subject=ctx.member_id, expires_in_seconds=900)
    r = ctx.client.get("/probe/me", headers=_auth(token))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == ctx.member_id
    assert body["ner"] == "Түвшин"


# --- attacks (each non-vacuous) ---------------------------------------------


def test_expired_token_is_401(ctx: SimpleNamespace) -> None:
    token = SIGNER.mint(subject=ctx.member_id, expires_in_seconds=-10)
    # Non-vacuous: the signature is valid and the subject is a real member — only
    # `exp` fails. A verifier that skipped expiry would admit this member.
    permissive = jwt.decode(
        token,
        key=SIGNER.public_key_pem,
        algorithms=["RS256"],
        options={"verify_exp": False},
    )
    assert permissive["sub"] == ctx.member_id
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_bad_signature_is_401(ctx: SimpleNamespace) -> None:
    # Signed by a DIFFERENT keypair than the verifier trusts.
    other = DevRsaSigner()
    token = other.mint(subject=ctx.member_id, expires_in_seconds=900)
    # Non-vacuous: payload is well-formed and names a real member; only the
    # signature is wrong. A verifier that skipped signature checks would admit.
    permissive = jwt.decode(token, options={"verify_signature": False})
    assert permissive["sub"] == ctx.member_id
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_alg_none_is_401(ctx: SimpleNamespace) -> None:
    token = jwt.encode(
        {"sub": ctx.member_id, "exp": int(_future().timestamp())},
        key=None,
        algorithm="none",
    )
    # Non-vacuous: an unsigned token naming a real member. A verifier that
    # allowed "none" would admit it.
    permissive = jwt.decode(token, options={"verify_signature": False})
    assert permissive["sub"] == ctx.member_id
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_hs256_algorithm_confusion_is_401(ctx: SimpleNamespace) -> None:
    # The classic key-confusion forgery: sign HS256 using the RSA PUBLIC key
    # (which the attacker can read) as the HMAC secret.
    payload = {"sub": ctx.member_id, "exp": int(_future().timestamp())}
    secret = SIGNER.public_key_pem.encode()
    token = _forge_hs256(payload, secret)
    # Non-vacuous: the forged HMAC genuinely validates against the public key as
    # the secret, so a verifier that let the header pick HS256 + the public key
    # would admit this real member.
    signing_input, _, sig = token.rpartition(".")
    expected = _b64(hmac.new(secret, signing_input.encode(), hashlib.sha256).digest()).decode()
    assert sig == expected
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_unknown_subject_is_rejected(ctx: SimpleNamespace) -> None:
    # A perfectly valid, correctly-signed, unexpired token — but `sub` is not a
    # known member. Non-vacuous: only the DB lookup rejects it.
    token = SIGNER.mint(subject=str(uuid.uuid4()), expires_in_seconds=900)
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code in (401, 403)


def test_malformed_subject_is_rejected(ctx: SimpleNamespace) -> None:
    # A validly-signed token whose `sub` is not even a UUID.
    token = SIGNER.mint(subject="not-a-uuid", expires_in_seconds=900)
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code in (401, 403)


def test_missing_authorization_header_is_401(ctx: SimpleNamespace) -> None:
    assert ctx.client.get("/probe/me").status_code == 401


def test_malformed_authorization_header_is_401(ctx: SimpleNamespace) -> None:
    # Right token, wrong scheme.
    token = SIGNER.mint(subject=ctx.member_id, expires_in_seconds=900)
    assert ctx.client.get("/probe/me", headers={"Authorization": f"Token {token}"}).status_code == 401


# --- iss / aud enforced only when configured --------------------------------


def _use_strict_verifier(ctx: SimpleNamespace) -> None:
    ctx.app.dependency_overrides[get_token_verifier] = lambda: SIGNER.verifier(
        issuer=ISSUER, audience=AUDIENCE
    )


def test_correct_issuer_and_audience_is_200(ctx: SimpleNamespace) -> None:
    _use_strict_verifier(ctx)
    token = SIGNER.mint(
        subject=ctx.member_id, issuer=ISSUER, audience=AUDIENCE, expires_in_seconds=900
    )
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 200


def test_wrong_issuer_is_401(ctx: SimpleNamespace) -> None:
    _use_strict_verifier(ctx)
    token = SIGNER.mint(
        subject=ctx.member_id,
        issuer="https://evil.example.invalid/",
        audience=AUDIENCE,
        expires_in_seconds=900,
    )
    # Non-vacuous: the same token verifies fine against a non-strict verifier.
    assert SIGNER.verifier().verify(token)["sub"] == ctx.member_id
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_wrong_audience_is_401(ctx: SimpleNamespace) -> None:
    _use_strict_verifier(ctx)
    token = SIGNER.mint(
        subject=ctx.member_id,
        issuer=ISSUER,
        audience="some-other-service",
        expires_in_seconds=900,
    )
    assert SIGNER.verifier().verify(token)["sub"] == ctx.member_id
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401


def test_not_yet_valid_nbf_is_401(ctx: SimpleNamespace) -> None:
    token = SIGNER.mint(
        subject=ctx.member_id,
        expires_in_seconds=900,
        not_before=_future(300),  # nbf 5 min in the future
    )
    assert ctx.client.get("/probe/me", headers=_auth(token)).status_code == 401
