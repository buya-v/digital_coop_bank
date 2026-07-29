"""Identity-domain repositories (E-2 KycSubmission, E-3 DeviceBinding, E-4
ConsentRecord).

A KycSubmission carries a NOT-NULL `member_id` FK, so it is created only AT
PROMOTION — when a Member finally exists (DEC-4). The in-flight KYC handle
(`kyc_inquiry_id` / `kyc_status`) lives on the onboarding draft until then. This
layer only inserts the resolved submission; the promotion rules live in the KYC
service.

`ConsentRepository` and `DeviceBindingRepository` back the EP-1 member
self-service endpoints (listMyConsents / upsertMyConsent / listDevices). Both are
STRICTLY member-scoped: every read and write is filtered by the authenticated
member's UUID, which is supplied by the router from `get_current_member` and NEVER
from a path or body. That is the structural IDOR guard — a repository here cannot
be asked for another member's rows because the only entry points take the owning
`member_id` as a required argument. Reads use keyset (cursor) pagination on
`(recorded_at|bound_at, id)`, expressed in a SQLite/Postgres-portable form (no
row-value tuple comparison). Like every repository these FLUSH, never commit — the
router owns the transaction boundary.
"""
from __future__ import annotations

import datetime
import uuid
from typing import Any, cast

from sqlalchemy import CursorResult, and_, or_, select, update

from app.models.identity import (
    ConsentAction,
    ConsentRecord,
    ConsentType,
    DeviceBinding,
    DeviceStatus,
    KycDocumentType,
    KycResult,
    KycScreeningResult,
    KycSubmission,
    MfaFactor,
    MfaFactorStatus,
    MfaFactorType,
    StepUpToken,
)
from app.repositories.base import BaseRepository


class KycSubmissionRepository(BaseRepository[KycSubmission]):
    model = KycSubmission

    def create(
        self,
        *,
        member_id: uuid.UUID,
        kyc_inquiry_id: str,
        document_type: KycDocumentType,
        ocr_extracted_fields: dict[str, object],
        screening_result: KycScreeningResult,
        result: KycResult,
        result_reasons: dict[str, object],
        evidence_refs: dict[str, object],
        submitted_at: datetime.datetime,
        resolved_at: datetime.datetime,
    ) -> KycSubmission:
        """Insert the resolved KYC submission and flush so its UUID PK populates."""
        submission = KycSubmission(
            member_id=member_id,
            kyc_inquiry_id=kyc_inquiry_id,
            document_type=document_type,
            ocr_extracted_fields=ocr_extracted_fields,
            screening_result=screening_result,
            result=result,
            result_reasons=result_reasons,
            evidence_refs=evidence_refs,
            submitted_at=submitted_at,
            resolved_at=resolved_at,
        )
        self.add(submission)
        self.flush()
        return submission


class ConsentRepository(BaseRepository[ConsentRecord]):
    """Append-only E-4 ConsentRecord access, scoped to one member (US-1.5).

    A ConsentRecord is an immutable audit row: a grant or a withdrawal appends a
    NEW row (there is no update/delete), so the member's consent history is the
    ordered list of these rows and the "current" state of a consent is simply its
    most recent row. Every method requires the owning `member_id`.
    """

    model = ConsentRecord

    def list_for_member(
        self,
        member_id: uuid.UUID,
        *,
        limit: int,
        after_recorded_at: datetime.datetime | None = None,
        after_id: uuid.UUID | None = None,
    ) -> list[ConsentRecord]:
        """Return one keyset page of the member's consent history (oldest first).

        Ordered by `(recorded_at, id)` ascending — chronological append order,
        with `id` breaking ties so the ordering (and thus the cursor) is total and
        stable. `after_*` continue after the previous page's last row; the OR/AND
        form is used instead of a row-value tuple comparison so the same query
        runs on SQLite (tests) and Postgres alike.
        """
        stmt = select(ConsentRecord).where(ConsentRecord.member_id == member_id)
        if after_recorded_at is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    ConsentRecord.recorded_at > after_recorded_at,
                    and_(
                        ConsentRecord.recorded_at == after_recorded_at,
                        ConsentRecord.id > after_id,
                    ),
                )
            )
        stmt = stmt.order_by(ConsentRecord.recorded_at, ConsentRecord.id).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def latest_for_type(
        self, member_id: uuid.UUID, consent_type: ConsentType
    ) -> ConsentRecord | None:
        """Return the member's most recent row for one consent type, or None.

        The current state of a consent (GRANTED vs WITHDRAWN) is its newest row.
        Used to reason about a withdrawal without mutating history.
        """
        stmt = (
            select(ConsentRecord)
            .where(
                ConsentRecord.member_id == member_id,
                ConsentRecord.consent_type == consent_type,
            )
            .order_by(ConsentRecord.recorded_at.desc(), ConsentRecord.id.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalars().first()

    def append(
        self,
        *,
        member_id: uuid.UUID,
        consent_type: ConsentType,
        action: ConsentAction,
        version: str,
        channel: str,
        recorded_at: datetime.datetime,
    ) -> ConsentRecord:
        """Append a new immutable consent row and flush so its UUID PK populates."""
        record = ConsentRecord(
            member_id=member_id,
            consent_type=consent_type,
            action=action,
            version=version,
            channel=channel,
            recorded_at=recorded_at,
        )
        self.add(record)
        self.flush()
        return record


class MfaFactorRepository(BaseRepository[MfaFactor]):
    """E-identity `mfa_factor` access, scoped to one member (US-1.4).

    STRICTLY member-scoped: `member_id` is a required argument on every entry
    point and comes from `get_current_member`, never from a path or body — the
    IDOR class is excluded by construction, matching the consent/device repos.
    The secret is ALWAYS handed in already-encrypted (the service owns the
    plaintext boundary); this layer never sees or logs a plaintext secret. Flush,
    never commit — the router owns the transaction.
    """

    model = MfaFactor

    def get_for_member_and_type(
        self, member_id: uuid.UUID, factor_type: MfaFactorType
    ) -> MfaFactor | None:
        """Return the member's factor of this type, or None (uniqueness is per-type)."""
        stmt = select(MfaFactor).where(
            MfaFactor.member_id == member_id,
            MfaFactor.factor_type == factor_type,
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_pending(
        self,
        *,
        member_id: uuid.UUID,
        factor_type: MfaFactorType,
        secret_ciphertext: str | None,
    ) -> MfaFactor:
        """Insert a new PENDING factor and flush so its UUID PK populates.

        `secret_ciphertext` is the already-encrypted TOTP seed (NULL for SMS).
        """
        factor = MfaFactor(
            member_id=member_id,
            factor_type=factor_type,
            status=MfaFactorStatus.PENDING,
            secret_ciphertext=secret_ciphertext,
            confirmed_at=None,
        )
        self.add(factor)
        self.flush()
        return factor


class StepUpTokenRepository(BaseRepository[StepUpToken]):
    """`step_up_token` access — the issued single-use step-up credential (US-1.4).

    STORES ONLY HASHES: `create` takes an already-computed `token_hash` (the
    service owns the plaintext boundary) and `get_by_hash` looks a presented token
    up by its hash — this layer never sees, stores, or logs a plaintext token.
    `consume` is the ATOMIC single-use guard: a conditional UPDATE that spends the
    token only if it is still unconsumed, so a concurrent replay cannot double-spend
    it. Flush, never commit — the router/dependency owns the transaction.
    """

    model = StepUpToken

    def create(
        self,
        *,
        member_id: uuid.UUID,
        token_hash: str,
        requested_action: str | None,
        expires_at: datetime.datetime,
    ) -> StepUpToken:
        """Insert a new (unconsumed) step-up token and flush so its PK populates.

        `token_hash` is the SHA-256 of the opaque token; the plaintext is NEVER
        handed to this layer.
        """
        token = StepUpToken(
            member_id=member_id,
            token_hash=token_hash,
            requested_action=requested_action,
            expires_at=expires_at,
            consumed_at=None,
        )
        self.add(token)
        self.flush()
        return token

    def get_by_hash(self, token_hash: str) -> StepUpToken | None:
        """Return the token row for a presented token's hash, or None."""
        stmt = select(StepUpToken).where(StepUpToken.token_hash == token_hash)
        return self.session.execute(stmt).scalar_one_or_none()

    def consume(
        self, token_id: uuid.UUID, member_id: uuid.UUID, *, now: datetime.datetime
    ) -> bool:
        """Atomically spend the token; return True iff THIS call consumed it.

        The UPDATE fires only while the row is unconsumed, unexpired, AND owned by
        `member_id` — so consumption, single-use, expiry and member-binding are all
        enforced in one guarded statement. A replay (or a cross-member presentation)
        matches zero rows and returns False. The caller must still validate up front
        to choose the right error code; this is the race-safe final gate.
        """
        stmt = (
            update(StepUpToken)
            .where(
                StepUpToken.id == token_id,
                StepUpToken.member_id == member_id,
                StepUpToken.consumed_at.is_(None),
                StepUpToken.expires_at > now,
            )
            .values(consumed_at=now)
        )
        # `execute` is typed as `Result`; a Core UPDATE returns a `CursorResult`,
        # which is where `rowcount` lives.
        result = cast("CursorResult[Any]", self.session.execute(stmt))
        return bool(result.rowcount == 1)


class DeviceBindingRepository(BaseRepository[DeviceBinding]):
    """E-3 DeviceBinding access, scoped to one member (US-1.4).

    `list_for_member` returns the member's TRUSTED devices — i.e. ACTIVE bindings.
    A REVOKED binding is no longer trusted and is excluded (the Device response
    schema carries no status, so a revoked row has no meaningful representation
    here). Revocation itself is a step-up-gated operation deferred to a later
    slice; this repository only reads.
    """

    model = DeviceBinding

    def list_for_member(
        self,
        member_id: uuid.UUID,
        *,
        limit: int,
        after_bound_at: datetime.datetime | None = None,
        after_id: uuid.UUID | None = None,
    ) -> list[DeviceBinding]:
        """Return one keyset page of the member's ACTIVE devices (oldest first).

        Ordered by `(bound_at, id)` ascending; `id` breaks ties so the cursor is
        total and stable. Portable keyset form (no row-value tuple comparison).
        """
        stmt = select(DeviceBinding).where(
            DeviceBinding.member_id == member_id,
            DeviceBinding.status == DeviceStatus.ACTIVE,
        )
        if after_bound_at is not None and after_id is not None:
            stmt = stmt.where(
                or_(
                    DeviceBinding.bound_at > after_bound_at,
                    and_(
                        DeviceBinding.bound_at == after_bound_at,
                        DeviceBinding.id > after_id,
                    ),
                )
            )
        stmt = stmt.order_by(DeviceBinding.bound_at, DeviceBinding.id).limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def get_owned(
        self, member_id: uuid.UUID, device_id: uuid.UUID
    ) -> DeviceBinding | None:
        """Return the member's OWN device by id (any status), or None.

        The lookup is scoped by BOTH `member_id` AND `id`, so another member's
        device id resolves to None here — the router renders that as a 404 and the
        IDOR class is excluded by construction (never a cross-member reveal). Not
        filtered by status, so an already-revoked device is found (idempotent
        revoke), never leaked as a spurious 404.
        """
        stmt = select(DeviceBinding).where(
            DeviceBinding.member_id == member_id,
            DeviceBinding.id == device_id,
        )
        return self.session.execute(stmt).scalar_one_or_none()
