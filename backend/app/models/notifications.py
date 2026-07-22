"""Notifications-domain models (04 §2.10 — EP-11): E-49, E-50, E-51.

Table definitions only, derived the same way as membership.py/ledger.py: enums
are real Enums ONLY where 04 lists their value set; ids are UUID; timestamps via
the mixin; free-form structures (payloads, per-channel dispatch status, quiet
hours) are JSONB. No dispatch/suppression/quiet-hours LOGIC lives here — that is
the notification service; these are the rows it reads and writes.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, Timestamps, UUIDPrimaryKey


class NotificationCategory(enum.Enum):
    """E-49 `category`. Values verbatim from 04 §2.10."""

    PAYMENTS = "PAYMENTS"
    CARDS = "CARDS"
    GROUP_POTS = "GROUP_POTS"
    GOVERNANCE = "GOVERNANCE"
    LENDING = "LENDING"
    GUARANTEES = "GUARANTEES"
    DIVIDENDS = "DIVIDENDS"
    PROJECTS = "PROJECTS"
    SECURITY_REGULATORY = "SECURITY_REGULATORY"
    SYSTEM = "SYSTEM"


class NotificationChannel(enum.Enum):
    """E-49 `default_channels[]` / E-51 `channel`. Values verbatim from 04 §2.10."""

    PUSH = "PUSH"
    EMAIL = "EMAIL"
    SMS = "SMS"
    IN_APP = "IN_APP"


class NotificationEventType(Base, UUIDPrimaryKey, Timestamps):
    """E-49 NotificationEventType — the governed event catalog (US-11.1): new
    event types are configuration rows, not code forks. `suppressible=False`
    marks regulatory/security notices that bypass quiet hours (US-11.2); the
    bypass ENFORCEMENT is dispatch logic, not modelled here."""

    __tablename__ = "notification_event_type"

    # e.g. payment.received, ballot.closing_soon, dividend.paid (04 examples).
    event_key: Mapped[str] = mapped_column(String(128), unique=True)
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, name="notification_category")
    )
    # Enum[] in 04 → array of the enum. Elements are NotificationChannel values.
    default_channels: Mapped[list[NotificationChannel]] = mapped_column(
        ARRAY(Enum(NotificationChannel, name="notification_channel"))
    )
    template_refs: Mapped[dict[str, Any]] = mapped_column(JSONB)
    deep_link_pattern: Mapped[Optional[str]] = mapped_column(String(256))
    suppressible: Mapped[bool] = mapped_column(Boolean)


class Notification(Base, UUIDPrimaryKey, Timestamps):
    """E-50 Notification — a single event instance for a member. `created_at`
    comes from the Timestamps mixin (04 lists it). `channel_dispatches` is the
    per-channel fan-out status {channel, status, at}; the status value set
    (QUEUED|SENT|DELIVERED|FAILED|SUPPRESSED_PREFS|HELD_QUIET_HOURS) lives INSIDE
    that JSON structure in 04, so it is stored as JSONB, not a scalar enum
    column."""

    __tablename__ = "notification"

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    event_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("notification_event_type.id")
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    deep_link: Mapped[Optional[str]] = mapped_column(String(256))
    channel_dispatches: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    read_at: Mapped[Optional[datetime.datetime]]  # in-app inbox read marker


class NotificationPreference(Base, UUIDPrimaryKey, Timestamps):
    """E-51 NotificationPreference — one row per (member, category, channel);
    `quiet_hours` is a member-level JSON blob {start_local, end_local, timezone}
    (04 keeps timezone in the row — consistent with the two-zone, no-DST rule).
    Non-suppressible notices ignore these preferences; that override is dispatch
    logic, not a column."""

    __tablename__ = "notification_preference"
    __table_args__ = (
        UniqueConstraint("member_id", "category", "channel"),  # UQ(member, category, channel)
    )

    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    category: Mapped[NotificationCategory] = mapped_column(
        Enum(NotificationCategory, name="notification_category")
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel")
    )
    enabled: Mapped[bool] = mapped_column(Boolean)
    quiet_hours: Mapped[Optional[dict[str, Any]]] = mapped_column(JSONB)
