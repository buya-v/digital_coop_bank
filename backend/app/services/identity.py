"""Member self-service for consents and devices (EP-1, 04 §3.1).

Operations against the existing OpenAPI contract:

- listMyConsents   GET /members/me/consents               -> ConsentListResponse
- upsertMyConsent  PUT /members/me/consents/{consent_type} -> ConsentListResponse
- listDevices      GET /auth/devices                       -> DeviceListResponse

Every method here takes the ALREADY-AUTHENTICATED member (resolved by
`get_current_member` from the verified token subject) and passes only that
member's UUID to the repositories. No member id is ever read from a path or a
body, so a caller can only ever read or affect THEIR OWN consents and devices —
the IDOR class is excluded by construction, not by a check that could be
forgotten.

Consents are an APPEND-ONLY audit log (E-4): a grant or a withdrawal appends a
new immutable row; nothing is updated or deleted. "Upsert" here means "append the
new state", and the current state of a consent is its most recent row.

Like the slice-1/2 services this NEVER commits — the router owns the transaction
boundary; the service reads/appends and the router commits on a mutation.
"""
from __future__ import annotations

import base64
import binascii
import datetime
import json
import uuid
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.identity import (
    ConsentAction,
    ConsentRecord,
    ConsentType,
    DeviceBinding,
)
from app.repositories.identity import ConsentRepository, DeviceBindingRepository
from app.repositories.membership import utc_now

# Cursor-pagination bounds (root.yaml Cursor/Limit: 1..100, default 20).
DEFAULT_LIMIT = 20
MAX_LIMIT = 100

# Consents whose withdrawal is refused because service cannot be provided without
# them (409 CONSENT_REQUIRED_FOR_SERVICE, 04 §3.1). The mandatory legal/regulatory
# acceptances a member must hold to use the cooperative; the remaining consent
# types (MARKETING, DATA_SHARING_OPEN_BANKING, IMPACT_SPOTLIGHT) are optional and
# may be freely withdrawn. Kept as an explicit set so the policy is auditable and
# a future config source can replace it without touching the flow.
SERVICE_REQUIRED_CONSENTS: frozenset[ConsentType] = frozenset(
    {
        ConsentType.TERMS_AND_BYLAWS,
        ConsentType.PRIVACY_POLICY,
        ConsentType.E_SIGN_DISCLOSURE,
    }
)

# Channel recorded when the request does not carry one. The ConsentUpsertRequest
# contract schema does not include `channel`, but the ConsentRecord audit row
# requires it (E-4, NOT NULL); a mobile-first member app is the default capture
# channel. A caller MAY still supply `channel` explicitly (the request schema does
# not forbid it); an explicit value wins.
DEFAULT_CONSENT_CHANNEL = "MOBILE_APP"


class IdentityServiceError(Exception):
    """Base for consent/device domain errors (mapped to HTTP by the router)."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


class InvalidCursor(IdentityServiceError):
    """A malformed pagination cursor was supplied (maps to 422)."""

    def __init__(self) -> None:
        super().__init__(422, "VALIDATION_FAILED", "Malformed pagination cursor.")


class UnknownConsentType(IdentityServiceError):
    """An unrecognised consent_type path value was supplied (maps to 422)."""

    def __init__(self, value: str) -> None:
        super().__init__(
            422, "VALIDATION_FAILED", f"Unknown consent type '{value}'."
        )


class UnknownConsentAction(IdentityServiceError):
    """An unrecognised consent action was supplied (maps to 422)."""

    def __init__(self, value: str) -> None:
        super().__init__(
            422, "VALIDATION_FAILED", f"Unknown consent action '{value}'."
        )


class ConsentRequiredForService(IdentityServiceError):
    """Withdrawing a service-required consent is refused (maps to 409)."""

    def __init__(self, consent_type: ConsentType) -> None:
        super().__init__(
            409,
            "CONSENT_REQUIRED_FOR_SERVICE",
            f"Consent '{consent_type.value}' is required for service and "
            "cannot be withdrawn.",
        )


@dataclass(frozen=True)
class Page:
    """A keyset page: the rows for this page and the cursor for the next one."""

    records: list[ConsentRecord]
    next_cursor: str | None


@dataclass(frozen=True)
class DevicePage:
    """A keyset page of device bindings and the cursor for the next one."""

    devices: list[DeviceBinding]
    next_cursor: str | None


def clamp_limit(limit: int | None) -> int:
    """Clamp a client `limit` to the contract bounds (1..100, default 20)."""
    if limit is None:
        return DEFAULT_LIMIT
    if limit < 1:
        return 1
    if limit > MAX_LIMIT:
        return MAX_LIMIT
    return limit


def _encode_cursor(recorded_at: datetime.datetime, id_: uuid.UUID) -> str:
    """Encode a keyset position as an opaque, URL-safe token."""
    payload = json.dumps({"t": recorded_at.isoformat(), "i": str(id_)})
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: str) -> tuple[datetime.datetime, uuid.UUID]:
    """Decode an opaque cursor to a keyset position, or raise `InvalidCursor`."""
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8")
        data = json.loads(raw)
        return datetime.datetime.fromisoformat(data["t"]), uuid.UUID(data["i"])
    except (
        ValueError,
        KeyError,
        TypeError,
        binascii.Error,
        json.JSONDecodeError,
    ) as exc:
        raise InvalidCursor() from exc


def parse_consent_type(value: str) -> ConsentType:
    """Resolve a path `consent_type` string to the enum, or raise 422."""
    try:
        return ConsentType(value)
    except ValueError as exc:
        raise UnknownConsentType(value) from exc


def parse_consent_action(value: str) -> ConsentAction:
    """Resolve a request `action` string to the enum, or raise 422."""
    try:
        return ConsentAction(value)
    except ValueError as exc:
        raise UnknownConsentAction(value) from exc


class ConsentService:
    """List and append the authenticated member's own consent records."""

    def __init__(self, session: Session) -> None:
        self._repo = ConsentRepository(session)

    def list_history(
        self, member_id: uuid.UUID, *, cursor: str | None, limit: int | None
    ) -> Page:
        """Return one keyset page of the member's append-only consent history."""
        page_size = clamp_limit(limit)
        after_recorded_at: datetime.datetime | None = None
        after_id: uuid.UUID | None = None
        if cursor:
            after_recorded_at, after_id = _decode_cursor(cursor)
        # Fetch one extra row to detect whether a further page exists.
        rows = self._repo.list_for_member(
            member_id,
            limit=page_size + 1,
            after_recorded_at=after_recorded_at,
            after_id=after_id,
        )
        return _paginate(rows, page_size)

    def upsert(
        self,
        member_id: uuid.UUID,
        *,
        consent_type: ConsentType,
        action: ConsentAction,
        version: str,
        channel: str | None,
    ) -> Page:
        """Append a grant/withdrawal for the member and return the first history page.

        Refuses (409) to withdraw a service-required consent. On success appends a
        new immutable audit row and returns the first page of the (now updated)
        history — matching the contract's `200 ConsentListResponse`.
        """
        if (
            action is ConsentAction.WITHDRAWN
            and consent_type in SERVICE_REQUIRED_CONSENTS
        ):
            raise ConsentRequiredForService(consent_type)
        self._repo.append(
            member_id=member_id,
            consent_type=consent_type,
            action=action,
            version=version,
            channel=channel or DEFAULT_CONSENT_CHANNEL,
            recorded_at=utc_now(),
        )
        return self.list_history(member_id, cursor=None, limit=None)


class DeviceService:
    """List the authenticated member's own trusted (ACTIVE) devices."""

    def __init__(self, session: Session) -> None:
        self._repo = DeviceBindingRepository(session)

    def list_devices(
        self, member_id: uuid.UUID, *, cursor: str | None, limit: int | None
    ) -> DevicePage:
        """Return one keyset page of the member's ACTIVE device bindings."""
        page_size = clamp_limit(limit)
        after_bound_at: datetime.datetime | None = None
        after_id: uuid.UUID | None = None
        if cursor:
            after_bound_at, after_id = _decode_cursor(cursor)
        rows = self._repo.list_for_member(
            member_id,
            limit=page_size + 1,
            after_bound_at=after_bound_at,
            after_id=after_id,
        )
        if len(rows) > page_size:
            page = rows[:page_size]
            last = page[-1]
            return DevicePage(
                devices=page, next_cursor=_encode_cursor(last.bound_at, last.id)
            )
        return DevicePage(devices=rows, next_cursor=None)


def _paginate(rows: list[ConsentRecord], page_size: int) -> Page:
    """Trim a fetched (page_size + 1) window into a `Page` with a next cursor."""
    if len(rows) > page_size:
        page = rows[:page_size]
        last = page[-1]
        return Page(
            records=page, next_cursor=_encode_cursor(last.recorded_at, last.id)
        )
    return Page(records=rows, next_cursor=None)
