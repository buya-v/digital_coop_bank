"""Repository for E-1 `Member` rows.

A Member is created ONLY at KYC promotion (DEC-4: no member record ever reaches a
rejected status, so no row exists before approval). This layer only inserts and
looks up; the promotion rules live in the KYC service. No business logic here.
"""
from __future__ import annotations

import datetime

from sqlalchemy import select

from app.models.membership import Member, MembershipStatus
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    model = Member

    def create(
        self,
        *,
        ovog: str | None,
        etsgiin_ner: str,
        ner: str,
        mrz_name_latin: str | None,
        registration_number: str | None,
        membership_status: MembershipStatus,
    ) -> Member:
        """Insert a new Member and flush so its UUID PK is populated."""
        member = Member(
            ovog=ovog,
            etsgiin_ner=etsgiin_ner,
            ner=ner,
            mrz_name_latin=mrz_name_latin,
            registration_number=registration_number,
            membership_status=membership_status,
        )
        self.add(member)
        self.flush()
        return member

    def get_by_registration_number(
        self, registration_number: str
    ) -> Member | None:
        """Resolve a Member by its national registration number (the identity key)."""
        stmt = select(Member).where(
            Member.registration_number == registration_number
        )
        return self.session.execute(stmt).scalar_one_or_none()


def utc_now() -> datetime.datetime:
    """UTC instant for domain lifecycle timestamps (no Mongolia offset hardcoded;
    the two-timezone/no-DST rule is a display concern, CLAUDE.md)."""
    return datetime.datetime.now(datetime.timezone.utc)  # noqa: UP017
