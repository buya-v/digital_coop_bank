"""Member self-service profile tests — getMyProfile / updateMyProfile (T2).

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral
in-memory RSA keypair) MINTS member tokens, an in-memory SQLite engine holds two
seeded `Member` rows (A and B), and the REAL `members` router is mounted.
`app.api.deps.get_session` and `app.auth.deps.get_token_verifier` are overridden
so the verifier trusts the dev signer's public key.

Covered:
- GET returns the profile including the DERIVED `legal_name` (ovog+patronymic+given).
- PATCH an editable field (city) persists and is reflected on a later GET.
- PATCH a read-only/derived/system-owned field -> 422 (legal_name, mrz_name_latin,
  registration_number, member_id).
- No / malformed token -> 401.
- IDOR: a token for member A reads/patches ONLY A; it can never reach B (the
  identity comes from the token subject, never from the path or body).
"""
from __future__ import annotations

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
from app.api.routers.members import router as members_router
from app.auth.deps import get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.models.membership import Member, MembershipStatus

# One ephemeral DEV/TEST keypair for the whole module (the IdP stand-in).
SIGNER = DevRsaSigner()


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _seed_member(session: Session, **overrides: object) -> Member:
    fields: dict[str, object] = {
        "member_id": "DCB-AAAA1111",
        "ovog": "Бат",
        "etsgiin_ner": "Болд",
        "ner": "Түвшин",
        "mrz_name_latin": "BOLD TUVSHIN",
        "registration_number": "УБ12345678",
        "membership_status": MembershipStatus.PENDING_PAYMENT,
        "email": "a@example.mn",
        "phone_number": "+97688110001",
        "city": "Улаанбаатар",
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
        city="Ховд",
    )
    seed.commit()
    a_id, b_id = str(member_a.id), str(member_b.id)
    seed.close()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(members_router)

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
        Member.__table__.drop(engine)
        engine.dispose()


# --- getMyProfile ------------------------------------------------------------


def test_get_profile_returns_derived_legal_name(ctx: SimpleNamespace) -> None:
    r = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_a))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == ctx.a_id
    assert body["member_id"] == "DCB-AAAA1111"
    assert body["ner"] == "Түвшин"
    # legal_name is DERIVED from ovog / etsgiin_ner / ner — never a stored column.
    assert body["legal_name"] == "Бат Болд Түвшин"
    assert body["membership_status"] == "PENDING_PAYMENT"


def test_get_profile_no_token_is_401(ctx: SimpleNamespace) -> None:
    assert ctx.client.get("/api/v1/members/me").status_code == 401


def test_get_profile_malformed_scheme_is_401(ctx: SimpleNamespace) -> None:
    r = ctx.client.get(
        "/api/v1/members/me", headers={"Authorization": f"Token {ctx.token_a}"}
    )
    assert r.status_code == 401


# --- updateMyProfile: editable field -----------------------------------------


def test_patch_editable_field_persists_and_reflects_on_get(ctx: SimpleNamespace) -> None:
    r = ctx.client.patch(
        "/api/v1/members/me/profile",
        headers=_auth(ctx.token_a),
        json={"city": "Дархан", "address_line_1": "5-р байр"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["profile"]["city"] == "Дархан"
    assert body["profile"]["address_line_1"] == "5-р байр"
    assert body["reverification_required"] is True

    # A fresh GET (new request-scoped session) reflects the committed change.
    again = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_a))
    assert again.json()["city"] == "Дархан"


def test_patch_no_token_is_401(ctx: SimpleNamespace) -> None:
    r = ctx.client.patch("/api/v1/members/me/profile", json={"city": "Дархан"})
    assert r.status_code == 401


# --- updateMyProfile: read-only / derived / system-owned -> 422 --------------


@pytest.mark.parametrize(
    ("field", "value", "code"),
    [
        ("legal_name", "Forged Name", "LEGAL_NAME_NOT_EDITABLE"),
        ("mrz_name_latin", "FORGED LATIN", "MRZ_NAME_NOT_EDITABLE"),
        ("registration_number", "УБ99999999", "REGISTRATION_NUMBER_NOT_EDITABLE"),
        ("member_id", "DCB-ZZZZ9999", "MEMBER_ID_NOT_EDITABLE"),
    ],
)
def test_patch_read_only_field_is_422(
    ctx: SimpleNamespace, field: str, value: str, code: str
) -> None:
    r = ctx.client.patch(
        "/api/v1/members/me/profile",
        headers=_auth(ctx.token_a),
        json={field: value},
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == code

    # And the read-only value was NOT mutated.
    current = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_a)).json()
    assert current.get(field) != value


# --- IDOR: the token subject is the ONLY identity ----------------------------


def test_token_resolves_to_own_profile_only(ctx: SimpleNamespace) -> None:
    a = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_a)).json()
    b = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_b)).json()
    assert a["id"] == ctx.a_id and a["member_id"] == "DCB-AAAA1111"
    assert b["id"] == ctx.b_id and b["member_id"] == "DCB-BBBB2222"
    assert a["id"] != b["id"]


def test_patch_with_a_token_never_touches_b(ctx: SimpleNamespace) -> None:
    # There is no member id in the path or body, so A's token can only ever write
    # A. Patching via A's token leaves B's row completely unchanged.
    r = ctx.client.patch(
        "/api/v1/members/me/profile",
        headers=_auth(ctx.token_a),
        json={"city": "Эрдэнэт", "email": "changed@example.mn"},
    )
    assert r.status_code == 200, r.text

    b = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_b)).json()
    assert b["city"] == "Ховд"
    assert b["email"] == "b@example.mn"
    # And A did change.
    a = ctx.client.get("/api/v1/members/me", headers=_auth(ctx.token_a)).json()
    assert a["city"] == "Эрдэнэт"
