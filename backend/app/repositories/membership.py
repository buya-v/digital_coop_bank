"""Repository for E-1 `Member` rows.

A Member is created ONLY at KYC promotion (DEC-4: no member record ever reaches a
rejected status, so no row exists before approval). This layer only inserts and
looks up; the promotion rules live in the KYC service. No business logic here.
"""
from __future__ import annotations

import datetime
import uuid

from sqlalchemy import select

from app.models.membership import Member, MembershipStatus
from app.repositories.base import BaseRepository


class MemberRepository(BaseRepository[Member]):
    model = Member

    def create(
        self,
        *,
        member_id: str,
        ovog: str | None,
        etsgiin_ner: str,
        ner: str,
        mrz_name_latin: str | None,
        registration_number: str | None,
        membership_status: MembershipStatus,
        email: str,
        phone_number: str,
        address_line_1: str | None = None,
        address_line_2: str | None = None,
        city: str | None = None,
        region: str | None = None,
        postal_code: str | None = None,
        country: str | None = None,
        preferred_language: str = "mn",
    ) -> Member:
        """Insert a new Member and flush so its UUID PK is populated.

        `member_id` is the caller-generated non-guessable public id (DEC-28);
        `email`/`phone_number` are the KYC-verified contact channels carried over
        from the draft (both required at draft bootstrap). Address parts and the
        preferred language default to unset / Cyrillic-Mongolian (`mn`)."""
        member = Member(
            member_id=member_id,
            ovog=ovog,
            etsgiin_ner=etsgiin_ner,
            ner=ner,
            mrz_name_latin=mrz_name_latin,
            registration_number=registration_number,
            membership_status=membership_status,
            email=email,
            phone_number=phone_number,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            region=region,
            postal_code=postal_code,
            country=country,
            preferred_language=preferred_language,
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

    def get_by_member_id(self, member_id: str) -> Member | None:
        """Resolve a Member by its public member_id (used only to guarantee the
        generated id is unique before insert; never a request-supplied lookup)."""
        stmt = select(Member).where(Member.member_id == member_id)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_subject(self, subject: str) -> Member | None:
        """Resolve a verified token `sub` to a Member, or None.

        The member-auth foundation maps the IdP token subject to the Member's
        UUID primary key. A `sub` that is not a well-formed UUID (or matches no
        row) resolves to None — the caller renders that as an auth failure. This
        is the ONLY claim treated as a member fact: nothing else in the token is
        trusted about the member (all member data comes from this DB row).
        """
        try:
            member_id = uuid.UUID(subject)
        except (ValueError, AttributeError, TypeError):
            return None
        return self.get(member_id)


def utc_now() -> datetime.datetime:
    """UTC instant for domain lifecycle timestamps (no Mongolia offset hardcoded;
    the two-timezone/no-DST rule is a display concern, CLAUDE.md)."""
    return datetime.datetime.now(datetime.timezone.utc)  # noqa: UP017
