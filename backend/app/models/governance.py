"""Democratic-governance models (EP-8) — 04 §2.8, entities E-34..E-42.

Table definitions only; no vote-tallying, quorum, certification, or delegation
logic (that is the Governance Service, S-8). Enums are real ONLY where 04 lists
their full value set; where 04 leaves a set open ("Enum incl. ...") the column is
a DeferredEnum (String), never an invented value set.

SECRET-BALLOT INVARIANT (04 §5.1, F-E). Participation and choice are separated at
the schema level: E-39 VoteParticipation records WHO voted (member x ballot, no
choice); E-40 VoteRecord records WHAT was chosen (choice, NO member FK). The two
tables share only `ballot_id` and carry no relational or storage-level link. Any
column that let you join a member to a choice would violate the invariant, so
VoteRecord deliberately has no member_id and does NOT use the Timestamps mixin
(precise created_at/updated_at would defeat the §5.1 timestamp-coarsening rule;
its only time field is the coarsened `cast_at`).
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DeferredEnum, Timestamps, UUIDPrimaryKey


# --- Enums (values verbatim from 04 §2.8 / DEC-1, DEC-2, DEC-9) ---

class ProposalCategory(enum.Enum):
    """E-34 category (DEC-2). Also the scope of a category-scoped ProxyDelegation."""

    COMMUNITY_GRANT = "COMMUNITY_GRANT"
    FINANCIAL_POLICY = "FINANCIAL_POLICY"
    GOVERNANCE_BYLAW = "GOVERNANCE_BYLAW"


class ProposalStatus(enum.Enum):
    """E-34 status machine (DEC-9)."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    OPEN_FOR_VOTING = "OPEN_FOR_VOTING"
    PASSED = "PASSED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"


class ProposalCommentStatus(enum.Enum):
    """E-36 moderation status."""

    VISIBLE = "VISIBLE"
    HIDDEN_BY_MODERATOR = "HIDDEN_BY_MODERATOR"
    REMOVED = "REMOVED"
    AUTHOR_DELETED = "AUTHOR_DELETED"


class BallotType(enum.Enum):
    """E-37 ballot_type (DEC-2)."""

    PROPOSAL = "PROPOSAL"
    BOARD_ELECTION = "BOARD_ELECTION"


class BallotStatus(enum.Enum):
    """E-37 status."""

    SCHEDULED = "SCHEDULED"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CERTIFIED = "CERTIFIED"


class VoteChoice(enum.Enum):
    """E-40 choice for PROPOSAL ballots (DEC-1)."""

    FOR = "FOR"
    AGAINST = "AGAINST"
    ABSTAIN = "ABSTAIN"


class ProxyDelegationStatus(enum.Enum):
    """E-41 status (DEC-8)."""

    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    AUTO_VOIDED = "AUTO_VOIDED"


# --- Tables ---

class Proposal(Base, UUIDPrimaryKey, Timestamps):
    """E-34 Proposal (DEC-2/DEC-9, US-8.2). `OPEN_FOR_VOTING` is set only by ballot
    scheduling (logic, not here). `cosignature_count` is derived by the service."""

    __tablename__ = "proposal"

    author_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    title: Mapped[str] = mapped_column(String(150))
    summary: Mapped[str] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    category: Mapped[ProposalCategory] = mapped_column(
        Enum(ProposalCategory, name="proposal_category")
    )
    status: Mapped[ProposalStatus] = mapped_column(
        Enum(ProposalStatus, name="proposal_status")
    )
    # 04: "Enum incl. QUORUM_NOT_MET" — the value set is NOT fully enumerated, so
    # this is a DeferredEnum (String), not an invented enum.
    rejection_reason: Mapped[Optional[str]] = mapped_column(DeferredEnum)
    cosignature_threshold: Mapped[int] = mapped_column(Integer)  # config
    cosignature_count: Mapped[int] = mapped_column(Integer)  # derived
    ballot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    linked_project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("community_project.id")
    )
    submitted_at: Mapped[Optional[datetime.datetime]]
    resolved_at: Mapped[Optional[datetime.datetime]]


class ProposalCosignature(Base, UUIDPrimaryKey, Timestamps):
    """E-35 ProposalCosignature. UQ(proposal, member)."""

    __tablename__ = "proposal_cosignature"
    __table_args__ = (UniqueConstraint("proposal_id", "member_id"),)

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposal.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    signed_at: Mapped[datetime.datetime]


class ProposalComment(Base, UUIDPrimaryKey, Timestamps):
    """E-36 ProposalComment (US-8.6). Self-referential thread; threads lock at
    OPEN_FOR_VOTING (enforced by the service, not the schema)."""

    __tablename__ = "proposal_comment"

    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposal.id")
    )
    parent_comment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposal_comment.id")
    )
    author_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    body: Mapped[str] = mapped_column(Text)
    status: Mapped[ProposalCommentStatus] = mapped_column(
        Enum(ProposalCommentStatus, name="proposal_comment_status")
    )
    moderation_reason: Mapped[Optional[str]] = mapped_column(String(255))
    report_count: Mapped[int] = mapped_column(Integer)


class Ballot(Base, UUIDPrimaryKey, Timestamps):
    """E-37 Ballot — the voting event (US-12.4). `results` is set at certification
    by the service; nothing writes it here. Circular FK with EligibilitySnapshot
    (Ballot->snapshot, snapshot->ballot) — the snapshot is captured at open, so
    `eligibility_snapshot_id` is nullable until then."""

    __tablename__ = "ballot"

    ballot_type: Mapped[BallotType] = mapped_column(Enum(BallotType, name="ballot_type"))
    proposal_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposal.id")
    )
    title: Mapped[str] = mapped_column(String(255))
    context_pack = mapped_column(JSONB)  # rationale, discussion link, category
    opens_at: Mapped[datetime.datetime]
    closes_at: Mapped[datetime.datetime]
    quorum_rule = mapped_column(JSONB)  # quorum % + result-visibility rules
    seats: Mapped[Optional[int]] = mapped_column(Integer)  # BOARD_ELECTION only
    eligibility_snapshot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("eligibility_snapshot.id")
    )
    status: Mapped[BallotStatus] = mapped_column(Enum(BallotStatus, name="ballot_status"))
    results = mapped_column(JSONB)  # tallies/turnout/outcome, set at certification
    certified_at: Mapped[Optional[datetime.datetime]]


class EligibilitySnapshot(Base, UUIDPrimaryKey, Timestamps):
    """E-38 EligibilitySnapshot (US-2.3). Immutable member-ID set (hashed at rest);
    `registry_hash` is tamper evidence for certification."""

    __tablename__ = "eligibility_snapshot"
    __table_args__ = (UniqueConstraint("ballot_id"),)

    ballot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    captured_at: Mapped[datetime.datetime]
    eligible_member_count: Mapped[int] = mapped_column(Integer)
    snapshot_ref: Mapped[str] = mapped_column(String(255))  # hashed member-ID set
    registry_hash: Mapped[str] = mapped_column(String(255))


class VoteParticipation(Base, UUIDPrimaryKey, Timestamps):
    """E-39 VoteParticipation — WHO voted, never how. One row per member per ballot
    (one-member-one-vote). SECRET-BALLOT: this is the ONLY governance table that
    links a member to a ballot; it carries NO choice. It shares only `ballot_id`
    with VoteRecord and there is no key from here to a VoteRecord row."""

    __tablename__ = "vote_participation"
    __table_args__ = (UniqueConstraint("ballot_id", "member_id"),)

    ballot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    via_delegation: Mapped[bool] = mapped_column(Boolean)
    delegate_member_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    superseded_by_direct_vote: Mapped[bool] = mapped_column(Boolean)
    receipt_hash: Mapped[str] = mapped_column(String(255), unique=True)
    voted_at: Mapped[datetime.datetime]
    auth_context = mapped_column(JSONB)  # step-up evidence (US-1.4)


class VoteRecord(Base, UUIDPrimaryKey):
    """E-40 VoteRecord — the anonymous CHOICE. SECRET-BALLOT INVARIANT (04 §5.1):
    NO member FK, NO relational or storage-level link to VoteParticipation. The
    only shared column is `ballot_id`. Deliberately does NOT inherit Timestamps —
    a precise created_at/updated_at would enable the timing correlation §5.1
    forbids; the single time field is `cast_at`, which the service coarsens.

    `candidate_selections` is a bare UUID[] of ElectionCandidate ids (BOARD_ELECTION
    ballots) — NOT a ForeignKey, so no relational path leads back to a member.
    `validity_proof` is a blind-token proof binding the record to a valid but
    unlinkable participation; `voided` is set via that proof, never by identity."""

    __tablename__ = "vote_record"

    ballot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    choice: Mapped[Optional[VoteChoice]] = mapped_column(
        Enum(VoteChoice, name="vote_choice")
    )  # PROPOSAL ballots
    candidate_selections = mapped_column(ARRAY(UUID(as_uuid=True)))  # BOARD_ELECTION; no FK
    validity_proof: Mapped[str] = mapped_column(String(255))  # blind-token proof
    voided: Mapped[bool] = mapped_column(Boolean)
    cast_at: Mapped[datetime.datetime]  # coarsened by the service (§5.1)


class ProxyDelegation(Base, UUIDPrimaryKey, Timestamps):
    """E-41 ProxyDelegation (DEC-8, US-8.4/8.5). Category-scoped, single-level,
    instantly revocable. Single-level enforcement and the "exactly one ACTIVE
    delegate per scope" partial-unique rule live in the service; 04's
    UQ(delegator, scope) WHERE status=ACTIVE is a partial index best emitted by a
    migration, so it is not declared as a table-level constraint here."""

    __tablename__ = "proxy_delegation"

    delegator_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    delegate_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    # Scope is EITHER a proposal category OR ballot_type_scope=BOARD_ELECTION.
    proposal_category: Mapped[Optional[ProposalCategory]] = mapped_column(
        Enum(ProposalCategory, name="proposal_category")
    )
    # Only BOARD_ELECTION is a valid scope value (constraint enforced in service).
    ballot_type_scope: Mapped[Optional[BallotType]] = mapped_column(
        Enum(BallotType, name="ballot_type")
    )
    status: Mapped[ProxyDelegationStatus] = mapped_column(
        Enum(ProxyDelegationStatus, name="proxy_delegation_status")
    )
    revoked_at: Mapped[Optional[datetime.datetime]]


class ElectionCandidate(Base, UUIDPrimaryKey, Timestamps):
    """E-42 ElectionCandidate (US-8.3). `votes_received`/`elected` populated only at
    certification. UQ(ballot, member)."""

    __tablename__ = "election_candidate"
    __table_args__ = (UniqueConstraint("ballot_id", "member_id"),)

    ballot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ballot.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    statement: Mapped[str] = mapped_column(Text)
    profile_ref: Mapped[Optional[str]] = mapped_column(String(255))
    votes_received: Mapped[Optional[int]] = mapped_column(Integer)  # at certification
    elected: Mapped[bool] = mapped_column(Boolean)
    term = mapped_column(JSONB)  # {starts_on, ends_on}
