"""initial schema — all 59 entities (60 tables) from 04 §2

Ledger-core tables (account, ledger_entry, transaction) are STRUCTURE ONLY —
no posting/balance/hold logic; entry_type/transaction_type are String (value
sets HELD on the corrected ledger design). Rendered offline from the ORM
metadata (Postgres dialect). CI applies + verifies against real Postgres.
"""
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

_UP = [
    """CREATE TYPE staff_role AS ENUM ('OPS_ADMIN', 'COMPLIANCE_OFFICER', 'LOAN_OFFICER', 'GOVERNANCE_ADMIN', 'FINANCE_ADMIN', 'AUDITOR', 'SUPER_ADMIN')""",
    """CREATE TYPE staff_status AS ENUM ('ACTIVE', 'SUSPENDED', 'DEACTIVATED')""",
    """CREATE TYPE approval_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED', 'CANCELLED')""",
    """CREATE TYPE compliance_case_type AS ENUM ('KYC_REVIEW', 'AML_ALERT', 'SAR', 'FRAUD', 'DISPUTE')""",
    """CREATE TYPE compliance_case_priority AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')""",
    """CREATE TYPE compliance_case_status AS ENUM ('OPEN', 'ASSIGNED', 'IN_REVIEW', 'PENDING_APPROVAL', 'ESCALATED', 'CLOSED_APPROVED', 'CLOSED_REJECTED', 'CLOSED_FILED', 'CLOSED_NO_ACTION')""",
    """CREATE TYPE card_type AS ENUM ('VIRTUAL', 'PHYSICAL')""",
    """CREATE TYPE card_status AS ENUM ('PENDING_ACTIVATION', 'ACTIVE', 'FROZEN', 'REPORTED_LOST', 'TERMINATED')""",
    """CREATE TYPE data_subject_request_type AS ENUM ('ACCESS', 'DELETION', 'RECTIFICATION', 'PORTABILITY')""",
    """CREATE TYPE data_subject_request_status AS ENUM ('RECEIVED', 'IN_PROGRESS', 'PENDING_REDACTION', 'DELIVERED', 'PARTIALLY_FULFILLED', 'REJECTED_LEGAL_BASIS')""",
    """CREATE TYPE regulatory_report_status AS ENUM ('RUNNING', 'COMPLETED', 'FAILED', 'SUBMITTED')""",
    """CREATE TYPE group_pot_status AS ENUM ('ACTIVE', 'CLOSED')""",
    """CREATE TYPE group_pot_member_role AS ENUM ('CREATOR', 'MEMBER')""",
    """CREATE TYPE recipient_identifier_type AS ENUM ('PHONE', 'EMAIL', 'MEMBER_ID')""",
    """CREATE TYPE group_pot_member_status AS ENUM ('INVITED', 'ACTIVE', 'DECLINED', 'REMOVED', 'LEFT')""",
    """CREATE TYPE group_pot_approval_status AS ENUM ('PENDING', 'APPROVED_EXECUTED', 'REJECTED', 'CANCELLED_UNREACHABLE', 'EXPIRED')""",
    """CREATE TYPE group_pot_approval_decision AS ENUM ('APPROVED', 'REJECTED')""",
    """CREATE TYPE patronage_period AS ENUM ('MONTH')""",
    """CREATE TYPE dividend_declaration_status AS ENUM ('DRAFT', 'CALCULATED', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTING', 'COMPLETED', 'RECONCILED', 'CANCELLED')""",
    """CREATE TYPE payout_destination AS ENUM ('SAVINGS', 'SHARE_REINVESTMENT')""",
    """CREATE TYPE dividend_allocation_status AS ENUM ('CALCULATED', 'PAID', 'REINVESTED', 'FAILED_RETRYING', 'ESCALATED')""",
    """CREATE TYPE community_project_status AS ENUM ('SUBMITTED', 'IN_REVIEW', 'PUBLISHED', 'DECLINED', 'FUNDED', 'UNSUCCESSFUL_REFUNDED', 'COMPLETED')""",
    """CREATE TYPE backing_source AS ENUM ('SAVINGS', 'ROUND_UP')""",
    """CREATE TYPE backing_status AS ENUM ('SETTLED', 'REFUNDED')""",
    """CREATE TYPE grant_pool_status AS ENUM ('OPEN', 'EXHAUSTED', 'CLOSED')""",
    """CREATE TYPE surplus_match_status AS ENUM ('ACCRUING', 'PENDING_BALLOT', 'RELEASED', 'HALTED_CAP', 'HALTED_POOL')""",
    """CREATE TYPE proposal_category AS ENUM ('COMMUNITY_GRANT', 'FINANCIAL_POLICY', 'GOVERNANCE_BYLAW')""",
    """CREATE TYPE proposal_status AS ENUM ('DRAFT', 'SUBMITTED', 'OPEN_FOR_VOTING', 'PASSED', 'REJECTED', 'WITHDRAWN')""",
    """CREATE TYPE proposal_comment_status AS ENUM ('VISIBLE', 'HIDDEN_BY_MODERATOR', 'REMOVED', 'AUTHOR_DELETED')""",
    """CREATE TYPE ballot_type AS ENUM ('PROPOSAL', 'BOARD_ELECTION')""",
    """CREATE TYPE ballot_status AS ENUM ('SCHEDULED', 'OPEN', 'CLOSED', 'CERTIFIED')""",
    """CREATE TYPE vote_choice AS ENUM ('FOR', 'AGAINST', 'ABSTAIN')""",
    """CREATE TYPE proxy_delegation_status AS ENUM ('ACTIVE', 'REVOKED', 'AUTO_VOIDED')""",
    """CREATE TYPE kyc_document_type AS ENUM ('PASSPORT', 'DRIVERS_LICENSE', 'NATIONAL_ID')""",
    """CREATE TYPE kyc_screening_result AS ENUM ('CLEAR', 'POTENTIAL_MATCH', 'MATCH')""",
    """CREATE TYPE kyc_result AS ENUM ('PASSED', 'NEEDS_REVIEW', 'FAILED')""",
    """CREATE TYPE device_platform AS ENUM ('IOS', 'ANDROID', 'WEB')""",
    """CREATE TYPE device_status AS ENUM ('ACTIVE', 'REVOKED')""",
    """CREATE TYPE consent_type AS ENUM ('TERMS_AND_BYLAWS', 'PRIVACY_POLICY', 'E_SIGN_DISCLOSURE', 'MARKETING', 'DATA_SHARING_OPEN_BANKING', 'IMPACT_SPOTLIGHT')""",
    """CREATE TYPE consent_action AS ENUM ('GRANTED', 'WITHDRAWN')""",
    """CREATE TYPE account_type AS ENUM ('MEMBERSHIP_SHARE', 'PRIMARY_SAVINGS', 'TRANSACTION', 'GROUP_POT', 'SYSTEM')""",
    """CREATE TYPE ledger_direction AS ENUM ('DEBIT', 'CREDIT')""",
    """CREATE TYPE loan_product_type AS ENUM ('PERSONAL', 'MICRO_BUSINESS')""",
    """CREATE TYPE schedule_type AS ENUM ('STANDARD', 'SEASONAL', 'INCOME_LINKED')""",
    """CREATE TYPE loan_product_status AS ENUM ('ACTIVE', 'RETIRED')""",
    """CREATE TYPE loan_status AS ENUM ('DRAFT', 'SUBMITTED', 'UNDER_REVIEW', 'APPROVED', 'ACTIVE', 'DELINQUENT', 'PAID_OFF', 'DEFAULTED', 'WRITTEN_OFF')""",
    """CREATE TYPE loan_circle_status AS ENUM ('FORMING', 'FORMED', 'ACTIVE', 'RELEASED', 'DISSOLVED')""",
    """CREATE TYPE loan_circle_invitation_status AS ENUM ('SENT', 'ACCEPTED', 'DECLINED', 'EXPIRED', 'WITHDRAWN')""",
    """CREATE TYPE pledge_source AS ENUM ('SAVINGS', 'SHARE_CAPITAL')""",
    """CREATE TYPE peer_guarantee_status AS ENUM ('PENDING_SIGNATURE', 'LOCKED', 'PARTIALLY_RELEASED', 'RELEASED', 'APPLIED_TO_DEFAULT', 'CANCELLED')""",
    """CREATE TYPE repayment_schedule_status AS ENUM ('ACTIVE', 'SUPERSEDED')""",
    """CREATE TYPE repayment_schedule_origin AS ENUM ('ORIGINATION', 'RESTRUCTURE', 'HARDSHIP_RESCHEDULE')""",
    """CREATE TYPE repayment_installment_status AS ENUM ('SCHEDULED', 'DUE', 'PAID', 'PARTIALLY_PAID', 'MISSED', 'RESCHEDULED', 'WAIVED')""",
    """CREATE TYPE payout_order_mode AS ENUM ('AGREED', 'RANDOMIZED')""",
    """CREATE TYPE pooled_loan_circle_status AS ENUM ('FORMING', 'ACTIVE', 'COMPLETED', 'HALTED')""",
    """CREATE TYPE participant_payout_status AS ENUM ('WAITING', 'PAID')""",
    """CREATE TYPE collections_trigger AS ENUM ('EARLY_WARNING', 'FAILED_COLLECTION', 'DELINQUENT_MILESTONE', 'HARDSHIP_REQUEST')""",
    """CREATE TYPE collections_case_status AS ENUM ('OPEN', 'IN_PROGRESS', 'RESOLVED_CURED', 'RESOLVED_RESCHEDULED', 'ESCALATED_DEFAULT', 'CLOSED')""",
    """CREATE TYPE signed_document_type AS ENUM ('LOAN_AGREEMENT', 'GUARANTEE_PLEDGE_AGREEMENT', 'MEMBERSHIP_CONFIRMATION', 'OTHER_AGREEMENT')""",
    """CREATE TYPE signed_document_status AS ENUM ('DRAFT', 'SENT', 'SIGNED', 'DECLINED', 'VOIDED', 'EXPIRED')""",
    """CREATE TYPE membership_status AS ENUM ('PENDING_KYC', 'PENDING_PAYMENT', 'ACTIVE', 'SUSPENDED', 'CLOSED')""",
    """CREATE TYPE share_class AS ENUM ('MEMBERSHIP', 'REINVESTED_PATRONAGE')""",
    """CREATE TYPE share_status AS ENUM ('MEMBER', 'REDEEMED')""",
    """CREATE TYPE notification_category AS ENUM ('PAYMENTS', 'CARDS', 'GROUP_POTS', 'GOVERNANCE', 'LENDING', 'GUARANTEES', 'DIVIDENDS', 'PROJECTS', 'SECURITY_REGULATORY', 'SYSTEM')""",
    """CREATE TYPE notification_channel AS ENUM ('PUSH', 'EMAIL', 'SMS', 'IN_APP')""",
    """CREATE TYPE verification_method AS ENUM ('PLAID_INSTANT', 'MICRO_DEPOSIT')""",
    """CREATE TYPE external_account_link_status AS ENUM ('PENDING_VERIFICATION', 'VERIFIED', 'RELINK_REQUIRED', 'REMOVED')""",
    """CREATE TYPE payee_type AS ENUM ('INTERNAL_MEMBER', 'EXTERNAL_ACCOUNT', 'BILLER')""",
    """CREATE TYPE payee_status AS ENUM ('ACTIVE', 'ARCHIVED')""",
    """CREATE TYPE payment_rail AS ENUM ('INTERNAL_P2P', 'ACH', 'WIRE', 'RTP')""",
    """CREATE TYPE scheduled_payment_status AS ENUM ('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED', 'FAILED')""",
    """CREATE TYPE split_mode AS ENUM ('EQUAL', 'CUSTOM')""",
    """CREATE TYPE payment_request_status AS ENUM ('OPEN', 'PARTIALLY_SETTLED', 'SETTLED', 'CANCELLED', 'EXPIRED')""",
    """CREATE TYPE payment_request_share_status AS ENUM ('PENDING', 'PAID', 'DECLINED', 'CANCELLED')""",
    """CREATE TYPE roundup_destination_type AS ENUM ('SAVINGS_GOAL', 'COMMUNITY_PROJECT')""",
    """CREATE TYPE roundup_capture_status AS ENUM ('ACCUMULATED', 'TRANSFERRED', 'SKIPPED_INSUFFICIENT_FUNDS', 'SKIPPED_CAP')""",
    """CREATE TABLE staff_user (
	staff_idp_id VARCHAR(128) NOT NULL, 
	display_name VARCHAR(200) NOT NULL, 
	email VARCHAR(320) NOT NULL, 
	roles staff_role[] NOT NULL, 
	status staff_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_staff_user PRIMARY KEY (id), 
	CONSTRAINT uq_staff_user_staff_idp_id UNIQUE (staff_idp_id), 
	CONSTRAINT uq_staff_user_email UNIQUE (email)
)""",
    """CREATE TABLE audit_log_entry (
	sequence BIGINT NOT NULL, 
	prev_hash VARCHAR(128), 
	entry_hash VARCHAR(128) NOT NULL, 
	actor JSONB NOT NULL, 
	action VARCHAR(128) NOT NULL, 
	subject JSONB NOT NULL, 
	before JSONB, 
	after JSONB, 
	occurred_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	correlation_id UUID NOT NULL, 
	id UUID NOT NULL, 
	CONSTRAINT pk_audit_log_entry PRIMARY KEY (id)
)""",
    """CREATE TABLE regulatory_report_run (
	report_key VARCHAR(128) NOT NULL, 
	as_of TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	output_ref VARCHAR(512), 
	schedule_ref VARCHAR(256), 
	threshold_breaches JSONB, 
	status regulatory_report_status NOT NULL, 
	submission_log JSONB, 
	run_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_regulatory_report_run PRIMARY KEY (id)
)""",
    """CREATE TABLE capital_allocation_snapshot (
	as_of TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	total_managed_funds BIGINT, 
	allocations JSONB NOT NULL, 
	spotlights JSONB, 
	source_ledger_hash VARCHAR(128) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_capital_allocation_snapshot PRIMARY KEY (id), 
	CONSTRAINT uq_capital_allocation_snapshot_as_of UNIQUE (as_of)
)""",
    """CREATE TABLE transaction (
	idempotency_key VARCHAR(128), 
	type VARCHAR(64) NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	amount BIGINT, 
	external_ref VARCHAR(128), 
	settled_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_transaction PRIMARY KEY (id), 
	CONSTRAINT uq_transaction_idempotency_key UNIQUE (idempotency_key)
)""",
    """CREATE TABLE signed_document (
	document_type signed_document_type NOT NULL, 
	subject_refs JSONB, 
	provider_envelope_ref VARCHAR(255), 
	signer_member_ids UUID[], 
	document_sha256 VARCHAR(64), 
	storage_ref VARCHAR(1024), 
	status signed_document_status NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_signed_document PRIMARY KEY (id)
)""",
    """CREATE TABLE member (
	ovog VARCHAR(120), 
	etsgiin_ner VARCHAR(120) NOT NULL, 
	ner VARCHAR(120) NOT NULL, 
	mrz_name_latin VARCHAR(120), 
	registration_number VARCHAR(10), 
	membership_status membership_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_member PRIMARY KEY (id), 
	CONSTRAINT uq_member_registration_number UNIQUE (registration_number)
)""",
    """CREATE TABLE notification_event_type (
	event_key VARCHAR(128) NOT NULL, 
	category notification_category NOT NULL, 
	default_channels notification_channel[] NOT NULL, 
	template_refs JSONB NOT NULL, 
	deep_link_pattern VARCHAR(256), 
	suppressible BOOLEAN NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_notification_event_type PRIMARY KEY (id), 
	CONSTRAINT uq_notification_event_type_event_key UNIQUE (event_key)
)""",
    """CREATE TABLE maker_checker_approval (
	action_type VARCHAR(64) NOT NULL, 
	subject_ref JSONB NOT NULL, 
	proposed_change JSONB NOT NULL, 
	maker_staff_id UUID NOT NULL, 
	checker_staff_id UUID, 
	status approval_status NOT NULL, 
	maker_note VARCHAR(2000), 
	checker_note VARCHAR(2000), 
	decided_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_maker_checker_approval PRIMARY KEY (id), 
	CONSTRAINT fk_maker_checker_approval_maker_staff_id_staff_user FOREIGN KEY(maker_staff_id) REFERENCES staff_user (id), 
	CONSTRAINT fk_maker_checker_approval_checker_staff_id_staff_user FOREIGN KEY(checker_staff_id) REFERENCES staff_user (id)
)""",
    """CREATE TABLE compliance_case (
	case_type compliance_case_type NOT NULL, 
	subject_member_id UUID, 
	source_refs JSONB NOT NULL, 
	alert_details JSONB, 
	sar_package JSONB, 
	assigned_staff_id UUID, 
	sla_due_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	priority compliance_case_priority NOT NULL, 
	status compliance_case_status NOT NULL, 
	opened_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_compliance_case PRIMARY KEY (id), 
	CONSTRAINT fk_compliance_case_subject_member_id_member FOREIGN KEY(subject_member_id) REFERENCES member (id), 
	CONSTRAINT fk_compliance_case_assigned_staff_id_staff_user FOREIGN KEY(assigned_staff_id) REFERENCES staff_user (id)
)""",
    """CREATE TABLE data_subject_request (
	member_id UUID NOT NULL, 
	request_type data_subject_request_type NOT NULL, 
	status data_subject_request_status NOT NULL, 
	deadline_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	fulfilment_package_ref VARCHAR(512), 
	retention_overrides JSONB, 
	received_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_data_subject_request PRIMARY KEY (id), 
	CONSTRAINT fk_data_subject_request_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE patronage_factor_record (
	member_id UUID NOT NULL, 
	fiscal_year INTEGER NOT NULL, 
	period patronage_period NOT NULL, 
	period_key VARCHAR(16) NOT NULL, 
	avg_savings_balance BIGINT, 
	transaction_volume BIGINT, 
	loan_repayment_performance_score INTEGER, 
	governance_participation_score INTEGER, 
	computed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_patronage_factor_record PRIMARY KEY (id), 
	CONSTRAINT fk_patronage_factor_record_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE community_project (
	submitter_member_id UUID, 
	submitter_org JSONB, 
	title VARCHAR(120) NOT NULL, 
	goals TEXT NOT NULL, 
	budget JSONB, 
	timeline JSONB, 
	impact_description TEXT NOT NULL, 
	documents JSONB, 
	funding_goal BIGINT, 
	deadline TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	all_or_nothing BOOLEAN NOT NULL, 
	amount_backed BIGINT, 
	amount_matched BIGINT, 
	amount_disbursed BIGINT, 
	status community_project_status NOT NULL, 
	review JSONB, 
	updates JSONB, 
	impact_report JSONB, 
	published_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_community_project PRIMARY KEY (id), 
	CONSTRAINT fk_community_project_submitter_member_id_member FOREIGN KEY(submitter_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE proxy_delegation (
	delegator_member_id UUID NOT NULL, 
	delegate_member_id UUID NOT NULL, 
	proposal_category proposal_category, 
	ballot_type_scope ballot_type, 
	status proxy_delegation_status NOT NULL, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_proxy_delegation PRIMARY KEY (id), 
	CONSTRAINT fk_proxy_delegation_delegator_member_id_member FOREIGN KEY(delegator_member_id) REFERENCES member (id), 
	CONSTRAINT fk_proxy_delegation_delegate_member_id_member FOREIGN KEY(delegate_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE kyc_submission (
	member_id UUID NOT NULL, 
	persona_inquiry_id VARCHAR(128) NOT NULL, 
	document_type kyc_document_type NOT NULL, 
	ocr_extracted_fields JSON NOT NULL, 
	screening_result kyc_screening_result NOT NULL, 
	result kyc_result NOT NULL, 
	result_reasons JSON NOT NULL, 
	evidence_refs JSON NOT NULL, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_kyc_submission PRIMARY KEY (id), 
	CONSTRAINT fk_kyc_submission_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT uq_kyc_submission_persona_inquiry_id UNIQUE (persona_inquiry_id)
)""",
    """CREATE TABLE device_binding (
	member_id UUID NOT NULL, 
	device_fingerprint VARCHAR(255) NOT NULL, 
	platform device_platform NOT NULL, 
	push_token VARCHAR(255), 
	biometric_enabled BOOLEAN NOT NULL, 
	status device_status NOT NULL, 
	bound_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	last_seen_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_device_binding PRIMARY KEY (id), 
	CONSTRAINT fk_device_binding_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE consent_record (
	member_id UUID NOT NULL, 
	consent_type consent_type NOT NULL, 
	action consent_action NOT NULL, 
	version VARCHAR(64) NOT NULL, 
	recorded_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	channel VARCHAR(64) NOT NULL, 
	id UUID NOT NULL, 
	CONSTRAINT pk_consent_record PRIMARY KEY (id), 
	CONSTRAINT fk_consent_record_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE account (
	owner_member_id UUID, 
	account_number VARCHAR(64) NOT NULL, 
	account_type account_type NOT NULL, 
	balance BIGINT, 
	available_balance BIGINT, 
	status VARCHAR(16) NOT NULL, 
	opened_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_account PRIMARY KEY (id), 
	CONSTRAINT fk_account_owner_member_id_member FOREIGN KEY(owner_member_id) REFERENCES member (id), 
	CONSTRAINT uq_account_account_number UNIQUE (account_number)
)""",
    """CREATE TABLE loan_circle (
	borrower_member_id UUID NOT NULL, 
	loan_application_id UUID NOT NULL, 
	status loan_circle_status NOT NULL, 
	formed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_loan_circle PRIMARY KEY (id), 
	CONSTRAINT fk_loan_circle_borrower_member_id_member FOREIGN KEY(borrower_member_id) REFERENCES member (id), 
	CONSTRAINT uq_loan_circle_loan_application_id UNIQUE (loan_application_id)
)""",
    """CREATE TABLE pooled_loan_circle (
	name VARCHAR(80) NOT NULL, 
	creator_member_id UUID NOT NULL, 
	contribution_amount BIGINT, 
	cycle_count INTEGER NOT NULL, 
	current_cycle INTEGER NOT NULL, 
	collection_day_of_month INTEGER NOT NULL, 
	payout_order_mode payout_order_mode NOT NULL, 
	backstop_rules JSONB, 
	status pooled_loan_circle_status NOT NULL, 
	activated_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_pooled_loan_circle PRIMARY KEY (id), 
	CONSTRAINT fk_pooled_loan_circle_creator_member_id_member FOREIGN KEY(creator_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE membership_share (
	member_id UUID NOT NULL, 
	certificate_number VARCHAR(64) NOT NULL, 
	par_value BIGINT, 
	share_class share_class NOT NULL, 
	status share_status NOT NULL, 
	issued_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	redeemed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_membership_share PRIMARY KEY (id), 
	CONSTRAINT fk_membership_share_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT uq_membership_share_certificate_number UNIQUE (certificate_number)
)""",
    """CREATE TABLE notification (
	member_id UUID NOT NULL, 
	event_type_id UUID NOT NULL, 
	payload JSONB NOT NULL, 
	deep_link VARCHAR(256), 
	channel_dispatches JSONB NOT NULL, 
	read_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_notification PRIMARY KEY (id), 
	CONSTRAINT fk_notification_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_notification_event_type_id_notification_event_type FOREIGN KEY(event_type_id) REFERENCES notification_event_type (id)
)""",
    """CREATE TABLE notification_preference (
	member_id UUID NOT NULL, 
	category notification_category NOT NULL, 
	channel notification_channel NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	quiet_hours JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_notification_preference PRIMARY KEY (id), 
	CONSTRAINT uq_notification_preference_member_id UNIQUE (member_id, category, channel), 
	CONSTRAINT fk_notification_preference_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE external_account_link (
	member_id UUID NOT NULL, 
	plaid_item_ref VARCHAR(255), 
	processor_token_ref VARCHAR(255), 
	institution_name VARCHAR(255), 
	account_mask VARCHAR(32), 
	account_subtype VARCHAR(64), 
	verification_method verification_method NOT NULL, 
	status external_account_link_status NOT NULL, 
	open_banking_consent BOOLEAN NOT NULL, 
	verified_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_external_account_link PRIMARY KEY (id), 
	CONSTRAINT fk_external_account_link_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE payee (
	member_id UUID NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	payee_type payee_type NOT NULL, 
	target_ref VARCHAR(255), 
	status payee_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_payee PRIMARY KEY (id), 
	CONSTRAINT fk_payee_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE payment_request (
	requester_member_id UUID NOT NULL, 
	origin_transaction_id UUID, 
	split_mode split_mode NOT NULL, 
	total_amount BIGINT, 
	reminders_sent INTEGER NOT NULL, 
	status payment_request_status NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_payment_request PRIMARY KEY (id), 
	CONSTRAINT fk_payment_request_requester_member_id_member FOREIGN KEY(requester_member_id) REFERENCES member (id), 
	CONSTRAINT fk_payment_request_origin_transaction_id_transaction FOREIGN KEY(origin_transaction_id) REFERENCES transaction (id)
)""",
    """CREATE TABLE roundup_capture (
	member_id UUID NOT NULL, 
	card_transaction_id UUID NOT NULL, 
	base_amount BIGINT, 
	roundup_amount BIGINT, 
	multiplier_applied INTEGER NOT NULL, 
	capped BOOLEAN NOT NULL, 
	status roundup_capture_status NOT NULL, 
	transfer_transaction_id UUID, 
	captured_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_roundup_capture PRIMARY KEY (id), 
	CONSTRAINT fk_roundup_capture_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT uq_roundup_capture_card_transaction_id UNIQUE (card_transaction_id), 
	CONSTRAINT fk_roundup_capture_card_transaction_id_transaction FOREIGN KEY(card_transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_roundup_capture_transfer_transaction_id_transaction FOREIGN KEY(transfer_transaction_id) REFERENCES transaction (id)
)""",
    """CREATE TABLE card (
	member_id UUID NOT NULL, 
	funding_account_id UUID NOT NULL, 
	card_type card_type NOT NULL, 
	issuer_card_ref VARCHAR(255) NOT NULL, 
	masked_pan VARCHAR(32), 
	expiry_month INTEGER, 
	expiry_year INTEGER, 
	embossed_name VARCHAR(120), 
	status card_status NOT NULL, 
	fulfilment JSONB, 
	controls JSONB, 
	wallet_tokens JSONB, 
	pin_set BOOLEAN NOT NULL, 
	activated_at TIMESTAMP WITHOUT TIME ZONE, 
	terminated_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_card PRIMARY KEY (id), 
	CONSTRAINT fk_card_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_card_funding_account_id_account FOREIGN KEY(funding_account_id) REFERENCES account (id), 
	CONSTRAINT uq_card_issuer_card_ref UNIQUE (issuer_card_ref)
)""",
    """CREATE TABLE savings_goal (
	member_id UUID NOT NULL, 
	savings_account_id UUID NOT NULL, 
	name VARCHAR(60) NOT NULL, 
	emoji_or_image_ref VARCHAR(255), 
	target_amount BIGINT, 
	current_amount BIGINT, 
	target_date DATE, 
	auto_transfer JSON NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_savings_goal PRIMARY KEY (id), 
	CONSTRAINT fk_savings_goal_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_savings_goal_savings_account_id_account FOREIGN KEY(savings_account_id) REFERENCES account (id)
)""",
    """CREATE TABLE group_pot (
	account_id UUID NOT NULL, 
	creator_member_id UUID NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	purpose VARCHAR(280) NOT NULL, 
	approval_threshold_m INTEGER NOT NULL, 
	status group_pot_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_group_pot PRIMARY KEY (id), 
	CONSTRAINT uq_group_pot_account_id UNIQUE (account_id), 
	CONSTRAINT fk_group_pot_account_id_account FOREIGN KEY(account_id) REFERENCES account (id), 
	CONSTRAINT fk_group_pot_creator_member_id_member FOREIGN KEY(creator_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE backing (
	project_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	amount BIGINT, 
	recurring JSONB, 
	source backing_source NOT NULL, 
	transaction_id UUID NOT NULL, 
	refund_transaction_id UUID, 
	status backing_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_backing PRIMARY KEY (id), 
	CONSTRAINT fk_backing_project_id_community_project FOREIGN KEY(project_id) REFERENCES community_project (id), 
	CONSTRAINT fk_backing_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_backing_transaction_id_transaction FOREIGN KEY(transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_backing_refund_transaction_id_transaction FOREIGN KEY(refund_transaction_id) REFERENCES transaction (id)
)""",
    """CREATE TABLE proposal (
	author_member_id UUID NOT NULL, 
	title VARCHAR(150) NOT NULL, 
	summary VARCHAR(500) NOT NULL, 
	body TEXT NOT NULL, 
	category proposal_category NOT NULL, 
	status proposal_status NOT NULL, 
	rejection_reason VARCHAR(64), 
	cosignature_threshold INTEGER NOT NULL, 
	cosignature_count INTEGER NOT NULL, 
	ballot_id UUID, 
	linked_project_id UUID, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_proposal PRIMARY KEY (id), 
	CONSTRAINT fk_proposal_author_member_id_member FOREIGN KEY(author_member_id) REFERENCES member (id), 
	CONSTRAINT fk_proposal_linked_project_id_community_project FOREIGN KEY(linked_project_id) REFERENCES community_project (id)
)""",
    """CREATE TABLE ledger_entry (
	transaction_id UUID NOT NULL, 
	account_id UUID NOT NULL, 
	direction ledger_direction NOT NULL, 
	amount BIGINT, 
	entry_type VARCHAR(64) NOT NULL, 
	sequence BIGINT NOT NULL, 
	posted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	CONSTRAINT pk_ledger_entry PRIMARY KEY (id), 
	CONSTRAINT fk_ledger_entry_transaction_id_transaction FOREIGN KEY(transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_ledger_entry_account_id_account FOREIGN KEY(account_id) REFERENCES account (id)
)""",
    """CREATE TABLE loan_circle_invitation (
	loan_circle_id UUID NOT NULL, 
	invitee_member_id UUID NOT NULL, 
	addressed_via recipient_identifier_type NOT NULL, 
	disclosure JSONB, 
	status loan_circle_invitation_status NOT NULL, 
	sent_at TIMESTAMP WITHOUT TIME ZONE, 
	responded_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_loan_circle_invitation PRIMARY KEY (id), 
	CONSTRAINT loan_circle_invitation_circle_invitee UNIQUE (loan_circle_id, invitee_member_id), 
	CONSTRAINT fk_loan_circle_invitation_loan_circle_id_loan_circle FOREIGN KEY(loan_circle_id) REFERENCES loan_circle (id), 
	CONSTRAINT fk_loan_circle_invitation_invitee_member_id_member FOREIGN KEY(invitee_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE pooled_loan_circle_participant (
	pooled_loan_circle_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	payout_position INTEGER NOT NULL, 
	payout_status participant_payout_status NOT NULL, 
	funding_account_id UUID NOT NULL, 
	missed_contributions INTEGER NOT NULL, 
	joined_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_pooled_loan_circle_participant PRIMARY KEY (id), 
	CONSTRAINT pooled_participant_circle_member UNIQUE (pooled_loan_circle_id, member_id), 
	CONSTRAINT pooled_participant_circle_position UNIQUE (pooled_loan_circle_id, payout_position), 
	CONSTRAINT fk_pooled_loan_circle_participant_pooled_loan_circle_id_2228 FOREIGN KEY(pooled_loan_circle_id) REFERENCES pooled_loan_circle (id), 
	CONSTRAINT fk_pooled_loan_circle_participant_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_pooled_loan_circle_participant_funding_account_id_account FOREIGN KEY(funding_account_id) REFERENCES account (id)
)""",
    """CREATE TABLE scheduled_payment (
	member_id UUID NOT NULL, 
	source_account_id UUID NOT NULL, 
	payee_id UUID NOT NULL, 
	amount BIGINT, 
	rail payment_rail NOT NULL, 
	schedule JSONB, 
	retry_policy JSONB, 
	next_run_at TIMESTAMP WITHOUT TIME ZONE, 
	status scheduled_payment_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_scheduled_payment PRIMARY KEY (id), 
	CONSTRAINT fk_scheduled_payment_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_scheduled_payment_source_account_id_account FOREIGN KEY(source_account_id) REFERENCES account (id), 
	CONSTRAINT fk_scheduled_payment_payee_id_payee FOREIGN KEY(payee_id) REFERENCES payee (id)
)""",
    """CREATE TABLE payment_request_share (
	payment_request_id UUID NOT NULL, 
	debtor_identifier_type recipient_identifier_type NOT NULL, 
	debtor_identifier VARCHAR(255) NOT NULL, 
	amount BIGINT, 
	status payment_request_share_status NOT NULL, 
	settled_transaction_id UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_payment_request_share PRIMARY KEY (id), 
	CONSTRAINT fk_payment_request_share_payment_request_id_payment_request FOREIGN KEY(payment_request_id) REFERENCES payment_request (id), 
	CONSTRAINT fk_payment_request_share_settled_transaction_id_transaction FOREIGN KEY(settled_transaction_id) REFERENCES transaction (id)
)""",
    """CREATE TABLE group_pot_member (
	group_pot_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	role group_pot_member_role NOT NULL, 
	invited_via recipient_identifier_type NOT NULL, 
	status group_pot_member_status NOT NULL, 
	invited_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	responded_at TIMESTAMP WITHOUT TIME ZONE, 
	total_contributed BIGINT, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_group_pot_member PRIMARY KEY (id), 
	CONSTRAINT uq_group_pot_member_group_pot_id UNIQUE (group_pot_id, member_id), 
	CONSTRAINT fk_group_pot_member_group_pot_id_group_pot FOREIGN KEY(group_pot_id) REFERENCES group_pot (id), 
	CONSTRAINT fk_group_pot_member_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE group_pot_approval_request (
	group_pot_id UUID NOT NULL, 
	transaction_id UUID NOT NULL, 
	initiated_by_member_id UUID NOT NULL, 
	amount BIGINT, 
	recipient JSON NOT NULL, 
	purpose VARCHAR(280) NOT NULL, 
	required_approvals INTEGER NOT NULL, 
	status group_pot_approval_status NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_group_pot_approval_request PRIMARY KEY (id), 
	CONSTRAINT fk_group_pot_approval_request_group_pot_id_group_pot FOREIGN KEY(group_pot_id) REFERENCES group_pot (id), 
	CONSTRAINT fk_group_pot_approval_request_transaction_id_transaction FOREIGN KEY(transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_group_pot_approval_request_initiated_by_member_id_member FOREIGN KEY(initiated_by_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE proposal_cosignature (
	proposal_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	signed_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_proposal_cosignature PRIMARY KEY (id), 
	CONSTRAINT uq_proposal_cosignature_proposal_id UNIQUE (proposal_id, member_id), 
	CONSTRAINT fk_proposal_cosignature_proposal_id_proposal FOREIGN KEY(proposal_id) REFERENCES proposal (id), 
	CONSTRAINT fk_proposal_cosignature_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE proposal_comment (
	proposal_id UUID NOT NULL, 
	parent_comment_id UUID, 
	author_member_id UUID NOT NULL, 
	body TEXT NOT NULL, 
	status proposal_comment_status NOT NULL, 
	moderation_reason VARCHAR(255), 
	report_count INTEGER NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_proposal_comment PRIMARY KEY (id), 
	CONSTRAINT fk_proposal_comment_proposal_id_proposal FOREIGN KEY(proposal_id) REFERENCES proposal (id), 
	CONSTRAINT fk_proposal_comment_parent_comment_id_proposal_comment FOREIGN KEY(parent_comment_id) REFERENCES proposal_comment (id), 
	CONSTRAINT fk_proposal_comment_author_member_id_member FOREIGN KEY(author_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE ballot (
	ballot_type ballot_type NOT NULL, 
	proposal_id UUID, 
	title VARCHAR(255) NOT NULL, 
	opens_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	closes_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	context_pack JSONB, 
	quorum_rule JSONB, 
	seats INTEGER, 
	eligibility_snapshot_id UUID, 
	status ballot_status NOT NULL, 
	results JSONB, 
	certified_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_ballot PRIMARY KEY (id), 
	CONSTRAINT fk_ballot_proposal_id_proposal FOREIGN KEY(proposal_id) REFERENCES proposal (id)
)""",
    """CREATE TABLE roundup_config (
	member_id UUID NOT NULL, 
	enabled BOOLEAN NOT NULL, 
	destination_type roundup_destination_type NOT NULL, 
	savings_goal_id UUID, 
	project_id UUID, 
	multiplier INTEGER NOT NULL, 
	monthly_cap BIGINT, 
	accumulated_pending BIGINT, 
	batch_threshold BIGINT, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_roundup_config PRIMARY KEY (id), 
	CONSTRAINT uq_roundup_config_member_id UNIQUE (member_id), 
	CONSTRAINT fk_roundup_config_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_roundup_config_savings_goal_id_savings_goal FOREIGN KEY(savings_goal_id) REFERENCES savings_goal (id), 
	CONSTRAINT fk_roundup_config_project_id_community_project FOREIGN KEY(project_id) REFERENCES community_project (id)
)""",
    """CREATE TABLE configuration_parameter (
	key VARCHAR(128) NOT NULL, 
	value JSONB NOT NULL, 
	version INTEGER NOT NULL, 
	effective_from TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	effective_to TIMESTAMP WITHOUT TIME ZONE, 
	approval_id UUID NOT NULL, 
	governing_ballot_id UUID, 
	created_by UUID NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_configuration_parameter PRIMARY KEY (id), 
	CONSTRAINT uq_configuration_parameter_key UNIQUE (key, version), 
	CONSTRAINT fk_configuration_parameter_approval_id_maker_checker_approval FOREIGN KEY(approval_id) REFERENCES maker_checker_approval (id), 
	CONSTRAINT fk_configuration_parameter_governing_ballot_id_ballot FOREIGN KEY(governing_ballot_id) REFERENCES ballot (id), 
	CONSTRAINT fk_configuration_parameter_created_by_staff_user FOREIGN KEY(created_by) REFERENCES staff_user (id)
)""",
    """CREATE TABLE group_pot_approval_decision (
	approval_request_id UUID NOT NULL, 
	approver_member_id UUID NOT NULL, 
	decision group_pot_approval_decision NOT NULL, 
	decided_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	auth_context JSON NOT NULL, 
	id UUID NOT NULL, 
	CONSTRAINT pk_group_pot_approval_decision PRIMARY KEY (id), 
	CONSTRAINT uq_group_pot_approval_decision_approval_request_id UNIQUE (approval_request_id, approver_member_id), 
	CONSTRAINT fk_group_pot_approval_decision_approval_request_id_grou_cddd FOREIGN KEY(approval_request_id) REFERENCES group_pot_approval_request (id), 
	CONSTRAINT fk_group_pot_approval_decision_approver_member_id_member FOREIGN KEY(approver_member_id) REFERENCES member (id)
)""",
    """CREATE TABLE eligibility_snapshot (
	ballot_id UUID NOT NULL, 
	captured_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	eligible_member_count INTEGER NOT NULL, 
	snapshot_ref VARCHAR(255) NOT NULL, 
	registry_hash VARCHAR(255) NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_eligibility_snapshot PRIMARY KEY (id), 
	CONSTRAINT uq_eligibility_snapshot_ballot_id UNIQUE (ballot_id), 
	CONSTRAINT fk_eligibility_snapshot_ballot_id_ballot FOREIGN KEY(ballot_id) REFERENCES ballot (id)
)""",
    """CREATE TABLE vote_participation (
	ballot_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	via_delegation BOOLEAN NOT NULL, 
	delegate_member_id UUID, 
	superseded_by_direct_vote BOOLEAN NOT NULL, 
	receipt_hash VARCHAR(255) NOT NULL, 
	auth_context JSONB, 
	voted_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_vote_participation PRIMARY KEY (id), 
	CONSTRAINT uq_vote_participation_ballot_id UNIQUE (ballot_id, member_id), 
	CONSTRAINT fk_vote_participation_ballot_id_ballot FOREIGN KEY(ballot_id) REFERENCES ballot (id), 
	CONSTRAINT fk_vote_participation_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_vote_participation_delegate_member_id_member FOREIGN KEY(delegate_member_id) REFERENCES member (id), 
	CONSTRAINT uq_vote_participation_receipt_hash UNIQUE (receipt_hash)
)""",
    """CREATE TABLE vote_record (
	ballot_id UUID NOT NULL, 
	choice vote_choice, 
	candidate_selections UUID[], 
	validity_proof VARCHAR(255) NOT NULL, 
	voided BOOLEAN NOT NULL, 
	cast_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	id UUID NOT NULL, 
	CONSTRAINT pk_vote_record PRIMARY KEY (id), 
	CONSTRAINT fk_vote_record_ballot_id_ballot FOREIGN KEY(ballot_id) REFERENCES ballot (id)
)""",
    """CREATE TABLE election_candidate (
	ballot_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	statement TEXT NOT NULL, 
	profile_ref VARCHAR(255), 
	votes_received INTEGER, 
	elected BOOLEAN NOT NULL, 
	term JSONB, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_election_candidate PRIMARY KEY (id), 
	CONSTRAINT uq_election_candidate_ballot_id UNIQUE (ballot_id, member_id), 
	CONSTRAINT fk_election_candidate_ballot_id_ballot FOREIGN KEY(ballot_id) REFERENCES ballot (id), 
	CONSTRAINT fk_election_candidate_member_id_member FOREIGN KEY(member_id) REFERENCES member (id)
)""",
    """CREATE TABLE dividend_declaration (
	fiscal_year INTEGER NOT NULL, 
	ratified_surplus BIGINT, 
	agm_record_ref VARCHAR(255) NOT NULL, 
	distributable_pool BIGINT, 
	community_grant_allocation BIGINT, 
	factor_weights JSONB, 
	factor_weights_config_ref UUID, 
	status dividend_declaration_status NOT NULL, 
	calculation_run_ref VARCHAR(255), 
	reconciliation_report_ref VARCHAR(255), 
	declared_at TIMESTAMP WITHOUT TIME ZONE, 
	approved_at TIMESTAMP WITHOUT TIME ZONE, 
	executed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_dividend_declaration PRIMARY KEY (id), 
	CONSTRAINT uq_dividend_declaration_fiscal_year UNIQUE (fiscal_year), 
	CONSTRAINT fk_dividend_declaration_factor_weights_config_ref_confi_9a68 FOREIGN KEY(factor_weights_config_ref) REFERENCES configuration_parameter (id)
)""",
    """CREATE TABLE loan_product (
	name VARCHAR(120) NOT NULL, 
	product_type loan_product_type NOT NULL, 
	amount_min BIGINT, 
	amount_max BIGINT, 
	term_options_months INTEGER[], 
	base_rate_apr_bps INTEGER, 
	schedule_types_allowed schedule_type[], 
	status loan_product_status NOT NULL, 
	config_version_ref UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_loan_product PRIMARY KEY (id), 
	CONSTRAINT fk_loan_product_config_version_ref_configuration_parameter FOREIGN KEY(config_version_ref) REFERENCES configuration_parameter (id)
)""",
    """CREATE TABLE dividend_allocation (
	dividend_declaration_id UUID NOT NULL, 
	member_id UUID NOT NULL, 
	entitlement_amount BIGINT, 
	explainability JSONB, 
	payout_destination payout_destination NOT NULL, 
	payout_transaction_id UUID, 
	reinvested_share_id UUID, 
	status dividend_allocation_status NOT NULL, 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	statement_ref VARCHAR(255), 
	tax_document_ref VARCHAR(255), 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_dividend_allocation PRIMARY KEY (id), 
	CONSTRAINT fk_dividend_allocation_dividend_declaration_id_dividend_f192 FOREIGN KEY(dividend_declaration_id) REFERENCES dividend_declaration (id), 
	CONSTRAINT fk_dividend_allocation_member_id_member FOREIGN KEY(member_id) REFERENCES member (id), 
	CONSTRAINT fk_dividend_allocation_payout_transaction_id_transaction FOREIGN KEY(payout_transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_dividend_allocation_reinvested_share_id_membership_share FOREIGN KEY(reinvested_share_id) REFERENCES membership_share (id)
)""",
    """CREATE TABLE community_grant_pool (
	fiscal_year INTEGER NOT NULL, 
	funded_from_declaration_id UUID NOT NULL, 
	pool_account_id UUID NOT NULL, 
	budget BIGINT, 
	committed BIGINT, 
	disbursed BIGINT, 
	status grant_pool_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_community_grant_pool PRIMARY KEY (id), 
	CONSTRAINT uq_community_grant_pool_fiscal_year UNIQUE (fiscal_year), 
	CONSTRAINT fk_community_grant_pool_funded_from_declaration_id_divi_dbad FOREIGN KEY(funded_from_declaration_id) REFERENCES dividend_declaration (id), 
	CONSTRAINT fk_community_grant_pool_pool_account_id_account FOREIGN KEY(pool_account_id) REFERENCES account (id)
)""",
    """CREATE TABLE loan_application (
	applicant_member_id UUID NOT NULL, 
	loan_product_id UUID NOT NULL, 
	requested_amount BIGINT, 
	requested_term_months INTEGER NOT NULL, 
	purpose VARCHAR(500), 
	affordability_inputs JSONB, 
	status loan_status NOT NULL, 
	decision JSONB, 
	offer JSONB, 
	loan_circle_id UUID, 
	referral_case_id UUID, 
	submitted_at TIMESTAMP WITHOUT TIME ZONE, 
	decided_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_loan_application PRIMARY KEY (id), 
	CONSTRAINT fk_loan_application_applicant_member_id_member FOREIGN KEY(applicant_member_id) REFERENCES member (id), 
	CONSTRAINT fk_loan_application_loan_product_id_loan_product FOREIGN KEY(loan_product_id) REFERENCES loan_product (id), 
	CONSTRAINT fk_loan_application_loan_circle_id_loan_circle FOREIGN KEY(loan_circle_id) REFERENCES loan_circle (id), 
	CONSTRAINT fk_loan_application_referral_case_id_compliance_case FOREIGN KEY(referral_case_id) REFERENCES compliance_case (id)
)""",
    """CREATE TABLE surplus_match (
	pool_id UUID NOT NULL, 
	project_id UUID NOT NULL, 
	match_ratio_bps INTEGER NOT NULL, 
	project_cap BIGINT, 
	accrued_amount BIGINT, 
	release_ballot_id UUID, 
	released_amount BIGINT, 
	release_transaction_ids UUID[], 
	status surplus_match_status NOT NULL, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_surplus_match PRIMARY KEY (id), 
	CONSTRAINT uq_surplus_match_pool_id UNIQUE (pool_id, project_id), 
	CONSTRAINT fk_surplus_match_pool_id_community_grant_pool FOREIGN KEY(pool_id) REFERENCES community_grant_pool (id), 
	CONSTRAINT fk_surplus_match_project_id_community_project FOREIGN KEY(project_id) REFERENCES community_project (id), 
	CONSTRAINT fk_surplus_match_release_ballot_id_ballot FOREIGN KEY(release_ballot_id) REFERENCES ballot (id)
)""",
    """CREATE TABLE loan (
	loan_application_id UUID NOT NULL, 
	borrower_member_id UUID NOT NULL, 
	loan_product_id UUID NOT NULL, 
	loan_circle_id UUID, 
	principal_amount BIGINT, 
	outstanding_principal BIGINT, 
	accrued_interest BIGINT, 
	apr_bps INTEGER, 
	disbursement_transaction_id UUID, 
	disbursement_account_id UUID, 
	status loan_status NOT NULL, 
	autopay JSONB, 
	days_past_due INTEGER, 
	agreement_document_id UUID, 
	disbursed_at TIMESTAMP WITHOUT TIME ZONE, 
	maturity_date DATE, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_loan PRIMARY KEY (id), 
	CONSTRAINT uq_loan_loan_application_id UNIQUE (loan_application_id), 
	CONSTRAINT fk_loan_loan_application_id_loan_application FOREIGN KEY(loan_application_id) REFERENCES loan_application (id), 
	CONSTRAINT fk_loan_borrower_member_id_member FOREIGN KEY(borrower_member_id) REFERENCES member (id), 
	CONSTRAINT fk_loan_loan_product_id_loan_product FOREIGN KEY(loan_product_id) REFERENCES loan_product (id), 
	CONSTRAINT fk_loan_loan_circle_id_loan_circle FOREIGN KEY(loan_circle_id) REFERENCES loan_circle (id), 
	CONSTRAINT fk_loan_disbursement_transaction_id_transaction FOREIGN KEY(disbursement_transaction_id) REFERENCES transaction (id), 
	CONSTRAINT fk_loan_disbursement_account_id_account FOREIGN KEY(disbursement_account_id) REFERENCES account (id), 
	CONSTRAINT fk_loan_agreement_document_id_signed_document FOREIGN KEY(agreement_document_id) REFERENCES signed_document (id)
)""",
    """CREATE TABLE peer_guarantee (
	loan_circle_id UUID NOT NULL, 
	guarantor_member_id UUID NOT NULL, 
	loan_id UUID, 
	pledge_source pledge_source NOT NULL, 
	source_account_id UUID NOT NULL, 
	pledged_amount BIGINT, 
	released_amount BIGINT, 
	applied_amount BIGINT, 
	hold_ledger_entry_id UUID, 
	agreement_document_id UUID, 
	status peer_guarantee_status NOT NULL, 
	locked_at TIMESTAMP WITHOUT TIME ZONE, 
	released_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_peer_guarantee PRIMARY KEY (id), 
	CONSTRAINT fk_peer_guarantee_loan_circle_id_loan_circle FOREIGN KEY(loan_circle_id) REFERENCES loan_circle (id), 
	CONSTRAINT fk_peer_guarantee_guarantor_member_id_member FOREIGN KEY(guarantor_member_id) REFERENCES member (id), 
	CONSTRAINT fk_peer_guarantee_loan_id_loan FOREIGN KEY(loan_id) REFERENCES loan (id), 
	CONSTRAINT fk_peer_guarantee_source_account_id_account FOREIGN KEY(source_account_id) REFERENCES account (id), 
	CONSTRAINT fk_peer_guarantee_hold_ledger_entry_id_ledger_entry FOREIGN KEY(hold_ledger_entry_id) REFERENCES ledger_entry (id), 
	CONSTRAINT fk_peer_guarantee_agreement_document_id_signed_document FOREIGN KEY(agreement_document_id) REFERENCES signed_document (id)
)""",
    """CREATE TABLE repayment_schedule (
	loan_id UUID NOT NULL, 
	version INTEGER NOT NULL, 
	schedule_type schedule_type NOT NULL, 
	seasonal_profile JSONB, 
	installment_count INTEGER NOT NULL, 
	first_due_date DATE NOT NULL, 
	status repayment_schedule_status NOT NULL, 
	origin repayment_schedule_origin NOT NULL, 
	approved_via UUID, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_repayment_schedule PRIMARY KEY (id), 
	CONSTRAINT repayment_schedule_loan_version UNIQUE (loan_id, version), 
	CONSTRAINT fk_repayment_schedule_loan_id_loan FOREIGN KEY(loan_id) REFERENCES loan (id), 
	CONSTRAINT fk_repayment_schedule_approved_via_maker_checker_approval FOREIGN KEY(approved_via) REFERENCES maker_checker_approval (id)
)""",
    """CREATE TABLE collections_case (
	loan_id UUID NOT NULL, 
	borrower_member_id UUID NOT NULL, 
	trigger collections_trigger NOT NULL, 
	hardship_request JSONB, 
	guarantor_notifications JSONB, 
	assigned_staff_id UUID, 
	status collections_case_status NOT NULL, 
	opened_at TIMESTAMP WITHOUT TIME ZONE, 
	closed_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_collections_case PRIMARY KEY (id), 
	CONSTRAINT fk_collections_case_loan_id_loan FOREIGN KEY(loan_id) REFERENCES loan (id), 
	CONSTRAINT fk_collections_case_borrower_member_id_member FOREIGN KEY(borrower_member_id) REFERENCES member (id), 
	CONSTRAINT fk_collections_case_assigned_staff_id_staff_user FOREIGN KEY(assigned_staff_id) REFERENCES staff_user (id)
)""",
    """CREATE TABLE repayment_installment (
	repayment_schedule_id UUID NOT NULL, 
	sequence INTEGER NOT NULL, 
	due_date DATE NOT NULL, 
	principal_due BIGINT, 
	interest_due BIGINT, 
	total_due BIGINT, 
	paid_amount BIGINT, 
	status repayment_installment_status NOT NULL, 
	payment_transaction_ids UUID[], 
	paid_at TIMESTAMP WITHOUT TIME ZONE, 
	id UUID NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	CONSTRAINT pk_repayment_installment PRIMARY KEY (id), 
	CONSTRAINT repayment_installment_schedule_sequence UNIQUE (repayment_schedule_id, sequence), 
	CONSTRAINT fk_repayment_installment_repayment_schedule_id_repaymen_8ee8 FOREIGN KEY(repayment_schedule_id) REFERENCES repayment_schedule (id)
)""",
    """ALTER TABLE ballot ADD CONSTRAINT fk_ballot_eligibility_snapshot FOREIGN KEY(eligibility_snapshot_id) REFERENCES eligibility_snapshot (id)""",
    """ALTER TABLE proposal ADD CONSTRAINT fk_proposal_ballot FOREIGN KEY(ballot_id) REFERENCES ballot (id)""",
    """ALTER TABLE loan_circle ADD CONSTRAINT fk_loan_circle_application FOREIGN KEY(loan_application_id) REFERENCES loan_application (id)""",
]

def upgrade() -> None:
    for stmt in _UP:
        op.execute(stmt)

def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS repayment_installment CASCADE")
    op.execute("DROP TABLE IF EXISTS repayment_schedule CASCADE")
    op.execute("DROP TABLE IF EXISTS peer_guarantee CASCADE")
    op.execute("DROP TABLE IF EXISTS collections_case CASCADE")
    op.execute("DROP TABLE IF EXISTS surplus_match CASCADE")
    op.execute("DROP TABLE IF EXISTS loan CASCADE")
    op.execute("DROP TABLE IF EXISTS loan_application CASCADE")
    op.execute("DROP TABLE IF EXISTS dividend_allocation CASCADE")
    op.execute("DROP TABLE IF EXISTS community_grant_pool CASCADE")
    op.execute("DROP TABLE IF EXISTS loan_product CASCADE")
    op.execute("DROP TABLE IF EXISTS dividend_declaration CASCADE")
    op.execute("DROP TABLE IF EXISTS vote_record CASCADE")
    op.execute("DROP TABLE IF EXISTS vote_participation CASCADE")
    op.execute("DROP TABLE IF EXISTS group_pot_approval_decision CASCADE")
    op.execute("DROP TABLE IF EXISTS eligibility_snapshot CASCADE")
    op.execute("DROP TABLE IF EXISTS election_candidate CASCADE")
    op.execute("DROP TABLE IF EXISTS configuration_parameter CASCADE")
    op.execute("DROP TABLE IF EXISTS roundup_config CASCADE")
    op.execute("DROP TABLE IF EXISTS proposal_cosignature CASCADE")
    op.execute("DROP TABLE IF EXISTS proposal_comment CASCADE")
    op.execute("DROP TABLE IF EXISTS group_pot_member CASCADE")
    op.execute("DROP TABLE IF EXISTS group_pot_approval_request CASCADE")
    op.execute("DROP TABLE IF EXISTS ballot CASCADE")
    op.execute("DROP TABLE IF EXISTS scheduled_payment CASCADE")
    op.execute("DROP TABLE IF EXISTS savings_goal CASCADE")
    op.execute("DROP TABLE IF EXISTS proposal CASCADE")
    op.execute("DROP TABLE IF EXISTS pooled_loan_circle_participant CASCADE")
    op.execute("DROP TABLE IF EXISTS payment_request_share CASCADE")
    op.execute("DROP TABLE IF EXISTS loan_circle_invitation CASCADE")
    op.execute("DROP TABLE IF EXISTS ledger_entry CASCADE")
    op.execute("DROP TABLE IF EXISTS group_pot CASCADE")
    op.execute("DROP TABLE IF EXISTS card CASCADE")
    op.execute("DROP TABLE IF EXISTS backing CASCADE")
    op.execute("DROP TABLE IF EXISTS roundup_capture CASCADE")
    op.execute("DROP TABLE IF EXISTS proxy_delegation CASCADE")
    op.execute("DROP TABLE IF EXISTS pooled_loan_circle CASCADE")
    op.execute("DROP TABLE IF EXISTS payment_request CASCADE")
    op.execute("DROP TABLE IF EXISTS payee CASCADE")
    op.execute("DROP TABLE IF EXISTS patronage_factor_record CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_preference CASCADE")
    op.execute("DROP TABLE IF EXISTS notification CASCADE")
    op.execute("DROP TABLE IF EXISTS membership_share CASCADE")
    op.execute("DROP TABLE IF EXISTS maker_checker_approval CASCADE")
    op.execute("DROP TABLE IF EXISTS loan_circle CASCADE")
    op.execute("DROP TABLE IF EXISTS kyc_submission CASCADE")
    op.execute("DROP TABLE IF EXISTS external_account_link CASCADE")
    op.execute("DROP TABLE IF EXISTS device_binding CASCADE")
    op.execute("DROP TABLE IF EXISTS data_subject_request CASCADE")
    op.execute("DROP TABLE IF EXISTS consent_record CASCADE")
    op.execute("DROP TABLE IF EXISTS compliance_case CASCADE")
    op.execute("DROP TABLE IF EXISTS community_project CASCADE")
    op.execute("DROP TABLE IF EXISTS account CASCADE")
    op.execute("DROP TABLE IF EXISTS transaction CASCADE")
    op.execute("DROP TABLE IF EXISTS staff_user CASCADE")
    op.execute("DROP TABLE IF EXISTS signed_document CASCADE")
    op.execute("DROP TABLE IF EXISTS regulatory_report_run CASCADE")
    op.execute("DROP TABLE IF EXISTS notification_event_type CASCADE")
    op.execute("DROP TABLE IF EXISTS member CASCADE")
    op.execute("DROP TABLE IF EXISTS capital_allocation_snapshot CASCADE")
    op.execute("DROP TABLE IF EXISTS audit_log_entry CASCADE")
    op.execute("DROP TYPE IF EXISTS staff_role")
    op.execute("DROP TYPE IF EXISTS staff_status")
    op.execute("DROP TYPE IF EXISTS approval_status")
    op.execute("DROP TYPE IF EXISTS compliance_case_type")
    op.execute("DROP TYPE IF EXISTS compliance_case_priority")
    op.execute("DROP TYPE IF EXISTS compliance_case_status")
    op.execute("DROP TYPE IF EXISTS card_type")
    op.execute("DROP TYPE IF EXISTS card_status")
    op.execute("DROP TYPE IF EXISTS data_subject_request_type")
    op.execute("DROP TYPE IF EXISTS data_subject_request_status")
    op.execute("DROP TYPE IF EXISTS regulatory_report_status")
    op.execute("DROP TYPE IF EXISTS group_pot_status")
    op.execute("DROP TYPE IF EXISTS group_pot_member_role")
    op.execute("DROP TYPE IF EXISTS recipient_identifier_type")
    op.execute("DROP TYPE IF EXISTS group_pot_member_status")
    op.execute("DROP TYPE IF EXISTS group_pot_approval_status")
    op.execute("DROP TYPE IF EXISTS group_pot_approval_decision")
    op.execute("DROP TYPE IF EXISTS patronage_period")
    op.execute("DROP TYPE IF EXISTS dividend_declaration_status")
    op.execute("DROP TYPE IF EXISTS payout_destination")
    op.execute("DROP TYPE IF EXISTS dividend_allocation_status")
    op.execute("DROP TYPE IF EXISTS community_project_status")
    op.execute("DROP TYPE IF EXISTS backing_source")
    op.execute("DROP TYPE IF EXISTS backing_status")
    op.execute("DROP TYPE IF EXISTS grant_pool_status")
    op.execute("DROP TYPE IF EXISTS surplus_match_status")
    op.execute("DROP TYPE IF EXISTS proposal_category")
    op.execute("DROP TYPE IF EXISTS proposal_status")
    op.execute("DROP TYPE IF EXISTS proposal_comment_status")
    op.execute("DROP TYPE IF EXISTS ballot_type")
    op.execute("DROP TYPE IF EXISTS ballot_status")
    op.execute("DROP TYPE IF EXISTS vote_choice")
    op.execute("DROP TYPE IF EXISTS proxy_delegation_status")
    op.execute("DROP TYPE IF EXISTS kyc_document_type")
    op.execute("DROP TYPE IF EXISTS kyc_screening_result")
    op.execute("DROP TYPE IF EXISTS kyc_result")
    op.execute("DROP TYPE IF EXISTS device_platform")
    op.execute("DROP TYPE IF EXISTS device_status")
    op.execute("DROP TYPE IF EXISTS consent_type")
    op.execute("DROP TYPE IF EXISTS consent_action")
    op.execute("DROP TYPE IF EXISTS account_type")
    op.execute("DROP TYPE IF EXISTS ledger_direction")
    op.execute("DROP TYPE IF EXISTS loan_product_type")
    op.execute("DROP TYPE IF EXISTS schedule_type")
    op.execute("DROP TYPE IF EXISTS loan_product_status")
    op.execute("DROP TYPE IF EXISTS loan_status")
    op.execute("DROP TYPE IF EXISTS loan_circle_status")
    op.execute("DROP TYPE IF EXISTS loan_circle_invitation_status")
    op.execute("DROP TYPE IF EXISTS pledge_source")
    op.execute("DROP TYPE IF EXISTS peer_guarantee_status")
    op.execute("DROP TYPE IF EXISTS repayment_schedule_status")
    op.execute("DROP TYPE IF EXISTS repayment_schedule_origin")
    op.execute("DROP TYPE IF EXISTS repayment_installment_status")
    op.execute("DROP TYPE IF EXISTS payout_order_mode")
    op.execute("DROP TYPE IF EXISTS pooled_loan_circle_status")
    op.execute("DROP TYPE IF EXISTS participant_payout_status")
    op.execute("DROP TYPE IF EXISTS collections_trigger")
    op.execute("DROP TYPE IF EXISTS collections_case_status")
    op.execute("DROP TYPE IF EXISTS signed_document_type")
    op.execute("DROP TYPE IF EXISTS signed_document_status")
    op.execute("DROP TYPE IF EXISTS membership_status")
    op.execute("DROP TYPE IF EXISTS share_class")
    op.execute("DROP TYPE IF EXISTS share_status")
    op.execute("DROP TYPE IF EXISTS notification_category")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS verification_method")
    op.execute("DROP TYPE IF EXISTS external_account_link_status")
    op.execute("DROP TYPE IF EXISTS payee_type")
    op.execute("DROP TYPE IF EXISTS payee_status")
    op.execute("DROP TYPE IF EXISTS payment_rail")
    op.execute("DROP TYPE IF EXISTS scheduled_payment_status")
    op.execute("DROP TYPE IF EXISTS split_mode")
    op.execute("DROP TYPE IF EXISTS payment_request_status")
    op.execute("DROP TYPE IF EXISTS payment_request_share_status")
    op.execute("DROP TYPE IF EXISTS roundup_destination_type")
    op.execute("DROP TYPE IF EXISTS roundup_capture_status")
