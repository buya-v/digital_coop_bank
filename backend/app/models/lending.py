"""Lending & Loan Circles (EP-6) — table definitions for E-19…E-30 (04 §2.6).

WHY THIS SCHEMA EXISTS BUT THE FEATURE DOES NOT:

  1. EP-6 is ENTITY-GATED. Lending is unlawful for an SCC until the entity
     decision is made (CLAUDE.md: "Lending/EP-6 is unlawful-until-the-entity-
     decision — do not build"). These tables MODEL the domain for completeness;
     no lending endpoint, flow, or service is built against them.

  2. The loan RATE MODEL is BLOCKED. DEC-48 (12.00% base) and DEC-49 (tiered
     circle discount, floor 4.00%) are recorded but the pricing is unproven and
     under active dispute (CLAUDE.md "Lending should be deferred": DEC-48's rate
     sits below the 17.45% bank-funded market; the FRC folded fintech credit into
     DTI limits on 2026-01-29). Therefore this module deliberately encodes NO
     interest-rate / APR / bps VALUE and NO computed installment:
       - `base_rate_apr_bps` (E-19) and `apr_bps` (E-24) exist as plain Integer
         columns with NO default and NO value — placeholders only, per the task
         rule "column exists, no value/logic". Nothing writes them here.
       - `circle_rate_discount_tiers` (E-19, the DEC-49 discount CURVE) is OMITTED
         — it IS the blocked rate model; see the T3 handoff. Re-add it only once
         the rate model is unblocked.
       - Money AMOUNTS (principal, outstanding, due, pledged, accrued) ARE
         MoneyMinor — they store values written by a servicing engine that does
         not exist yet; no amount is computed in this schema.

Pattern mirrors membership.py / ledger.py: `class X(Base, UUIDPrimaryKey,
Timestamps)`; money -> MoneyMinor; ids UUID; FKs by table-name string. Enums are
real ONLY where 04 §2 lists the value set (LoanStatus per DEC-20 is listed and is
used verbatim); otherwise DeferredEnum (String). Cross-domain references to tables
owned by OTHER model slices (ConfigurationParameter, MakerCheckerApproval,
StaffUser, ComplianceCase, and the glossary `RecipientIdentifierType`) are NOT DB
foreign keys here — they are plain UUID / String columns with a note — so the
schema gate resolves against only the tables that exist. This module implements
NO behaviour: table definitions only.
"""
from __future__ import annotations

import datetime
import enum
import uuid
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, DeferredEnum, Timestamps, UUIDPrimaryKey
from app.db.types import MoneyMinor


# ---------------------------------------------------------------------------
# Enums — real ONLY where 04 §2 lists the value set (verbatim). No invented
# values. LoanStatus is the DEC-20 glossary enum, used verbatim by E-20 & E-24.
# ---------------------------------------------------------------------------


class LoanStatus(enum.Enum):
    """DEC-20 `LoanStatus` — verbatim. Single lifecycle across origination,
    servicing, and NPL reporting (KPI-2.5). ACTIVE begins at disbursement.

    Note: E-20 references a terminal application outcome `DECLINED_CLOSED` that
    is NOT in DEC-20 (see 06 §8.8); per DEC-20 it is recorded in
    `LoanApplication.decision.outcome`, NOT added to this enum."""

    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DELINQUENT = "DELINQUENT"
    PAID_OFF = "PAID_OFF"
    DEFAULTED = "DEFAULTED"
    WRITTEN_OFF = "WRITTEN_OFF"


class LoanProductType(enum.Enum):
    """E-19 product_type. Values verbatim from 04 §2."""

    PERSONAL = "PERSONAL"
    MICRO_BUSINESS = "MICRO_BUSINESS"


class LoanProductStatus(enum.Enum):
    """E-19 status. Values verbatim from 04 §2."""

    ACTIVE = "ACTIVE"
    RETIRED = "RETIRED"


class ScheduleType(enum.Enum):
    """E-19 `schedule_types_allowed[]` and E-25 `schedule_type`. Verbatim."""

    STANDARD = "STANDARD"
    SEASONAL = "SEASONAL"
    INCOME_LINKED = "INCOME_LINKED"


class LoanCircleStatus(enum.Enum):
    """E-21 status. Verbatim. FORMED at 3–5 accepted; ACTIVE while backed loan
    outstanding."""

    FORMING = "FORMING"
    FORMED = "FORMED"
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    DISSOLVED = "DISSOLVED"


class LoanCircleInvitationStatus(enum.Enum):
    """E-22 status. Verbatim. Declining is frictionless and private."""

    SENT = "SENT"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"


class PledgeSource(enum.Enum):
    """E-23 pledge_source. Verbatim. SHARE_CAPITAL enforceability sits behind a
    jurisdiction flag (Open Item 2)."""

    SAVINGS = "SAVINGS"
    SHARE_CAPITAL = "SHARE_CAPITAL"


class PeerGuaranteeStatus(enum.Enum):
    """E-23 status. Verbatim."""

    PENDING_SIGNATURE = "PENDING_SIGNATURE"
    LOCKED = "LOCKED"
    PARTIALLY_RELEASED = "PARTIALLY_RELEASED"
    RELEASED = "RELEASED"
    APPLIED_TO_DEFAULT = "APPLIED_TO_DEFAULT"
    CANCELLED = "CANCELLED"


class RepaymentScheduleStatus(enum.Enum):
    """E-25 status. Verbatim. One ACTIVE version per loan; priors SUPERSEDED."""

    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"


class RepaymentScheduleOrigin(enum.Enum):
    """E-25 origin. Verbatim."""

    ORIGINATION = "ORIGINATION"
    RESTRUCTURE = "RESTRUCTURE"
    HARDSHIP_RESCHEDULE = "HARDSHIP_RESCHEDULE"


class RepaymentInstallmentStatus(enum.Enum):
    """E-26 status. Verbatim."""

    SCHEDULED = "SCHEDULED"
    DUE = "DUE"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    MISSED = "MISSED"
    RESCHEDULED = "RESCHEDULED"
    WAIVED = "WAIVED"


class PayoutOrderMode(enum.Enum):
    """E-27 payout_order_mode. Verbatim. Fixed at creation."""

    AGREED = "AGREED"
    RANDOMIZED = "RANDOMIZED"


class PooledLoanCircleStatus(enum.Enum):
    """E-27 status. Verbatim."""

    FORMING = "FORMING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    HALTED = "HALTED"


class ParticipantPayoutStatus(enum.Enum):
    """E-28 payout_status. Verbatim."""

    WAITING = "WAITING"
    PAID = "PAID"


class CollectionsTrigger(enum.Enum):
    """E-29 trigger. Verbatim."""

    EARLY_WARNING = "EARLY_WARNING"
    FAILED_COLLECTION = "FAILED_COLLECTION"
    DELINQUENT_MILESTONE = "DELINQUENT_MILESTONE"
    HARDSHIP_REQUEST = "HARDSHIP_REQUEST"


class CollectionsCaseStatus(enum.Enum):
    """E-29 status. Verbatim."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED_CURED = "RESOLVED_CURED"
    RESOLVED_RESCHEDULED = "RESOLVED_RESCHEDULED"
    ESCALATED_DEFAULT = "ESCALATED_DEFAULT"
    CLOSED = "CLOSED"


class SignedDocumentType(enum.Enum):
    """E-30 document_type. Verbatim."""

    LOAN_AGREEMENT = "LOAN_AGREEMENT"
    GUARANTEE_PLEDGE_AGREEMENT = "GUARANTEE_PLEDGE_AGREEMENT"
    MEMBERSHIP_CONFIRMATION = "MEMBERSHIP_CONFIRMATION"
    OTHER_AGREEMENT = "OTHER_AGREEMENT"


class SignedDocumentStatus(enum.Enum):
    """E-30 status. Verbatim."""

    DRAFT = "DRAFT"
    SENT = "SENT"
    SIGNED = "SIGNED"
    DECLINED = "DECLINED"
    VOIDED = "VOIDED"
    EXPIRED = "EXPIRED"


# ---------------------------------------------------------------------------
# E-19 LoanProduct
# ---------------------------------------------------------------------------


class LoanProduct(Base, UUIDPrimaryKey, Timestamps):
    """E-19 LoanProduct. Amounts/terms are config-sourced (US-12.5), never
    hard-coded. RATE MODEL BLOCKED: base_rate_apr_bps is a bare placeholder and
    the DEC-49 discount-tier curve is intentionally omitted (see module docstring
    / T3 handoff)."""

    __tablename__ = "loan_product"

    name: Mapped[str] = mapped_column(String(120))
    product_type: Mapped[LoanProductType] = mapped_column(
        Enum(LoanProductType, name="loan_product_type")
    )
    amount_min = mapped_column(MoneyMinor)  # config-sourced (US-12.5)
    amount_max = mapped_column(MoneyMinor)  # config-sourced (US-12.5)
    term_options_months = mapped_column(ARRAY(Integer))
    # rate model BLOCKED (DEC-48/49) — column exists, no value/logic. NO default.
    base_rate_apr_bps: Mapped[Optional[int]] = mapped_column(Integer)
    # OMITTED: circle_rate_discount_tiers (DEC-49 discount curve) — that JSON IS
    # the blocked rate model. Re-add only when the rate model is unblocked.
    schedule_types_allowed = mapped_column(
        ARRAY(Enum(ScheduleType, name="schedule_type"))
    )
    status: Mapped[LoanProductStatus] = mapped_column(
        Enum(LoanProductStatus, name="loan_product_status")
    )
    # logical FK -> ConfigurationParameter (US-12.5 registry, another slice); not
    # a DB FK here so the schema gate resolves.
    config_version_ref: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))


# ---------------------------------------------------------------------------
# E-20 LoanApplication
# ---------------------------------------------------------------------------


class LoanApplication(Base, UUIDPrimaryKey, Timestamps):
    """E-20 LoanApplication. Uses LoanStatus (DEC-20) for its origination segment
    (DRAFT | SUBMITTED | UNDER_REVIEW | APPROVED — declined outcomes live in
    `decision.outcome`, not the enum; declined applications never become Loans)."""

    __tablename__ = "loan_application"

    applicant_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )  # must be ACTIVE (US-2.2) — enforced in service, not schema
    loan_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_product.id")
    )
    requested_amount = mapped_column(MoneyMinor)
    requested_term_months: Mapped[int] = mapped_column(Integer)
    purpose: Mapped[Optional[str]] = mapped_column(String(500))
    affordability_inputs = mapped_column(JSONB)  # declared income/expenses
    # Full LoanStatus enum; the DRAFT..APPROVED subset is a state-machine rule.
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus, name="loan_status"))
    decision = mapped_column(JSONB)  # engine output; fully logged (US-13.3)
    offer = mapped_column(JSONB)  # {amount, term_months, ..., expires_at} — see note
    loan_circle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_circle.id")
    )
    # logical FK -> ComplianceCase-style loan referral (US-12.3 queue, another
    # slice); not a DB FK here.
    referral_case_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    submitted_at: Mapped[Optional[datetime.datetime]]
    decided_at: Mapped[Optional[datetime.datetime]]
    # NOTE: `offer`/`decision` JSON carry apr_bps FIELDS at runtime, but this
    # schema encodes NO rate VALUE — the rate model is BLOCKED (DEC-48/49).


# ---------------------------------------------------------------------------
# E-21 LoanCircle
# ---------------------------------------------------------------------------


class LoanCircle(Base, UUIDPrimaryKey, Timestamps):
    """E-21 LoanCircle. Peer-guarantee group of 3–5 ACTIVE members (DEC-7).
    min/max members (3/5) are config-asserted, not schema constraints."""

    __tablename__ = "loan_circle"

    borrower_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    loan_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_application.id"), unique=True
    )
    status: Mapped[LoanCircleStatus] = mapped_column(
        Enum(LoanCircleStatus, name="loan_circle_status")
    )
    formed_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-22 LoanCircleInvitation
# ---------------------------------------------------------------------------


class LoanCircleInvitation(Base, UUIDPrimaryKey, Timestamps):
    """E-22 LoanCircleInvitation. UQ(circle, invitee)."""

    __tablename__ = "loan_circle_invitation"
    __table_args__ = (
        UniqueConstraint(
            "loan_circle_id", "invitee_member_id", name="loan_circle_invitation_circle_invitee"
        ),
    )

    loan_circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_circle.id")
    )
    invitee_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )  # ACTIVE only — enforced in service
    # `addressed_via` is the glossary enum RecipientIdentifierType
    # (PHONE|EMAIL|MEMBER_ID, DEC-3) — owned by another slice; DeferredEnum here
    # to avoid cross-slice enum-type ownership collision.
    addressed_via: Mapped[str] = mapped_column(DeferredEnum)
    disclosure = mapped_column(JSONB)  # amount, term, requested pledge, risk stmt
    status: Mapped[LoanCircleInvitationStatus] = mapped_column(
        Enum(LoanCircleInvitationStatus, name="loan_circle_invitation_status")
    )
    sent_at: Mapped[Optional[datetime.datetime]]
    responded_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-23 PeerGuarantee
# ---------------------------------------------------------------------------


class PeerGuarantee(Base, UUIDPrimaryKey, Timestamps):
    """E-23 PeerGuarantee — the guarantee pledge (DEC-7): a guarantor's locked
    portion of savings/share capital. The hold is a ledger posting (E-7), never a
    mutable flag; that posting logic lives in the ledger service (not built)."""

    __tablename__ = "peer_guarantee"

    loan_circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_circle.id")
    )
    guarantor_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    loan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan.id")
    )  # attached at disbursement
    pledge_source: Mapped[PledgeSource] = mapped_column(
        Enum(PledgeSource, name="pledge_source")
    )
    source_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    pledged_amount = mapped_column(MoneyMinor)  # <= available balance at pledge time
    released_amount = mapped_column(MoneyMinor)  # cumulative pro-rata release
    applied_amount = mapped_column(MoneyMinor)  # applied on DEFAULTED
    hold_ledger_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ledger_entry.id")
    )  # the hold posting; excluded from withdrawals/transfers/Round-Up sweeps
    agreement_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signed_document.id")
    )
    status: Mapped[PeerGuaranteeStatus] = mapped_column(
        Enum(PeerGuaranteeStatus, name="peer_guarantee_status")
    )
    locked_at: Mapped[Optional[datetime.datetime]]
    released_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-24 Loan
# ---------------------------------------------------------------------------


class Loan(Base, UUIDPrimaryKey, Timestamps):
    """E-24 Loan — the servicing entity, created at disbursement (APPROVED ->
    ACTIVE, US-6.7). Lifecycle = LoanStatus (DEC-20). outstanding_principal /
    accrued_interest / days_past_due are DERIVED by a servicing engine that does
    not exist yet; nothing here computes them. RATE MODEL BLOCKED: apr_bps is a
    bare placeholder column with NO value."""

    __tablename__ = "loan"

    loan_application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_application.id"), unique=True
    )
    borrower_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    loan_product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_product.id")
    )
    loan_circle_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan_circle.id")
    )
    principal_amount = mapped_column(MoneyMinor)
    outstanding_principal = mapped_column(MoneyMinor)  # derived — not computed here
    accrued_interest = mapped_column(MoneyMinor)  # derived — no accrual logic here
    # rate model BLOCKED (DEC-48/49) — column exists, no value/logic. NO default.
    apr_bps: Mapped[Optional[int]] = mapped_column(Integer)
    disbursement_transaction_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("transaction.id")
    )
    disbursement_account_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    status: Mapped[LoanStatus] = mapped_column(Enum(LoanStatus, name="loan_status"))
    autopay = mapped_column(JSONB)  # {enabled, source_account_id, retry_policy}
    days_past_due: Mapped[Optional[int]] = mapped_column(Integer)  # derived
    agreement_document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("signed_document.id")
    )
    disbursed_at: Mapped[Optional[datetime.datetime]]
    maturity_date: Mapped[Optional[datetime.date]] = mapped_column(Date)
    closed_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-25 RepaymentSchedule
# ---------------------------------------------------------------------------


class RepaymentSchedule(Base, UUIDPrimaryKey, Timestamps):
    """E-25 RepaymentSchedule — versioned header; regenerated (new version) on
    restructure/hardship, priors retained for audit. UQ(loan, version)."""

    __tablename__ = "repayment_schedule"
    __table_args__ = (
        UniqueConstraint("loan_id", "version", name="repayment_schedule_loan_version"),
    )

    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan.id")
    )
    version: Mapped[int] = mapped_column(Integer)
    schedule_type: Mapped[ScheduleType] = mapped_column(
        Enum(ScheduleType, name="schedule_type")
    )
    seasonal_profile = mapped_column(JSONB)  # month-weighting for flexible plans
    installment_count: Mapped[int] = mapped_column(Integer)
    first_due_date: Mapped[datetime.date] = mapped_column(Date)
    status: Mapped[RepaymentScheduleStatus] = mapped_column(
        Enum(RepaymentScheduleStatus, name="repayment_schedule_status")
    )
    origin: Mapped[RepaymentScheduleOrigin] = mapped_column(
        Enum(RepaymentScheduleOrigin, name="repayment_schedule_origin")
    )
    # logical FK -> MakerCheckerApproval (staff reschedules, another slice); not a
    # DB FK here.
    approved_via: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))


# ---------------------------------------------------------------------------
# E-26 RepaymentInstallment
# ---------------------------------------------------------------------------


class RepaymentInstallment(Base, UUIDPrimaryKey, Timestamps):
    """E-26 RepaymentInstallment. UQ(schedule, sequence). The due amounts are
    STORED columns (MoneyMinor) written by the servicing engine — this schema
    computes NO installment (rate model BLOCKED, DEC-48/49)."""

    __tablename__ = "repayment_installment"
    __table_args__ = (
        UniqueConstraint(
            "repayment_schedule_id", "sequence", name="repayment_installment_schedule_sequence"
        ),
    )

    repayment_schedule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repayment_schedule.id")
    )
    sequence: Mapped[int] = mapped_column(Integer)
    due_date: Mapped[datetime.date] = mapped_column(Date)
    principal_due = mapped_column(MoneyMinor)  # stored amount; not computed here
    interest_due = mapped_column(MoneyMinor)  # stored amount; not computed here
    total_due = mapped_column(MoneyMinor)  # stored amount; not computed here
    paid_amount = mapped_column(MoneyMinor)
    status: Mapped[RepaymentInstallmentStatus] = mapped_column(
        Enum(RepaymentInstallmentStatus, name="repayment_installment_status")
    )
    payment_transaction_ids = mapped_column(
        ARRAY(UUID(as_uuid=True))
    )  # repayment Transactions applied (logical refs -> transaction.id)
    paid_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-27 PooledLoanCircle
# ---------------------------------------------------------------------------


class PooledLoanCircle(Base, UUIDPrimaryKey, Timestamps):
    """E-27 PooledLoanCircle — the ROSCA variant (DEC-7, US-6.5): fixed monthly
    contribution, rotating lump-sum payout, order fixed at creation. The circle
    ledger (contributions, payouts, arrears) is a DERIVED view over Transactions,
    not a column here."""

    __tablename__ = "pooled_loan_circle"

    name: Mapped[str] = mapped_column(String(80))
    creator_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    contribution_amount = mapped_column(MoneyMinor)
    cycle_count: Mapped[int] = mapped_column(Integer)  # = participant count
    current_cycle: Mapped[int] = mapped_column(Integer)
    collection_day_of_month: Mapped[int] = mapped_column(Integer)
    payout_order_mode: Mapped[PayoutOrderMode] = mapped_column(
        Enum(PayoutOrderMode, name="payout_order_mode")
    )
    backstop_rules = mapped_column(JSONB)  # missed-contribution handling config
    status: Mapped[PooledLoanCircleStatus] = mapped_column(
        Enum(PooledLoanCircleStatus, name="pooled_loan_circle_status")
    )
    activated_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-28 PooledLoanCircleParticipant
# ---------------------------------------------------------------------------


class PooledLoanCircleParticipant(Base, UUIDPrimaryKey, Timestamps):
    """E-28 PooledLoanCircleParticipant. UQ(circle, member); payout_position UQ
    within circle."""

    __tablename__ = "pooled_loan_circle_participant"
    __table_args__ = (
        UniqueConstraint(
            "pooled_loan_circle_id", "member_id", name="pooled_participant_circle_member"
        ),
        UniqueConstraint(
            "pooled_loan_circle_id", "payout_position", name="pooled_participant_circle_position"
        ),
    )

    pooled_loan_circle_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pooled_loan_circle.id")
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )  # ACTIVE only — enforced in service
    payout_position: Mapped[int] = mapped_column(Integer)  # UQ within circle
    payout_status: Mapped[ParticipantPayoutStatus] = mapped_column(
        Enum(ParticipantPayoutStatus, name="participant_payout_status")
    )
    funding_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("account.id")
    )
    missed_contributions: Mapped[int] = mapped_column(Integer)
    joined_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-29 CollectionsCase
# ---------------------------------------------------------------------------


class CollectionsCase(Base, UUIDPrimaryKey, Timestamps):
    """E-29 CollectionsCase — arrears/hardship case (US-6.8), worked in the Loan
    Operations Console (US-12.3). Guarantors are alerted at DELINQUENT milestones
    BEFORE any pledge draw (US-6.8)."""

    __tablename__ = "collections_case"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("loan.id")
    )
    borrower_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("member.id")
    )
    trigger: Mapped[CollectionsTrigger] = mapped_column(
        Enum(CollectionsTrigger, name="collections_trigger")
    )
    hardship_request = mapped_column(JSONB)  # borrower's proposed reschedule
    guarantor_notifications = mapped_column(JSONB)  # log of guarantor alerts
    # logical FK -> StaffUser (another slice); not a DB FK here.
    assigned_staff_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    status: Mapped[CollectionsCaseStatus] = mapped_column(
        Enum(CollectionsCaseStatus, name="collections_case_status")
    )
    opened_at: Mapped[Optional[datetime.datetime]]
    closed_at: Mapped[Optional[datetime.datetime]]


# ---------------------------------------------------------------------------
# E-30 SignedDocument
# ---------------------------------------------------------------------------


class SignedDocument(Base, UUIDPrimaryKey, Timestamps):
    """E-30 SignedDocument — e-signature ceremony record + encrypted vault entry
    (US-6.6). Applies to loan agreements, pledge agreements, and future types;
    templates are configuration. `provider_envelope_ref` is a vendor envelope ID:
    per CLAUDE.md the e-sign vendor is a Mongolian-market open item, not assumed."""

    __tablename__ = "signed_document"

    document_type: Mapped[SignedDocumentType] = mapped_column(
        Enum(SignedDocumentType, name="signed_document_type")
    )
    subject_refs = mapped_column(JSONB)  # linked domain entities (loan, pledge, member)
    provider_envelope_ref: Mapped[Optional[str]] = mapped_column(String(255))
    signer_member_ids = mapped_column(
        ARRAY(UUID(as_uuid=True))
    )  # logical refs -> member.id
    document_sha256: Mapped[Optional[str]] = mapped_column(String(64))  # tamper hash
    storage_ref: Mapped[Optional[str]] = mapped_column(String(1024))  # encrypted WORM URI
    status: Mapped[SignedDocumentStatus] = mapped_column(
        Enum(SignedDocumentStatus, name="signed_document_status")
    )
    sent_at: Mapped[Optional[datetime.datetime]]
    completed_at: Mapped[Optional[datetime.datetime]]
