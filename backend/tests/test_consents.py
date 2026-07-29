"""Member consent self-service tests — listMyConsents / upsertMyConsent (T1).

No real database and no real IdP: a `DevRsaSigner` (DEV/TEST-ONLY, ephemeral
in-memory RSA keypair) MINTS member tokens, an in-memory SQLite engine holds two
seeded members (A and B) each with their OWN consent history, and the REAL
consents router is mounted. `app.api.deps.get_session` and
`app.auth.deps.get_token_verifier` are overridden so the verifier trusts the dev
signer's public key.

Covered:
- GET returns ONLY the caller's append-only consent history (ordered).
- PUT appends a record for the caller and it is reflected on a later GET.
- PUT append is additive (append-only): a prior record is never mutated/removed.
- PUT withdrawing a service-required consent -> 409 CONSENT_REQUIRED_FOR_SERVICE.
- PUT withdrawing an optional consent (MARKETING) -> 200.
- Unknown consent_type / action -> 422.
- No / malformed token -> 401.
- IDOR (NON-VACUOUS): B is seeded with distinct consents; A's token never returns
  or affects B's consents, and B's rows are byte-for-byte untouched after A writes.
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
from app.api.routers.consents import router as consents_router
from app.auth.deps import get_token_verifier
from app.auth.dev_signer import DevRsaSigner
from app.models.identity import ConsentAction, ConsentRecord, ConsentType
from app.models.membership import Member, MembershipStatus

SIGNER = DevRsaSigner()

# A fixed base instant so seeded `recorded_at` values are deterministic/ordered.
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


def _seed_consent(
    session: Session,
    member: Member,
    *,
    consent_type: ConsentType,
    action: ConsentAction,
    version: str,
    channel: str,
    offset_minutes: int,
) -> ConsentRecord:
    record = ConsentRecord(
        member_id=member.id,
        consent_type=consent_type,
        action=action,
        version=version,
        channel=channel,
        recorded_at=BASE + datetime.timedelta(minutes=offset_minutes),
    )
    session.add(record)
    session.flush()
    return record


@pytest.fixture()
def ctx() -> Iterator[SimpleNamespace]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Member.__table__.create(engine)
    ConsentRecord.__table__.create(engine)
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
    # A: two records.
    _seed_consent(
        seed,
        member_a,
        consent_type=ConsentType.TERMS_AND_BYLAWS,
        action=ConsentAction.GRANTED,
        version="v1",
        channel="MOBILE_APP",
        offset_minutes=1,
    )
    _seed_consent(
        seed,
        member_a,
        consent_type=ConsentType.MARKETING,
        action=ConsentAction.GRANTED,
        version="v1",
        channel="MOBILE_APP",
        offset_minutes=2,
    )
    # B: one DISTINCT record (so IDOR assertions are non-vacuous).
    _seed_consent(
        seed,
        member_b,
        consent_type=ConsentType.PRIVACY_POLICY,
        action=ConsentAction.GRANTED,
        version="vB",
        channel="WEB",
        offset_minutes=1,
    )
    seed.commit()
    a_id, b_id = str(member_a.id), str(member_b.id)
    seed.close()

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(consents_router)

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
        ConsentRecord.__table__.drop(engine)
        Member.__table__.drop(engine)
        engine.dispose()


# --- listMyConsents ----------------------------------------------------------


def test_list_returns_only_callers_history(ctx: SimpleNamespace) -> None:
    r = ctx.client.get("/api/v1/members/me/consents", headers=_auth(ctx.token_a))
    assert r.status_code == 200, r.text
    records = r.json()["consent_records"]
    assert [x["consent_type"] for x in records] == ["TERMS_AND_BYLAWS", "MARKETING"]
    # None of B's records (PRIVACY_POLICY / version vB) leak into A's history.
    assert all(x["version"] != "vB" for x in records)


def test_list_no_token_is_401(ctx: SimpleNamespace) -> None:
    assert ctx.client.get("/api/v1/members/me/consents").status_code == 401


def test_list_malformed_scheme_is_401(ctx: SimpleNamespace) -> None:
    r = ctx.client.get(
        "/api/v1/members/me/consents",
        headers={"Authorization": f"Token {ctx.token_a}"},
    )
    assert r.status_code == 401


# --- upsertMyConsent ---------------------------------------------------------


def test_upsert_appends_and_reflects_on_list(ctx: SimpleNamespace) -> None:
    r = ctx.client.put(
        "/api/v1/members/me/consents/DATA_SHARING_OPEN_BANKING",
        headers=_auth(ctx.token_a),
        json={"action": "GRANTED", "version": "2026.1"},
    )
    assert r.status_code == 200, r.text
    types_after = [x["consent_type"] for x in r.json()["consent_records"]]
    assert "DATA_SHARING_OPEN_BANKING" in types_after
    # A default channel is stamped when the request omits one.
    new = next(
        x
        for x in r.json()["consent_records"]
        if x["consent_type"] == "DATA_SHARING_OPEN_BANKING"
    )
    assert new["action"] == "GRANTED"
    assert new["channel"] == "MOBILE_APP"

    # A fresh GET (new request-scoped session) reflects the committed append.
    again = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_a)
    ).json()
    assert len(again["consent_records"]) == 3


def test_upsert_is_append_only_not_mutation(ctx: SimpleNamespace) -> None:
    # Withdraw MARKETING (optional) — the earlier GRANTED row must remain.
    r = ctx.client.put(
        "/api/v1/members/me/consents/MARKETING",
        headers=_auth(ctx.token_a),
        json={"action": "WITHDRAWN", "version": "v1"},
    )
    assert r.status_code == 200, r.text
    marketing = [
        x
        for x in r.json()["consent_records"]
        if x["consent_type"] == "MARKETING"
    ]
    # Both the original GRANTED and the new WITHDRAWN survive (append-only).
    assert {x["action"] for x in marketing} == {"GRANTED", "WITHDRAWN"}
    assert len(marketing) == 2


def test_withdraw_service_required_consent_is_409(ctx: SimpleNamespace) -> None:
    r = ctx.client.put(
        "/api/v1/members/me/consents/TERMS_AND_BYLAWS",
        headers=_auth(ctx.token_a),
        json={"action": "WITHDRAWN", "version": "v1"},
    )
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"] == "CONSENT_REQUIRED_FOR_SERVICE"
    # And nothing was appended.
    hist = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_a)
    ).json()
    assert len(hist["consent_records"]) == 2


def test_unknown_consent_type_is_422(ctx: SimpleNamespace) -> None:
    r = ctx.client.put(
        "/api/v1/members/me/consents/NOT_A_REAL_TYPE",
        headers=_auth(ctx.token_a),
        json={"action": "GRANTED", "version": "v1"},
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_unknown_action_is_422(ctx: SimpleNamespace) -> None:
    r = ctx.client.put(
        "/api/v1/members/me/consents/MARKETING",
        headers=_auth(ctx.token_a),
        json={"action": "MAYBE", "version": "v1"},
    )
    assert r.status_code == 422, r.text
    assert r.json()["error"]["code"] == "VALIDATION_FAILED"


def test_upsert_no_token_is_401(ctx: SimpleNamespace) -> None:
    r = ctx.client.put(
        "/api/v1/members/me/consents/MARKETING",
        json={"action": "GRANTED", "version": "v1"},
    )
    assert r.status_code == 401


# --- IDOR: the token subject is the ONLY identity ----------------------------


def test_list_is_scoped_per_member(ctx: SimpleNamespace) -> None:
    a = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_a)
    ).json()["consent_records"]
    b = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_b)
    ).json()["consent_records"]
    # B sees only their own single distinct record; A sees only their two.
    assert [x["consent_type"] for x in b] == ["PRIVACY_POLICY"]
    assert b[0]["version"] == "vB"
    assert len(a) == 2
    assert all(x["version"] != "vB" for x in a)


def test_a_upsert_never_touches_b(ctx: SimpleNamespace) -> None:
    # There is no member id in path or body: A's token can only append to A.
    before = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_b)
    ).json()["consent_records"]

    r = ctx.client.put(
        "/api/v1/members/me/consents/PRIVACY_POLICY",
        headers=_auth(ctx.token_a),
        json={"action": "WITHDRAWN", "version": "hostile"},
    )
    # A withdrawing THEIR privacy consent is A's business; it 409s (required),
    # but even a successful A write could never reach B. Assert B is untouched.
    assert r.status_code in (200, 409)

    after = ctx.client.get(
        "/api/v1/members/me/consents", headers=_auth(ctx.token_b)
    ).json()["consent_records"]
    assert after == before
    assert len(after) == 1
    assert after[0]["version"] == "vB"
