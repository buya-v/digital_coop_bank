# Acceptance Criteria — Digital Coop Bank

**Document ID:** 03_acceptance_criteria
**Status:** Final (single authoritative acceptance-criteria document; supersedes the sprint_1–sprint_3 QA documents)
**Upstream sources of truth:** `02_user_stories.md` (canonical backlog, US-x.y IDs used verbatim) and `01_business_analysis.md` (Canonical Glossary & Decision Log DEC-1…DEC-20, KPIs, personas).

## Conventions

* **Structure:** Organized by epic (EP-1…EP-13) and story, mirroring `02_user_stories.md` order. Every story has at least one happy-path and one negative/error scenario; every M/L/XL story additionally has at least one edge case.
* **Actors:** Members are "Member A", "Member B", etc. Back-office staff (P-5) are "Operator A" (maker) and "Operator B" (checker). No placeholder personal names are used.
* **Enums** are used verbatim per the glossary: `MembershipStatus`, `KycStatus`, `VoteChoice`, `ProposalCategory`, `ProposalStatus`, `BallotType`, `RecipientIdentifierType`, `LoanStatus`. All amounts are USD; machine representation is integer minor units (DEC-18) even where scenarios show display values like "$25.00".
* **Business Rules blocks:** Each epic opens with a Business Rules block. Every concrete threshold is tagged either **[CONFIRMED]** (traceable to the glossary/decision log, a KPI, or explicit story text) or **[PROPOSED]** (introduced by the sprint QA drafts or needed to make a scenario testable, **requires PO confirmation** and, where money-related, US-12.5 configuration rather than hard-coding). Draft values that contradict a decision are listed as **Superseded** and must not be implemented.
* **HTTP semantics:** `401 Unauthorized` = missing/invalid authentication; `403 Forbidden` = authenticated but not permitted (ownership, role, or status check failed); `409 Conflict` = duplicate/conflicting state change (e.g., double vote, idempotency replay with different payload); `422 Unprocessable Content` = payload validation failure. APIs may return `404 Not Found` instead of `403` for cross-member resource probing to prevent resource enumeration; where a scenario says `403`, `404`-for-privacy is an acceptable equivalent if applied consistently.
* **Idempotency:** Every money-movement command (P2P send, external payment, share purchase, Backing, Round-Up batch, pledge lock, disbursement, dividend posting) must accept a client-supplied idempotency key. Replaying the same key returns the original result and posts nothing twice; replaying the key with a different payload returns `409 Conflict`.
* **Audit:** Every scenario that changes financial, governance, or administrative state implicitly ends with "And the action is written to the immutable audit log (US-13.3) with actor, action, subject, before/after state, and timestamp." It is restated only where the audit entry itself is under test.

---

## EP-1 — Identity, Onboarding & KYC (CAP-1)

### EP-1 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** Onboarding time is measured from first app-flow screen to `MembershipStatus = ACTIVE`; targets: median ≤ 8 minutes, p90 ≤ 10 minutes (DEC-17, KPI-1.1). Instrumentation timestamps are mandatory.
* **[CONFIRMED]** `KycStatus = NOT_STARTED | IN_PROGRESS | PENDING_REVIEW | APPROVED | REJECTED` (DEC-19). `REJECTED` ends the application; no member record reaches a "rejected" membership status (DEC-4).
* **[CONFIRMED]** Persona is the identity-verification vendor for document OCR, biometric selfie match, and sanctions/PEP screening (DEC-5).
* **[CONFIRMED]** Name/address use the DEC-6 three-part Mongolian model (`ner`, `etsgiin_ner`, optional `ovog`, plus read-only `mrz_name_latin` and `registration_number`, `address_line_1`, `address_line_2`, `city`, `region`, `postal_code`, `country`); Cyrillic is canonical and `mrz_name_latin` is stored verbatim; the derived `legal_name` (the composition `ovog` `etsgiin_ner` `ner`) is display-only and never independently editable; `etsgiin_ner` is a patronymic and MUST NOT be treated as a family name or used to infer household or relationship.
* **[CONFIRMED]** Step-up authentication is required for: external payments above limits, card credential reveal, vote submission, Proxy Delegation changes, and guarantee pledges (US-1.4 list).
* **[PROPOSED]** Accepted ID-capture formats JPEG/PNG/PDF; maximum upload size 10 MB per file. (Sprint 1 draft.)
* **[PROPOSED]** OCR extraction confidence ≥ 80% required to auto-populate DEC-6 fields; below threshold triggers retry guidance. (Sprint 1 draft.)
* **[PROPOSED]** Biometric selfie match confidence ≥ 95% with passed liveness to auto-set `KycStatus = APPROVED`; ambiguous scores route to `PENDING_REVIEW`. (Sprint 1/2 drafts.)
* **[PROPOSED]** Maximum 3 automated verification attempts per stage before forced routing to `PENDING_REVIEW`. (Sprint 1/3 drafts.)
* **[PROPOSED]** Minimum applicant age 18 years, validated from the OCR-extracted date of birth. (Sprint 2 draft; statutory confirmation needed per chartering jurisdiction.)
* **[PROPOSED]** KYC artifacts (ID images, selfies, OCR output) encrypted with AES-256 at rest and TLS 1.3 in transit (TLS 1.2 minimum for third-party integrations that do not yet support 1.3), stored in an isolated compliant bucket. (Sprint 1/3 drafts.) [ADJUDICATED → see DEC-26 in 05_prd_and_roadmap.md: AES-256-GCM at rest; TLS 1.3 in transit, per the standard above]
* **[PROPOSED]** 3 consecutive failed step-up attempts cancel the sensitive action and require full re-authentication. (Sprint 1 draft.)
* **Superseded — do not implement:** draft statuses "ID Uploaded - Awaiting Verification", "Verified", "Passed", "Pending Manual Verification" (replaced by `KycStatus` per DEC-19); membership tiers "Founding Member"/"Active Shareholder" (contradict one-member-one-vote).

### US-1.1 — Start, Save and Resume the Digital Onboarding Journey (M)

**Data validation & security:** application state is persisted server-side, keyed to the applicant's verified contact channel; resume requires re-verification of that channel (OTP); onboarding APIs reject unauthenticated calls with `401 Unauthorized`.

**Scenario 1 — Happy path: start application and see progress**
* **Given** a prospective member has installed the app and verified their phone number via OTP
* **When** they tap "Become a member" and complete the personal-details step using the DEC-6 fields (`ner` "Болд", `etsgiin_ner` "Батын", `ovog` omitted, `address_line_1`, `city`, `region`, `postal_code`, `country`)
* **Then** an application record is created with `KycStatus = NOT_STARTED` and `MembershipStatus = PENDING_KYC`
* **And** the progress indicator shows step 1 of 4 complete (personal details → eligibility → KYC → share purchase)
* **And** the instrumentation event `onboarding_started` is emitted with a timestamp for KPI-1.1 measurement.

**Scenario 2 — Happy path: resume exactly where interrupted**
* **Given** Member A completed the personal-details and eligibility steps yesterday and force-closed the app during document capture (`KycStatus = IN_PROGRESS`)
* **When** they reopen the app and re-verify their registered phone number via OTP
* **Then** the application resumes at the document-capture step with all previously entered data intact
* **And** no completed step is re-requested.

**Scenario 3 — Negative: resume attempt without verified channel**
* **Given** an application saved against a verified phone number
* **When** a client requests the saved application state without completing the OTP challenge (missing/invalid session token)
* **Then** the API responds `401 Unauthorized`
* **And** no application data (including partial PII) is returned in the response body.

**Scenario 4 — Edge: state advanced on another device**
* **Given** Member A's application reached `KycStatus = IN_PROGRESS` on device 1
* **When** they resume on device 2 and complete document capture, then reopen device 1 which still displays the capture step
* **And** device 1 submits the now-stale step
* **Then** the server rejects the stale submission with `409 Conflict`
* **And** device 1 refreshes to the current server-side step without losing any data.

### US-1.2 — eKYC Verification via Persona (Document, Biometric, Screening) (L)

**Data validation & security:** OCR output must populate non-empty `ner`, `etsgiin_ner`, `mrz_name_latin`, date of birth, and document number before proceeding; `registration_number` is **not** expected from card-face OCR (post-2022 ID cards do not print it) — it is supplied by the applicant and confirmed against the verified identity source, and a mismatch blocks the application (DEC-6(d)); the vendor result is correlated to the application by `registration_number` only, never by name match (DEC-6(c)); all vendor callbacks are signature-verified; screening results are never exposed to the applicant verbatim (tipping-off safeguard).

**Scenario 1 — Happy path: clear pass end to end**
* **Given** Member A's application is at the KYC step with `KycStatus = IN_PROGRESS`
* **When** they photograph a valid, unexpired government ID, Persona OCR extracts the DEC-6 name/address fields with ≥ 80% confidence [PROPOSED threshold]
* **And** the live selfie passes liveness detection and matches the document photo at ≥ 95% confidence [PROPOSED threshold]
* **And** sanctions/PEP screening returns no hits
* **Then** `KycStatus` transitions to `APPROVED`
* **And** `MembershipStatus` transitions `PENDING_KYC → PENDING_PAYMENT`
* **And** the applicant is navigated to the share-purchase step (US-2.1).

**Scenario 2 — Negative: liveness spoof attempt**
* **Given** Member A is at the selfie step
* **When** a printed photograph is presented to the camera instead of a live face
* **Then** Persona liveness detection fails the capture
* **And** `KycStatus` remains `IN_PROGRESS` with the attempt counter incremented ("Attempt 1 of 3" [PROPOSED limit])
* **And** the applicant sees retry guidance without any indication of which specific check failed beyond "we could not verify it was you, live".

**Scenario 3 — Negative: hard fail ends the application**
* **Given** Persona returns a confirmed document-fraud signal (tampered ID)
* **When** the verification result is processed
* **Then** `KycStatus` transitions to `REJECTED`
* **And** the application ends; no member record is created and no "rejected" membership status exists (DEC-4)
* **And** the applicant is informed the application cannot proceed, with an appeal/contact route but no fraud-signal detail.

**Scenario 4 — Edge: ambiguous result routes to manual review**
* **Given** the selfie match returns 87% confidence (below the [PROPOSED] 95% auto-pass) with passed liveness
* **When** the third automated attempt also scores below threshold
* **Then** `KycStatus` transitions to `PENDING_REVIEW`
* **And** a case is created in the US-12.2 KYC queue containing the Persona evidence bundle
* **And** the applicant sees "Your identity is being reviewed — we'll notify you" with the application saved for resume.

**Scenario 5 — Edge: watchlist potential match**
* **Given** document and selfie checks pass cleanly
* **When** sanctions/PEP screening returns a potential (non-exact) name match
* **Then** `KycStatus` transitions to `PENDING_REVIEW` and the case routes to US-12.2 flagged "screening hit — potential match"
* **And** the applicant-facing message is the neutral review message with no mention of screening (tipping-off safeguard)
* **And** the applicant cannot reach the share-purchase step while `PENDING_REVIEW`.

### US-1.3 — Membership Eligibility & Common-Bond Validation (S)

**Scenario 1 — Happy path: eligible applicant passes before payment**
* **Given** Member A's application has a residential address inside the cooperative's configured common-bond region
* **When** the eligibility step executes against the data-driven rule set (seeded via US-12.5)
* **Then** the check passes and the applicant proceeds toward KYC/share purchase
* **And** the evaluated rule version ID is recorded on the application.

**Scenario 2 — Negative: ineligible applicant blocked before the $25.00 payment**
* **Given** Member A's address is outside every configured common-bond criterion
* **When** the eligibility step executes
* **Then** the application is halted before the share-purchase step is ever presented
* **And** the applicant sees which criterion failed and a remediation path (e.g., "eligibility extends to employees of listed partner co-ops — check the full criteria")
* **And** no payment is collected and `MembershipStatus` never advances past `PENDING_KYC`.

**Scenario 3 — Edge: rules amended by GOVERNANCE_BYLAW without code change**
* **Given** a certified `GOVERNANCE_BYLAW` ballot outcome expands the common bond to a new county, applied as a US-12.5 configuration change linked to the ballot
* **When** an applicant from the new county reaches the eligibility step after the configuration's effective date
* **Then** the check passes using the new rule version
* **And** applications evaluated before the effective date retain their originally recorded rule version.

### US-1.4 — Multi-Factor Authentication, Biometrics & Device Binding (M)

**Scenario 1 — Happy path: biometric sign-in on a bound device**
* **Given** Member A enrolled in MFA during onboarding and bound device 1
* **When** they open the app on device 1 and pass the device biometric prompt
* **Then** a session is issued without a password challenge
* **And** routine actions (view balances, browse ballots) require no further challenge.

**Scenario 2 — Happy path: step-up challenge on a sensitive action**
* **Given** Member A has an active session
* **When** they initiate a card credential reveal (US-5.1), a vote submission (US-8.1), or an external payment above the configured limit (US-4.2)
* **Then** the system requires a fresh step-up authentication (biometric or PIN) before executing
* **And** the step-up result is bound to that single action and cannot be replayed for another action.

**Scenario 3 — Negative: repeated step-up failure cancels the action**
* **Given** Member A triggers step-up for a guarantee pledge
* **When** authentication fails 3 consecutive times [PROPOSED limit]
* **Then** the pledge action is cancelled with no state change
* **And** the session is downgraded to require full re-authentication
* **And** a security notification is sent via US-11.1 (exempt from quiet hours per US-11.2).

**Scenario 4 — Edge: sign-in from a new, unbound device**
* **Given** Member A attempts sign-in on device 2, never seen before
* **When** they present valid credentials
* **Then** the system requires verification via the registered contact channel before binding device 2
* **And** a "new device added" notification is sent to all previously bound devices
* **And** sensitive actions from device 2 remain step-up-gated as usual.

### US-1.5 — Member Profile, Consents & Communication Preferences (S)

**Scenario 1 — Happy path: view profile and standing**
* **Given** Member A is ACTIVE with a Member ID and join date
* **When** they open the profile screen
* **Then** they see their DEC-6 structured name and address, contact details, consents, `MembershipStatus = ACTIVE` with a plain-language explanation, Member ID, and join date
* **And** the derived `legal_name` is displayed read-only with no edit affordance.

**Scenario 2 — Negative: attempt to edit a non-editable or invalid field**
* **Given** Member A opens profile editing
* **When** a client submits a payload attempting to write `legal_name` directly, or submits a `postal_code` failing the country-specific format
* **Then** the API rejects the request with `422 Unprocessable Content` naming the offending fields
* **And** no profile attribute is changed.

**Scenario 3 — Edge: KYC-relevant change triggers re-verification**
* **Given** Member A changes `etsgiin_ner` and `address_line_1`
* **When** the change is submitted
* **Then** the change is held pending re-verification (Persona re-check or US-12.1 admin review, per policy)
* **And** the previous verified values remain in force for card embossing, ACH, and statements until the re-verification completes
* **And** a consent-relevant change (e.g., withdrawing marketing consent) takes effect immediately and is recorded for US-13.6 enforcement.

---

## EP-2 — Membership Shares & Equity (CAP-2)

### EP-2 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** One mandatory membership share at $25.00 par value, purchased during onboarding; non-withdrawable equity while ACTIVE; redeemable at par on `CLOSED` subject to bylaws (DEC-11; redemption terms are Open Item 1 — implemented behind a configurable rule).
* **[CONFIRMED]** Status machine per DEC-4: `PENDING_KYC → PENDING_PAYMENT → ACTIVE`; `ACTIVE ↔ SUSPENDED`; `ACTIVE/SUSPENDED → CLOSED`. Only ACTIVE members may vote, borrow, or guarantee. Admin transitions require maker-checker.
* **[CONFIRMED]** Voting eligibility is binary: the one mandatory share while ACTIVE confers exactly one vote regardless of any future additional holdings (US-2.3).
* **[CONFIRMED]** Share par value is US-12.5 configuration ("share par" listed as a configurable parameter), never hard-coded.
* **[PROPOSED]** Member ID format: system-issued, unique, non-guessable and non-sequential (e.g., `DCB-8K4W2M9X`). (Sprint 1/2 drafts.) [ADJUDICATED → see DEC-28 in 05_prd_and_roadmap.md: final format `DCB-` + 8 non-sequential alphanumeric characters including a check character]
* **Superseded — do not implement:** $10.00/share and multi-share purchase at onboarding (Sprint 1 draft), $5.00 share funded from first deposit (Sprint 3 draft) — both replaced by DEC-11 ($25.00, purchased in-flow); "membership token"/`PENDING_TOKEN` (replaced by the `PENDING_PAYMENT → ACTIVE` transition, DEC-4).

### US-2.1 — Initial Membership Share Purchase & Member Activation (M)

**Data validation & security:** the purchase amount is fixed at exactly $25.00 (2500 minor units) sourced from US-12.5 configuration; client-supplied amounts are ignored/rejected; the purchase endpoint requires an application in `MembershipStatus = PENDING_PAYMENT`.

**Scenario 1 — Happy path: card payment activates membership**
* **Given** Member A's application has `KycStatus = APPROVED` and `MembershipStatus = PENDING_PAYMENT`
* **When** they pay $25.00 by debit card and the payment settles
* **Then** $25.00 posts to the Membership Share Account as non-withdrawable equity
* **And** `MembershipStatus` transitions `PENDING_PAYMENT → ACTIVE`
* **And** the member receives their Member ID and a digital confirmation containing the share record and a copy of the bylaws
* **And** voting, borrowing, and guaranteeing rights activate, and the `onboarding_completed` timestamp is emitted for KPI-1.1.

**Scenario 2 — Negative: payment declined**
* **Given** Member A is at the share-purchase step
* **When** the card payment is declined for insufficient funds
* **Then** no entry posts to the Membership Share Account
* **And** `MembershipStatus` remains `PENDING_PAYMENT`
* **And** the applicant sees "Payment declined — please try another method" and can retry with card, bank transfer, or wallet-funded card without restarting onboarding.

**Scenario 3 — Edge: duplicate settlement webhook (idempotency)**
* **Given** Member A's $25.00 payment settled and activated membership
* **When** the payment processor redelivers the same settlement webhook (same payment reference)
* **Then** the system recognizes the idempotency key and posts nothing further
* **And** exactly one share is recorded in the registry and the equity ledger shows exactly one $25.00 credit.

**Scenario 4 — Negative (security): API bypass attempt before KYC approval**
* **Given** a client authenticated to an application with `KycStatus = PENDING_REVIEW` (so `MembershipStatus = PENDING_KYC`)
* **When** it POSTs directly to the share-purchase endpoint
* **Then** the API responds `403 Forbidden` (authenticated but state-ineligible)
* **And** no payment is initiated and no ledger entry is created
* **And** the attempt is written to the audit log as a policy violation.

### US-2.2 — Membership Lifecycle Enforcement (Status Machine) (M)

**Scenario 1 — Happy path: rights follow status**
* **Given** Member A is `ACTIVE`
* **When** they cast a vote, apply for a loan, and accept a guarantor invitation
* **Then** all three actions are permitted by the server-side status check
* **And** each permission evaluation is performed server-side, not inferred from UI state.

**Scenario 2 — Negative: SUSPENDED blocks vote/borrow/guarantee**
* **Given** Member A has been suspended (`MembershipStatus = SUSPENDED`) via US-12.1
* **When** they attempt to submit a vote, a loan application, or a pledge
* **Then** each request is rejected with `403 Forbidden` and reason "membership suspended"
* **And** their record, balances, and history are preserved and viewable
* **And** the in-app status screen (US-1.5) explains the suspension's practical meaning and the appeal route.

**Scenario 3 — Negative: illegal transition rejected everywhere**
* **Given** Member A is `CLOSED`
* **When** any API or admin action attempts `CLOSED → ACTIVE`, or an application attempts `PENDING_KYC → ACTIVE` (skipping `PENDING_PAYMENT`)
* **Then** the domain layer rejects the transition with `409 Conflict` and an "illegal transition" error naming the from/to states
* **And** no partial state change occurs.

**Scenario 4 — Edge: reinstatement restores rights immediately**
* **Given** Member A is `SUSPENDED` and their appeal is upheld
* **When** Operator A initiates and Operator B approves the `SUSPENDED → ACTIVE` transition (maker-checker via US-12.1)
* **Then** `MembershipStatus` becomes `ACTIVE` and vote/borrow/guarantee rights are restored immediately
* **And** the member is notified via US-11.1 with a deep link to their status screen.

### US-2.3 — Share Registry & Voting-Eligibility Snapshots (M)

**Scenario 1 — Happy path: snapshot at ballot open**
* **Given** the cooperative has 1,000 members of whom 940 are `ACTIVE` at 09:00
* **When** a ballot opens at 09:00 (US-12.4)
* **Then** the registry produces an eligibility snapshot containing exactly those 940 ACTIVE members, each with exactly one vote
* **And** the snapshot is immutable, timestamped, and referenced by the ballot for US-8.1 checks and US-12.4 certification.

**Scenario 2 — Negative: registry/ledger reconciliation mismatch**
* **Given** a reconciliation run compares share registry entries to the equity ledger
* **When** the registry shows 940 issued shares but the ledger total equals 939 × $25.00
* **Then** the reconciliation job flags the discrepancy, alerts P-5, and blocks new snapshot production until resolved
* **And** the discrepancy record identifies the specific member entries that fail to reconcile.

**Scenario 3 — Edge: member activated after ballot open is excluded**
* **Given** a ballot's snapshot was taken at 09:00
* **When** Member B becomes `ACTIVE` at 09:05
* **Then** Member B is not eligible on that ballot and an attempted vote returns `403 Forbidden` with reason "not in the eligibility snapshot"
* **And** Member B appears in snapshots for all subsequently opened ballots.

**Scenario 4 — Edge: one vote regardless of holdings**
* **Given** a future state where Member A holds additional (voluntary) shares beyond the mandatory share
* **When** any eligibility snapshot is produced
* **Then** Member A still carries exactly one vote (binary eligibility)
* **And** registry queries surfaced to P-4 show holdings without any voting-weight field other than 1.

### US-2.4 — Voluntary Membership Closure & Share Redemption (M)

**Scenario 1 — Happy path: clean closure with par redemption**
* **Given** Member A is `ACTIVE` with no `ACTIVE`/`DELINQUENT` loans, no locked guarantee pledges, no unresolved Group Pot memberships, and a verified external account on file
* **When** they complete the guided closure flow and confirm with step-up authentication
* **Then** remaining deposit balances are swept to the external account
* **And** the membership share is redeemed at $25.00 par (per the configurable bylaws rule, Open Item 1) to the same external account
* **And** `MembershipStatus` transitions to `CLOSED`, the share registry records the redemption, and post-closure data handling follows US-13.6.

**Scenario 2 — Negative: closure blocked by an active loan**
* **Given** Member A has a loan with `LoanStatus = ACTIVE`
* **When** they start the closure flow
* **Then** the precondition check fails before any irreversible step
* **And** the flow lists the blocking items ("repay or settle loan L-…") with deep links
* **And** no status change or redemption occurs.

**Scenario 3 — Negative: closure blocked by a locked guarantee pledge**
* **Given** Member A has a $200.00 guarantee pledge locked against Member B's `ACTIVE` loan
* **When** they attempt closure
* **Then** the flow is blocked with reason "guarantee pledge locked until the guaranteed loan is repaid or released"
* **And** the pledge remains locked and untouched.

**Scenario 4 — Edge: unresolved Group Pot membership**
* **Given** Member A is the last remaining approver in a Group Pot with a non-zero balance
* **When** they attempt closure
* **Then** the flow requires the Group Pot membership to be resolved first (transfer role/funds or dissolve the pot per US-3.4 rules)
* **And** closure proceeds only once the pot check passes on re-run.

---

## EP-3 — Savings & Deposit Accounts (CAP-3)

### EP-3 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** Four deposit constructs per DEC-13: Primary Savings Account, Transaction Account, Savings Goal (personal), Group Pot (shared m-of-n). Terms used verbatim.
* **[CONFIRMED]** Primary Savings Account opens automatically at `MembershipStatus = ACTIVE`; interest accrues daily and posts monthly; rate parameters administered via US-12.5 (US-3.1).
* **[CONFIRMED]** Group Pot: invitations only to ACTIVE members addressed by `PHONE | EMAIL | MEMBER_ID`; inbound contributions need no approval; every outbound transfer requires the configured m-of-n approvals (US-3.4/US-3.5).
* **[CONFIRMED — structural]** The approval threshold m must satisfy 1 ≤ m ≤ n where n = current number of pot approvers; configurations violating this are rejected.
* **[PROPOSED]** Pending Group Pot outbound approvals expire after 48 hours; on expiry the request is cancelled and the hold released. (Sprint 3 draft; story requires "time-outs", the 48 h value needs PO confirmation.)
* **[PROPOSED]** Savings Goal scheduled auto-transfers that meet insufficient funds are skipped for that occurrence with a member notification, and do not overdraft the Transaction Account. (Extrapolated from the confirmed Round-Up skip rule; needs PO confirmation.)
* **[PROPOSED]** Savings Goal target amount must be > $0.00 and target date, when set, must be in the future. (Draft-level validation.)

### US-3.1 — Primary Savings Account with Interest Accrual & Posting (M)

**Scenario 1 — Happy path: automatic opening at activation**
* **Given** Member A's `MembershipStatus` transitions to `ACTIVE` at 14:02
* **When** the activation event is processed
* **Then** a Primary Savings Account is opened automatically with a $0.00 balance and the current US-12.5-configured interest rate
* **And** the account is visible in-app within the same session with accrued interest shown as $0.00.

**Scenario 2 — Happy path: daily accrual, monthly posting**
* **Given** Member A holds $1,000.00 for all 30 days of a month at an annual rate of 2.00% (configuration example)
* **When** the month-end posting job runs
* **Then** daily accruals of $1,000.00 × 2.00%/365 have accumulated each day and the month's accrued total posts as one interest credit
* **And** the member-facing yield history shows earned-to-date and the last posting amount, both reconciling to the ledger
* **And** rounding to integer minor units follows a single documented rule (accumulate at high precision, round at posting).

**Scenario 3 — Negative: withdrawal exceeding available balance**
* **Given** Member A's savings balance is $150.00 with $100.00 locked as a guarantee pledge (US-6.4), so available = $50.00
* **When** they attempt an internal transfer of $75.00 out of savings
* **Then** the transfer is rejected with `422 Unprocessable Content` and message "amount exceeds available balance $50.00"
* **And** no ledger entry is created and the locked pledge is untouched.

**Scenario 4 — Edge: effective-dated rate change mid-month**
* **Given** a maker-checker-approved US-12.5 rate change from 2.00% to 2.50% effective the 16th
* **When** the month-end posting runs
* **Then** days 1–15 accrued at 2.00% and days 16–end at 2.50%
* **And** the yield history discloses the rate change date, linked to the certified `FINANCIAL_POLICY` ballot where applicable.

### US-3.2 — Transaction (Checking) Account with Categorized History (M)

**Scenario 1 — Happy path: real-time balance and categorized history**
* **Given** Member A's Transaction Account has a $250.00 balance
* **When** a $12.40 card purchase at a grocery merchant settles
* **Then** the balance updates to $237.60 in real time
* **And** the transaction appears in history with an automatic category "Groceries", merchant name, and timestamp
* **And** opening the transaction detail offers a shareable confirmation receipt containing timestamp, unique transaction reference, amount, counterparty, and status.

**Scenario 2 — Happy path: search and filter**
* **Given** Member A has 200 historical transactions
* **When** they search "coffee" filtered to the last 30 days and category "Eating out"
* **Then** only matching transactions are returned, ordered newest first, with correct running totals.

**Scenario 3 — Negative (security): cross-member transaction access**
* **Given** Member B is authenticated
* **When** Member B requests the transaction detail or receipt for a transaction belonging to Member A by guessing its reference ID
* **Then** the API responds `403 Forbidden` (or `404 Not Found` per the enumeration-protection convention)
* **And** no transaction attribute of Member A is disclosed.

**Scenario 4 — Edge: uncategorizable transaction**
* **Given** a settled transaction from an unknown merchant code
* **When** categorization runs
* **Then** the transaction is assigned "Uncategorized" rather than a wrong guess, and the member can recategorize it manually
* **And** the manual category persists for the member's future transactions from the same merchant.

### US-3.3 — Savings Goals (Personal Pots) (M)

**Scenario 1 — Happy path: create a goal with automated transfers**
* **Given** Member A has a Primary Savings Account and a Transaction Account
* **When** they create Savings Goal "New Laptop" with target $900.00, target date 6 months out, an emoji, and a recurring $75.00 monthly auto-transfer from the Transaction Account
* **Then** the goal is created as a sub-account under the Primary Savings Account with a progress bar at 0%
* **And** on the next scheduled date $75.00 moves Transaction Account → goal and progress shows $75.00 / $900.00 (8%).

**Scenario 2 — Happy path: withdraw from a goal with gentle confirmation**
* **Given** the "New Laptop" goal holds $300.00
* **When** Member A withdraws $100.00 back to the Transaction Account
* **Then** a confirmation explains the effect on their goal progress before executing
* **And** on confirm, $100.00 transfers and progress updates to $200.00 / $900.00.

**Scenario 3 — Negative: invalid goal parameters**
* **Given** Member A is creating a goal
* **When** they submit a target amount of $0.00 or a target date in the past [PROPOSED validation]
* **Then** the API rejects with `422 Unprocessable Content` naming the invalid fields
* **And** no goal is created.

**Scenario 4 — Edge: scheduled transfer meets insufficient funds**
* **Given** Member A's Transaction Account holds $40.00 on the scheduled date of a $75.00 auto-transfer
* **When** the transfer job runs
* **Then** the occurrence is skipped without overdrafting [PROPOSED rule], the goal balance is unchanged
* **And** Member A is notified via US-11.1 with the next scheduled attempt date; the schedule itself remains active.

### US-3.4 — Group Pot Creation, Membership & Verifiable Ledger (L)

**Scenario 1 — Happy path: create pot, invite, configure m-of-n**
* **Given** Member A (P-4) is `ACTIVE`
* **When** they create Group Pot "Community Garden Fund" with a named purpose, invite Member B by `MEMBER_ID` and Member C by `EMAIL`, and set the approval rule to 2-of-3
* **Then** the pot is created, invitees show "invited" until they accept, and the 2-of-3 rule is stored
* **And** on both acceptances all three see the shared sub-ledger (balance, history, per-member contribution breakdown) in real time.

**Scenario 2 — Happy path: contributions need no approval**
* **Given** the pot is formed
* **When** Member B contributes $50.00 from their Transaction Account
* **Then** the contribution posts immediately without any approval
* **And** the ledger shows the pot balance and Member B's cumulative contribution ($50.00) to all pot members.

**Scenario 3 — Negative: invalid approval threshold**
* **Given** the pot has 3 approvers
* **When** Member A attempts to set the rule to 4-of-3 (or 0-of-3)
* **Then** the configuration is rejected with `422 Unprocessable Content`: "threshold must be between 1 and the number of approvers (3)"
* **And** the previous rule remains in force.

**Scenario 4 — Negative: inviting a non-ACTIVE member**
* **Given** Member D's `MembershipStatus = SUSPENDED`
* **When** Member A invites Member D by phone number
* **Then** the invitation is refused with "no active cooperative member found for this identifier"
* **And** the response does not disclose whether the identifier belongs to a suspended member or to nobody (no status leakage).

**Scenario 5 — Edge (security): non-member access to the pot ledger**
* **Given** Member E is not a pot member
* **When** Member E requests the pot's balance, history, or member list by pot ID
* **Then** the API responds `403 Forbidden`/`404 Not Found`
* **And** access control is enforced per pot-membership list, not merely hidden in the UI.

### US-3.5 — Group Pot Outbound Approval Workflow (m-of-n) (M)

**Scenario 1 — Happy path: threshold reached, transfer executes**
* **Given** Group Pot "Community Garden Fund" holds $600.00 with a 2-of-3 rule
* **When** Member A requests an outbound transfer of $200.00 to a nursery with purpose "seedlings"
* **Then** the request enters pending-approval, $200.00 is held, and Members B and C are notified with amount, recipient, and purpose (US-11.1)
* **And when** Member B approves in-app
* **Then** the 2-of-3 threshold is met (initiator counts as one approval — see note below), the transfer executes, the hold converts to a debit, and all pot members are notified
* **And** the decision trail (who requested, who approved, when) is written to the pot ledger and the immutable audit log.
* *Note:* whether the initiator's request counts as their approval is **[PROPOSED — needs PO confirmation]**; scenarios must be re-parameterized once decided.

**Scenario 2 — Negative: threshold becomes unreachable**
* **Given** a pending $150.00 request under a 2-of-3 rule where the initiator's request counts as one approval
* **When** both other approvers reject it
* **Then** the request is cancelled as unreachable, the $150.00 hold is released
* **And** all pot members are notified with the rejection reasons recorded in the ledger.

**Scenario 3 — Negative (security): non-approver or double approval**
* **Given** a pending outbound request
* **When** Member E (not a pot approver) posts an approval, or Member B approves the same request a second time
* **Then** the non-approver receives `403 Forbidden` and the duplicate receives `409 Conflict`
* **And** the approval count is unchanged by either call.

**Scenario 4 — Edge: expiry and reminder nudges**
* **Given** a pending request has received 1 of 2 required approvals
* **When** 24 hours pass, a reminder nudge is sent to outstanding approvers; **when** 48 hours pass without threshold [PROPOSED window]
* **Then** the request status becomes expired/cancelled, the hold is released to the pot balance
* **And** the expiry is recorded in the pot ledger and all members are notified.

---

## EP-4 — Payments & Transfers (CAP-4)

### EP-4 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** P2P recipients addressed by exactly one of `PHONE | EMAIL | MEMBER_ID`; usernames/handles unsupported (DEC-3). Recipient display-name confirmation before send. Internal P2P fee is $0.00. Per-transaction and velocity limits are US-12.5 configuration.
* **[CONFIRMED]** USD only, integer minor units (DEC-18); FX out of scope. All transfer flows feed AML monitoring (US-13.1). Step-up authentication for external payments above configured thresholds (US-1.4/US-4.2).
* **[PROPOSED]** Default P2P daily velocity limit $2,000.00 per sender (Sprint 1 draft) — to be seeded as the initial US-12.5 value, not hard-coded.
* **[PROPOSED]** Internal P2P ledger settlement SLA < 3 seconds (Sprint 1 draft).
* **[PROPOSED]** Recipient confirmation shows display name as first name + last initial (e.g., "Member B.") to limit PII exposure (Sprint 1 draft).
* **[PROPOSED]** Default step-up threshold for external payments: single transfer > $1,000.00 (no draft value existed; placeholder for the US-12.5 seed — PO to confirm).
* **[PROPOSED]** External account linking verified via micro-deposits or instant account verification before first outbound use. [ADJUDICATED → see DEC-37 in 05_prd_and_roadmap.md: Plaid instant verification primary; micro-deposit fallback for unsupported institutions]
* **[PROPOSED]** Failed recurring payments retry up to 2 times at 24-hour intervals before the occurrence is marked failed (Sprint drafts imply retry; count/interval need PO confirmation).
* **Security assertions (all EP-4 stories):** every money-movement command carries an idempotency key; senders can only originate from accounts they own (ownership check server-side); velocity/limit checks evaluate server-side before ledger execution.

### US-4.1 — Instant Internal P2P Transfer (M)

**Scenario 1 — Happy path: send by phone number with display-name confirmation**
* **Given** Member A has $100.00 in their Transaction Account and Member B has a registered phone number
* **When** Member A enters that phone number (`RecipientIdentifierType = PHONE`), the app shows "Member B." for confirmation, and Member A confirms and sends $25.00
* **Then** the ledger settles instantly (target < 3 s [PROPOSED SLA]) with a $0.00 fee
* **And** Member A's balance is $75.00 and Member B's is credited $25.00
* **And** both parties receive notifications with deep links (US-11.1) and the transfer is emitted to AML monitoring (US-13.1).

**Scenario 2 — Negative: recipient not found / not addressable**
* **Given** Member A enters an email address registered to no ACTIVE member
* **When** the lookup executes
* **Then** the response is "no member found for this identifier" and the send button stays disabled
* **And** the response is identical whether the identifier is unknown, or belongs to a `SUSPENDED`/`CLOSED` member (no membership-status leakage).

**Scenario 3 — Negative: velocity limit exceeded**
* **Given** the configured daily P2P limit is $2,000.00 [PROPOSED seed value] and Member A has sent $1,900.00 today
* **When** they attempt to send another $150.00
* **Then** the transfer is rejected before execution with "this transfer would exceed your daily limit; remaining today: $100.00"
* **And** no ledger entry is created.

**Scenario 4 — Edge: duplicate submission (idempotency)**
* **Given** Member A taps "Send" and the network times out, and the client retries with the same idempotency key
* **When** both requests reach the server
* **Then** exactly one $25.00 transfer settles
* **And** the retry receives the original success response; a replay of the same key with a different amount returns `409 Conflict`.

**Scenario 5 — Edge: self-transfer via own identifier**
* **Given** Member A enters their own registered email as recipient
* **When** the lookup resolves to the sender
* **Then** P2P send is blocked with guidance to use internal account-to-account transfer instead
* **And** no transfer record is created.

### US-4.2 — External Payments (ACH, Wire, Real-Time Rails) (L)

**Scenario 1 — Happy path: link external account and send outbound ACH**
* **Given** Member A has linked and verified an external bank account
* **When** they submit a $500.00 outbound ACH before the configured cut-off time
* **Then** the payment is accepted with status "submitted", included in that day's batch, and status tracking progresses submitted → processing → completed
* **And** any configured fee (US-12.5) is disclosed before confirmation and posted as a separate ledger line
* **And** the payment is emitted to AML monitoring (US-13.1).

**Scenario 2 — Happy path: step-up above the threshold**
* **Given** the step-up threshold is $1,000.00 [PROPOSED seed value]
* **When** Member A submits a $2,500.00 wire
* **Then** step-up authentication (US-1.4) is required before the wire is accepted
* **And** without a fresh successful step-up, the API rejects the submission with `403 Forbidden` reason "step-up required".

**Scenario 3 — Negative: unverified external account**
* **Given** Member A added an external account but has not completed verification
* **When** they attempt an outbound transfer to it
* **Then** the request is rejected with "external account not yet verified" and verification instructions
* **And** no payment is initiated.

**Scenario 4 — Edge: ACH return after posting**
* **Given** Member A's $500.00 inbound ACH was credited and 2 days later an R01 (insufficient funds) return arrives
* **When** the return is processed
* **Then** the credit is reversed with a clearly labeled linked ledger entry, the payment status becomes "returned" with a member-readable reason
* **And** the member is notified via US-11.1; if the reversal overdraws the account, the balance may go negative and collections/notification policy applies (no silent absorption).

**Scenario 5 — Edge: cut-off boundary and rail fallback**
* **Given** the same-day ACH cut-off is 16:00 and a real-time rail (FedNow) is unavailable for the recipient bank
* **When** Member A submits at 16:05 requesting the fastest option
* **Then** the app shows the payment will process next business day (or offers wire where eligible), with the effective date displayed before confirmation
* **And** the stored payment carries the correct effective date, not the submission date.

### US-4.3 — Bill Pay & Scheduled / Recurring Transfers (M)

**Scenario 1 — Happy path: recurring payment executes on schedule**
* **Given** Member A creates a recurring monthly payment of $60.00 to a saved payee, first execution on the 1st
* **When** the 1st arrives with sufficient funds
* **Then** the payment executes over the appropriate rail (US-4.1/US-4.2), the occurrence is marked completed
* **And** the schedule shows the next execution date.

**Scenario 2 — Negative: insufficient funds triggers retry policy and notification**
* **Given** the scheduled $60.00 payment finds a $40.00 balance
* **When** the execution job runs
* **Then** the occurrence fails without overdrafting, Member A is notified immediately (US-11.1)
* **And** the payment retries per policy (up to 2 retries at 24 h intervals [PROPOSED]); after final failure the occurrence is marked failed and the schedule continues to the next period.

**Scenario 3 — Happy path: pause, edit, cancel**
* **Given** an active schedule
* **When** Member A pauses it, edits the amount to $75.00, or cancels it before the next cut-off
* **Then** the change takes effect for all future occurrences and is confirmed in-app
* **And** already-executed occurrences are unaffected.

**Scenario 4 — Edge: schedule dated in the past or on a non-processing day**
* **Given** Member A creates a one-off payment
* **When** they select yesterday's date, the API rejects with `422 Unprocessable Content`
* **And when** they select a date falling on a weekend/holiday for an ACH payee
* **Then** the UI discloses the adjusted processing date (next business day) before confirmation and stores it explicitly.

### US-4.4 — Expense Splitting & Payment Requests (M)

**Scenario 1 — Happy path: equal split with one-tap settlement**
* **Given** Member A has a $90.00 restaurant transaction in their Transaction Account history
* **When** they split it equally among themselves, Member B, and Member C (addressed per DEC-3)
* **Then** payment requests of $30.00 are sent to Members B and C with the transaction context
* **And when** Member B taps "Pay" and confirms
* **Then** a US-4.1 transfer of $30.00 settles and the request auto-reconciles to "paid", with Member A's tracker showing B paid / C outstanding.

**Scenario 2 — Negative: custom shares don't sum to the total**
* **Given** Member A chooses custom split amounts on the $90.00 transaction
* **When** they enter $30.00 + $40.00 + $30.00 (= $100.00)
* **Then** the client and server reject with `422 Unprocessable Content`: "shares must sum to $90.00"
* **And** no requests are issued.

**Scenario 3 — Negative: request to a non-member**
* **Given** Member A enters a phone number not registered to any ACTIVE member
* **When** they attempt to include it in a split
* **Then** the participant is rejected with "no member found for this identifier" (external links are out of scope)
* **And** the remaining valid participants can still be requested.

**Scenario 4 — Edge: recipient declines; reminder nudges**
* **Given** Member C received a $30.00 request
* **When** Member C declines it
* **Then** the request is marked declined and Member A is notified (the debt is not enforced by the platform)
* **And** for outstanding requests, Member A can send at most one reminder nudge per request per 24 hours [PROPOSED anti-spam rule].

---

## EP-5 — Card Management (CAP-5)

### EP-5 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** Virtual card issued automatically on Transaction Account opening; PAN/CVV reveal requires step-up authentication; wallet tokenization for Apple Pay and Google Pay; card transactions post to the Transaction Account and drive Round-Ups (US-5.1).
* **[CONFIRMED]** Physical card embossing uses `mrz_name_latin` verbatim — the platform never transliterates the Cyrillic name fields to produce an embossed name (DEC-6(b)) — and shipping uses the DEC-6 structured address (US-5.2).
* **[CONFIRMED]** Card controls (freeze, per-period spending limits, online/ATM/merchant-category toggles) are enforced at authorization time and take effect in seconds; all changes logged to US-13.3 (US-5.3).
* **[PROPOSED]** Virtual card expiry 3 years from issuance. (Sprint 1 draft.) [ADJUDICATED → see DEC-40 in 05_prd_and_roadmap.md: REJECTED — no platform-side expiry rule; defer to the issuer-processor (Lithic) default]
* **[PROPOSED]** Control-change propagation target ≤ 500 ms to the authorization decision path. (Sprint 1 draft; story only commits to "seconds".)
* **[PROPOSED]** Full PAN is never stored or logged by Digital Coop Bank systems outside the PCI-scoped issuer-processor integration; in-app reveal is fetched on demand and never cached. (Security engineering rule to ratify.)
* **[PROPOSED]** Frozen-card declines use a distinct decline reason ("card frozen") and trigger a member notification. (Sprint 1 draft behavior.)

### US-5.1 — Instant Virtual Debit Card & Wallet Tokenization (M)

**Scenario 1 — Happy path: automatic issuance and secure reveal**
* **Given** Member A's Transaction Account has just opened
* **When** the account-opened event is processed
* **Then** a virtual debit card is issued automatically and appears in the Cards tab
* **And when** Member A taps "Show card details" and passes step-up authentication (US-1.4)
* **Then** PAN, expiry, and CVV are displayed with a copy option, fetched live and never persisted on the device or in application logs.

**Scenario 2 — Happy path: wallet tokenization**
* **Given** Member A has the virtual card
* **When** they add it to Apple Pay or Google Pay from within the app
* **Then** a network token is provisioned to the wallet in a few taps
* **And** a wallet purchase authorizes against the Transaction Account balance and posts to it on settlement, driving Round-Ups (EP-10).

**Scenario 3 — Negative: reveal without valid step-up**
* **Given** Member A's session is active but the step-up challenge fails or is dismissed
* **When** the client calls the credential-reveal endpoint anyway
* **Then** the API responds `403 Forbidden` with reason "step-up required"
* **And** no card credential field is present in any response; the attempt is audit-logged.

**Scenario 4 — Edge: card spend posts and links downstream**
* **Given** Member A pays $12.40 with the virtual card and Round-Ups are enabled
* **When** the transaction settles
* **Then** it posts to the Transaction Account with category and merchant detail (US-3.2)
* **And** the Round-Up capture engine computes $0.60 against it (US-10.2), linked by transaction reference.

### US-5.2 — Physical Debit Card Ordering, Fulfilment & Activation (M)

**Scenario 1 — Happy path: order, track, activate, set PIN**
* **Given** Member A is `ACTIVE` with a verified DEC-6 address
* **When** they order a physical card
* **Then** the order uses the structured address for shipping and embosses `mrz_name_latin` exactly as captured
* **And** fulfilment status progresses ordered → printed → shipped → delivered in the app
* **And when** the card arrives and Member A activates it in-app and sets a PIN (entered twice, matching)
* **Then** the card becomes usable and PIN change is available thereafter behind step-up.

**Scenario 2 — Negative: PIN validation failure**
* **Given** Member A is setting their PIN
* **When** the confirmation entry does not match, or a trivially weak PIN is chosen (e.g., "0000", "1234") [PROPOSED denylist]
* **Then** the PIN is rejected with specific guidance
* **And** the card remains in its prior state (inactive if first activation).

**Scenario 3 — Negative (security): activation of someone else's card**
* **Given** Member B obtains Member A's card and attempts activation from Member B's authenticated session
* **When** the activation request is submitted with Member A's card reference
* **Then** the API responds `403 Forbidden` (ownership check)
* **And** Member A receives a security notification of the failed activation attempt.

**Scenario 4 — Edge: lost/stolen replacement**
* **Given** Member A reports their physical card lost
* **When** they request a replacement
* **Then** the old card is permanently blocked immediately (authorizations decline)
* **And** a replacement order enters the same fulfilment flow; the virtual card and wallet tokens remain usable unless the member also blocks them.

### US-5.3 — Card Controls (Freeze, Limits, Category Blocks) (S)

**Scenario 1 — Happy path: freeze declines instantly, unfreeze restores**
* **Given** Member A's virtual card is active
* **When** they toggle "Freeze card"
* **Then** the control propagates within seconds (target ≤ 500 ms [PROPOSED])
* **And** a merchant authorization attempt of $15.00 is declined with reason "card frozen" without checking funds, and Member A receives a notification naming the amount and merchant
* **And when** Member A unfreezes, subsequent authorizations are evaluated normally.

**Scenario 2 — Negative: spending limit exceeded**
* **Given** Member A set a $200.00 per-week spending limit and has spent $190.00 this week
* **When** a $25.00 authorization arrives
* **Then** it is declined for "limit exceeded" and logged with the control that fired
* **And** a $10.00 authorization would still be approved (boundary respected exactly).

**Scenario 3 — Edge: merchant-category and channel toggles**
* **Given** Member A disabled the "Gambling" merchant category and ATM withdrawals on their physical card
* **When** an authorization arrives from a gambling MCC, it is declined with the category control cited
* **And when** an e-commerce authorization arrives with online purchases still enabled
* **Then** it is approved — controls apply per card and per channel exactly as configured, and every control change is logged to US-13.3.

---

## EP-6 — Lending & Loan Circles (CAP-6)

### EP-6 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** `LoanStatus = DRAFT | SUBMITTED | UNDER_REVIEW | APPROVED | ACTIVE | DELINQUENT | PAID_OFF | DEFAULTED | WRITTEN_OFF`; `ACTIVE` begins at disbursement (DEC-20). Only ACTIVE members may apply or guarantee (DEC-4).
* **[CONFIRMED]** A Loan Circle forms when 3–5 ACTIVE invitees accept; members of the circle are "guarantors"; the pledged amount is a "guarantee pledge" (DEC-7). Pledges are locked for the loan term, excluded from withdrawal/transfer/Round-Up sweeps, and released pro-rata on principal repayment (US-6.4).
* **[CONFIRMED]** Underwriting weighs open-banking data, optional bureau data, and cooperative history; declines produce reasons and an adverse-action notice; parameters are US-12.5 configuration; decisions fully logged for fair-lending review (US-6.2).
* **[CONFIRMED]** Guarantee-pledge enforceability of share capital is Open Item 2 — hold mechanics behind a jurisdiction flag.
* **[CONFIRMED]** `WRITTEN_OFF` is admin-only via US-12.3 under dual approval; loan caps and pricing are US-12.5 configuration subject to `FINANCIAL_POLICY` governance (backlog reconciliation note).
* **[PROPOSED]** Launch loan amount bounds: minimum $100.00, maximum $1,000.00 (Sprint 1 draft; explicitly de-ratified in the backlog — seed as US-12.5 values). [ADJUDICATED → see DEC-45 in 05_prd_and_roadmap.md: final value min $100.00 / max $5,000.00 seed; the de-ratified $1,000.00 cap is not carried forward]
* **[PROPOSED]** Launch term options: 3, 6, or 12 months. (Sprint 1 draft.)
* **[PROPOSED]** Purpose field: required, 20–500 characters. (Sprint 1 draft.)
* **[PROPOSED]** Base rate: Sprint 1 proposed 8.00% APR; Sprint 2 proposed 12.00% APR for unsecured loans. **Conflicting drafts.** [ADJUDICATED → see DEC-48 in 05_prd_and_roadmap.md: final value 12.00% APR unsecured base rate (US-12.5 seed), discountable to 6.00% via Loan Circle coverage tiers per DEC-49]
* **[PROPOSED]** Tiered rate reduction by pledged coverage: 25–49% → −2.00 pp; 50–74% → −4.00 pp; ≥ 75% → −6.00 pp; rate floor 4.00% APR. (Sprint 1/2 drafts.)
* **[PROPOSED]** Circle invitations expire 7 calendar days after issue if the circle has not formed. (Sprint 2 draft.)
* **[PROPOSED]** Pledges are revocable before disbursement and locked from disbursement onward. (Sprint 2 draft.)
* **[PROPOSED]** `DELINQUENT` is set at the first missed installment after the grace period (grace period value TBD); `DEFAULTED` at 90 days past due. (Sprint 3 draft.) [ADJUDICATED → see DEC-52 in 05_prd_and_roadmap.md: grace period 10 calendar days; `DEFAULTED` at 90 days past due confirmed]
* **[PROPOSED]** Pooled Loan Circle size 3–12 participants; equal fixed contributions debited the same day monthly; payout order fixed at creation. (Sprint 3 draft — note DEC-7's 3–5 bound applies to guarantor Loan Circles, not the ROSCA variant; ROSCA bounds need PO confirmation.)
* **[PROPOSED]** Missed ROSCA contribution: alert the circle, retry once after 3 days, then apply the circle's configured backstop rule. [ADJUDICATED → see DEC-54 in 05_prd_and_roadmap.md: backstop menu defined — (a) circle absorbs shortfall pro-rata, (b) beneficiary payout reduced, or (c) member removed and forfeits position to end of rotation; chosen at circle creation]
* **Superseded — do not implement:** Sprint 3's "defaulting triggers automatic lockout of the member's cooperative share" (share treatment on default is governed by US-6.4 rules and Open Item 2, not an automatic seizure).

### US-6.1 — Digital Loan Application & Instant Conditional Offers (M)

**Scenario 1 — Happy path: apply and receive a conditional offer**
* **Given** Member A is `ACTIVE` with a Transaction Account
* **When** they select "Personal loan", enter amount $500.00 and term 6 months, watch the live repayment estimator update, enter purpose "Replacement laptop for freelance design work" (≥ 20 chars [PROPOSED]), and complete affordability declarations, then submit
* **Then** `LoanStatus` transitions `DRAFT → SUBMITTED` and decisioning (US-6.2) is invoked
* **And** the offer screen shows rate, repayment schedule, and total cost; where a Loan Circle is attached it shows the standard rate and the peer-guaranteed discounted rate side by side.

**Scenario 2 — Negative: non-ACTIVE applicant**
* **Given** Member B's `MembershipStatus = SUSPENDED`
* **When** they attempt to open or submit a loan application
* **Then** the API responds `403 Forbidden` with reason "only ACTIVE members may borrow" (US-2.2)
* **And** no `DRAFT` loan record is created via the submit path.

**Scenario 3 — Negative: input validation**
* **Given** Member A is completing the form
* **When** they enter $6,000.00 (above the $5,000.00 launch cap, adjudicated per DEC-45 in 05_prd_and_roadmap.md) or a 9-character purpose
* **Then** inline validation cites the specific bound ("maximum loan amount is $5,000.00" / "purpose must be at least 20 characters")
* **And** the server independently enforces the same bounds with `422 Unprocessable Content` (client validation is not the control).

**Scenario 4 — Edge: draft persistence**
* **Given** Member A abandons the application after entering amount and term
* **When** they return within the draft retention window
* **Then** the application reopens in `DRAFT` with entered values intact
* **And** submitting later re-runs the estimator against current US-12.5 rate configuration, not stale figures.

### US-6.2 — Automated Underwriting with Cooperative History (L)

**Scenario 1 — Happy path: approval with itemized cooperative discounts**
* **Given** Member A's application is `SUBMITTED` with open-banking data connected, 12 months of savings history, a clean repayment record, and high governance participation
* **When** the decision engine runs
* **Then** `LoanStatus` moves `SUBMITTED → UNDER_REVIEW → APPROVED`
* **And** the offer itemizes each cooperative-engagement discount separately (e.g., "savings history −0.50 pp, on-time repayment −0.50 pp, governance participation −0.50 pp" — values are US-12.5 parameters)
* **And** the full input snapshot, model/parameter version, and decision are logged (US-13.3) for fair-lending review.

**Scenario 2 — Negative: decline with reasons and adverse-action notice**
* **Given** Member B's application shows affordability below the configured threshold
* **When** the engine declines
* **Then** the applicant receives the principal decline reasons in plain language and a compliant adverse-action notice referencing data sources used
* **And** `LoanStatus` is terminal for this application; reapplication guidance is shown.

**Scenario 3 — Edge: referral to the manual queue**
* **Given** Member C's application scores in the configured referral band (neither clear approve nor decline)
* **When** the engine completes
* **Then** `LoanStatus` remains `UNDER_REVIEW` and a case is created in the US-12.3 referral queue with the full application, data inputs, and engine recommendation
* **And** the applicant sees "under review" with an expected turnaround, not a decline.

**Scenario 4 — Negative: open-banking data unavailable**
* **Given** Member D declines to connect open banking and no bureau consent is given
* **When** the engine runs on cooperative-history factors alone
* **Then** it produces a decision or referral per configuration without erroring
* **And** the absence of a data source is never itself recorded as a negative factor unless the configured policy explicitly says so (and that policy is logged).

**Scenario 5 — Edge: parameter change mid-flight**
* **Given** a US-12.5 underwriting-parameter change becomes effective while Member E's application is `UNDER_REVIEW`
* **Then** the decision uses the parameter version captured at submission, recorded on the decision log
* **And** re-submission after expiry of the offer uses current parameters.

### US-6.3 — Loan Circle Creation & Guarantor Invitations (M)

**Scenario 1 — Happy path: circle forms at 3 acceptances**
* **Given** Member A has a loan application for $1,000.00 over 12 months
* **When** they create a Loan Circle and invite Members B, C, D, and E per DEC-3, each invitation disclosing amount, term, and requested pledge
* **And** Members B, C, and D accept after viewing the risk disclosure
* **Then** the circle status becomes "formed" (3–5 acceptances per DEC-7)
* **And** underwriting is notified that a circle is attached so the discounted rate can be presented (US-6.1/US-6.2).

**Scenario 2 — Negative: invitee not ACTIVE**
* **Given** Member F's `MembershipStatus = SUSPENDED`
* **When** Member A invites Member F
* **Then** the invitation is refused with "no active cooperative member found for this identifier" without status leakage
* **And** the circle's invitee count is unchanged.

**Scenario 3 — Negative: frictionless, private decline**
* **Given** Member E received an invitation
* **When** Member E declines
* **Then** the decline requires no reason and completes in one tap
* **And** Member A sees only that the invitation was not accepted; other invitees are never shown who declined.

**Scenario 4 — Edge: circle size bounds and expiry**
* **Given** 5 invitees have accepted
* **When** Member A attempts a 6th invitation, it is rejected: "a Loan Circle has at most 5 guarantors" (DEC-7)
* **And given** only 2 invitees have accepted when the 7-day invitation window lapses [PROPOSED]
* **Then** outstanding invitations expire, the circle does not form, and Member A is prompted to re-invite or proceed at the standard rate.

### US-6.4 — Guarantee Pledge Locking, Rate Reduction & Release (L)

**Scenario 1 — Happy path: pledge, e-sign, lock**
* **Given** Member B is a guarantor in Member A's formed circle with an available savings balance of $500.00
* **When** Member B pledges $200.00, passes step-up authentication, and e-signs the pledge agreement (US-6.6) spelling out default consequences
* **Then** a $200.00 guarantee-pledge lock is placed: available balance becomes $300.00 while total balance stays $500.00
* **And** the locked amount is excluded from withdrawals, transfers, and Round-Up sweeps
* **And** Member B's guarantor dashboard shows the outstanding pledge and total exposure.

**Scenario 2 — Negative: pledge exceeds available balance**
* **Given** Member C has $150.00 available (net of existing locks)
* **When** they attempt to pledge $200.00
* **Then** the pledge is rejected with "pledge cannot exceed your available balance of $150.00"
* **And** no lock is created.

**Scenario 3 — Happy path: tiered rate reduction applied**
* **Given** Member A's $1,000.00 loan has total pledges of $600.00 (60% coverage)
* **When** underwriting prices the offer
* **Then** the Tier-2 discount (−4.00 pp [PROPOSED tiers]) applies against the base rate, and the offer shows exactly how the circle's $600.00 reduced the rate
* **And if** a guarantor revokes a $200.00 pledge before disbursement [PROPOSED revocability], acceptance is blocked and the offer reprices at 40% coverage (Tier 1, −2.00 pp) before Member A can sign.

**Scenario 4 — Happy path: pro-rata release on repayment**
* **Given** Member A's disbursed loan is backed by Member B's $200.00 pledge covering 20% of the $1,000.00 principal
* **When** Member A repays $300.00 of principal
* **Then** Member B's lock is reduced pro-rata by $60.00 (20% × $300.00) to $140.00
* **And** the release posts automatically with a notification and a ledger entry linking loan, payment, and release.

**Scenario 5 — Edge: default treatment behind the jurisdiction flag**
* **Given** Member A's loan transitions to `DEFAULTED` with $500.00 principal outstanding and pledges locked
* **When** the default protocol is applied by US-12.3 staff per US-6.4 rules
* **Then** pledge application to the outstanding balance follows the jurisdiction-flagged mechanism (Open Item 2) — never an unreviewed automatic seizure
* **And** each affected guarantor is notified of the exact amount applied, with the decision trail in the audit log.

### US-6.5 — Pooled Loan Circle (ROSCA) (XL)

**Scenario 1 — Happy path: circle creation with fixed schedule and order**
* **Given** Member A creates a Pooled Loan Circle with contribution $50.00/month, duration 4 months, participants Members A–D, and payout order randomized at creation
* **When** all four participants accept the terms (including the fixed order)
* **Then** the circle activates with the contribution amount, duration, participant list, and payout order immutable from that point
* **And** every participant sees the full schedule: who receives $200.00 in which month.

**Scenario 2 — Happy path: monthly collection and lump-sum payout**
* **Given** the active circle reaches collection day of month 1 and all participants have sufficient balances
* **When** the collection job runs
* **Then** $50.00 is debited from each participant's designated account (4 × $50.00) and $200.00 is paid in one lump sum to the month-1 beneficiary, interest-free
* **And** the circle ledger visible to all participants records every debit and the payout, each with an idempotency-keyed posting.

**Scenario 3 — Negative: missed contribution handling**
* **Given** month 2's collection finds Member B with a $10.00 balance
* **When** the $50.00 debit fails
* **Then** the payout to the month-2 beneficiary is withheld pending resolution, the circle is alerted (US-11.1), and a retry is scheduled per the configured policy [PROPOSED: one retry after 3 days]
* **And** if the retry fails, the circle's configured backstop rule applies and the shortfall handling is recorded in the circle ledger — Member B's membership share is not automatically seized (superseded draft rule).

**Scenario 4 — Negative: joining and integrity rules**
* **Given** an activated circle
* **When** a fifth member requests to join mid-cycle, or a participant attempts to change the payout order or contribution amount
* **Then** each request is rejected with `409 Conflict` — composition, amount, and order are fixed at creation
* **And when** a non-participant requests the circle ledger, the API responds `403 Forbidden`/`404 Not Found`.

**Scenario 5 — Edge: final rotation closes the circle**
* **Given** month 4's collection and payout complete for the last beneficiary
* **When** the cycle ends
* **Then** the circle status becomes completed, no further debits are scheduled
* **And** the full ledger remains readable to all participants, and totals reconcile: each participant paid $200.00 in and received exactly one $200.00 payout.

### US-6.6 — E-Signature & Loan Document Vault (M)

**Scenario 1 — Happy path: e-sign a loan agreement**
* **Given** Member A's loan is `APPROVED` and the agreement is generated from the configured template
* **When** they review the agreement and sign after step-up authentication (US-1.4)
* **Then** the signature ceremony records the signer identity binding, timestamp, and document hash (tamper evidence)
* **And** the signed agreement is stored encrypted in the vault and immediately retrievable by Member A.

**Scenario 2 — Happy path: vault retrieval any time**
* **Given** Member A has a signed loan agreement and a signed guarantee-pledge agreement (as guarantor for Member B)
* **When** they open the document vault
* **Then** both documents are listed with type, counterpart, date, and status, and download works
* **And** P-5 access to the same documents flows only through US-12.3 with its own authorization and audit trail.

**Scenario 3 — Negative (security): access to another member's documents**
* **Given** Member C is authenticated
* **When** Member C requests a vault document belonging to Member A by document ID
* **Then** the API responds `403 Forbidden`/`404 Not Found`
* **And** the attempt is audit-logged.

**Scenario 4 — Edge: tamper-evidence verification**
* **Given** a stored signed agreement
* **When** an integrity check recomputes the document hash and compares it to the hash sealed at signing
* **Then** an unmodified document verifies; any byte-level modification fails verification and raises an operational alert
* **And** the vault never permits in-place overwrite of a signed document (new versions are new signed documents).

### US-6.7 — Loan Servicing, Disbursement & Flexible Repayment (L)

**Scenario 1 — Happy path: disbursement on signing**
* **Given** Member A's loan is `APPROVED` and the agreement is signed (US-6.6)
* **When** disbursement executes with an idempotency key
* **Then** $500.00 is credited to Member A's Transaction Account exactly once and `LoanStatus` transitions `APPROVED → ACTIVE`
* **And** the amortization schedule, first due date, and autopay setup are visible immediately; guarantors are notified that pledges are now locked for the term (US-6.4).

**Scenario 2 — Happy path: autopay with retry**
* **Given** autopay is enabled for the $88.20 monthly installment
* **When** the due date arrives with sufficient funds, the installment collects and the schedule advances
* **And when** a later installment fails for insufficient funds
* **Then** the retry policy runs [PROPOSED: retries per EP-4 rules] with member notification before each attempt
* **And** repeated failure past the grace period hands off to US-6.8 (`DELINQUENT` transition per the [PROPOSED] milestone rule).

**Scenario 3 — Happy path: payoff quote and early repayment**
* **Given** Member A's loan has $300.00 principal outstanding
* **When** they request a full payoff quote
* **Then** the quote shows principal, accrued interest to the quoted date, any configured fees (US-12.5), and a validity window
* **And when** they pay the quoted amount within the window
* **Then** `LoanStatus` transitions to `PAID_OFF`, remaining pledge locks release in full (US-6.4), and a closure statement is issued.

**Scenario 4 — Edge: seasonal/income-linked schedule**
* **Given** Member B (P-3) selects a seasonal schedule with reduced installments in configured low-income months
* **When** the schedule is generated
* **Then** total repayment over the term equals principal plus interest computed on actual outstanding balances (no hidden cost versus the disclosed APR)
* **And** the member sees a month-by-month comparison against the standard schedule before accepting.

**Scenario 5 — Negative: overpayment/idempotency on repayment**
* **Given** Member A submits an extra payment of $100.00 and the client retries on timeout with the same idempotency key
* **Then** exactly one $100.00 payment posts, principal reduces once, and the pro-rata pledge release fires once
* **And** an attempted payment exceeding the payoff amount is capped at payoff with the surplus never collected.

### US-6.8 — Arrears Monitoring, Guarantor Alerts & Hardship Rescheduling (M)

**Scenario 1 — Happy path: early warning before the miss**
* **Given** Member A's $88.20 installment is due in 3 days and their Transaction Account holds $40.00
* **When** the early-warning trigger evaluates
* **Then** Member A receives a non-punitive notification stating the shortfall and clear options (top up, adjust autopay date, request hardship reschedule)
* **And** no negative status change occurs from the warning itself.

**Scenario 2 — Happy path: guarantor alerts at defined milestones**
* **Given** Member A's circle-backed loan becomes `DELINQUENT` and reaches the first configured guarantor-notification milestone
* **When** the milestone fires
* **Then** each guarantor is notified of the delinquency stage and their potential exposure, before any pledge is drawn
* **And** guarantors are never notified ahead of the configured milestone (borrower privacy until then).

**Scenario 3 — Happy path: hardship reschedule request**
* **Given** Member A anticipates two low-income months
* **When** they submit a self-service hardship request proposing reduced installments
* **Then** the proposal routes to US-12.3 for staff approval; the loan's current schedule remains in force until approval
* **And** on approval the new schedule takes effect, the borrower and guarantors are notified, and the collections case is updated.

**Scenario 4 — Negative: hardship request on an ineligible loan**
* **Given** Member B's loan is `PAID_OFF` (or `WRITTEN_OFF`)
* **When** they attempt a hardship reschedule request
* **Then** the request is rejected with `409 Conflict` reason "loan not in a reschedulable state"
* **And** no case is created.

---

## EP-7 — Dividends & Surplus Distribution (CAP-7)

### EP-7 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** "Patronage Dividend", annual cycle, ratified at the AGM, paid within 5 business days of ratification (DEC-10, KPI-4.3). Patronage factors: savings balances, transaction volume, loan repayment performance, governance participation. Factor weights are US-12.5 configuration subject to `FINANCIAL_POLICY` proposals — never hard-coded.
* **[CONFIRMED]** Reconciliation invariant: the sum of member entitlements equals the distributable pool (US-7.1). Calculation runs are deterministic and re-runnable.
* **[CONFIRMED]** Member election between Primary Savings payout and share-capital reinvestment, settable any time before the run (US-7.2). All estimator projections labeled "estimated" (DEC-15); estimator refreshed at least daily (US-7.3).
* **[PROPOSED]** Estimator scenario bands: Conservative = 80%, Expected = 100%, High = 120% of the forecast surplus. (Sprint 2 draft.)
* **[PROPOSED]** Members with zero patronage activity in the year receive a $0.00 entitlement statement (not an error). (Draft-implied; PO to confirm statement handling.)
* **Superseded — do not implement:** quarterly payout framing (Sprint 1/2 drafts) — DEC-10 fixes the annual cycle with a real-time estimator; dividend proportional to share count (one $25.00 share; patronage factors, not shareholding, drive the dividend).

### US-7.1 — Patronage Calculation Engine (L)

**Scenario 1 — Happy path: calculation run reconciles exactly**
* **Given** the AGM-ratified surplus yields a distributable pool of $600,000.00 and factor weights are configured via US-12.5 (linked to their certified `FINANCIAL_POLICY` ballot)
* **When** the calculation run executes over the year's accumulated per-member factor data
* **Then** every eligible member receives an entitlement computed from the weighted factors
* **And** the reconciliation total satisfies Σ entitlements = $600,000.00 to the minor unit, with the rounding-remainder allocation rule documented and applied deterministically.

**Scenario 2 — Happy path: explainability statement**
* **Given** Member A's entitlement is $84.60
* **When** they open the entitlement statement (post-approval)
* **Then** it breaks the amount down by factor (savings balances, transaction volume, loan repayment performance, governance participation) with the weight and the member's measured value for each
* **And** the statement identifies the surplus figure, the ratifying AGM record, and the weight-configuration version used.

**Scenario 3 — Edge: deterministic re-run**
* **Given** a completed calculation run
* **When** the run is re-executed with identical inputs (same surplus, weights version, factor snapshot)
* **Then** every member's entitlement is identical to the minor unit
* **And** the re-run is recorded as a distinct run instance referencing the same input snapshot.

**Scenario 4 — Negative: reconciliation failure aborts**
* **Given** a defect causes Σ entitlements = $599,999.87 against a $600,000.00 pool
* **When** the reconciliation check runs
* **Then** the run is marked failed, no entitlement becomes payable, and US-12.6 is alerted with the discrepancy detail
* **And** payout (US-7.2) cannot be invoked against a failed run.

**Scenario 5 — Negative: unratified inputs rejected**
* **Given** an operator supplies a surplus figure with no linked AGM ratification record, or weights not linked to their governing ballot where required
* **When** the run is requested
* **Then** the engine refuses to execute with a validation error naming the missing linkage
* **And** the refusal is audit-logged.

### US-7.2 — Automated Dividend Payout with Member Election (M)

**Scenario 1 — Happy path: payout per standing election within 5 business days**
* **Given** the calculation run is approved via US-12.6 and Member A's standing election is "Primary Savings", Member B's is "reinvest as share capital"
* **When** the batch payout executes
* **Then** Member A's $84.60 posts to their Primary Savings Account and Member B's entitlement posts to their Membership Share Account as equity
* **And** both receive a notification with the amount and a link to the explainability breakdown
* **And** 100% of approved entitlements are posted within 5 business days of AGM ratification (KPI-4.3), with each posting idempotency-keyed.

**Scenario 2 — Negative: execution without approval**
* **Given** a calculation run exists but US-12.6 dual approval has not completed
* **When** any actor invokes the payout batch
* **Then** the request is rejected with `403 Forbidden` reason "run not approved"
* **And** no posting occurs.

**Scenario 3 — Negative: failed posting handled without stopping the batch**
* **Given** the batch reaches Member C whose `MembershipStatus = CLOSED` since the snapshot
* **When** the posting fails
* **Then** the batch records the exception with a reason code and continues processing remaining members
* **And** the exception appears in the US-12.6 reconciliation report for manual disposition (e.g., redemption-channel payment per bylaws).

**Scenario 4 — Edge: election changed just before the run**
* **Given** Member D changes their election from savings to reinvestment 1 hour before batch execution
* **When** the batch runs
* **Then** the election in force at execution time applies, and the confirmation notification states the destination
* **And** election changes submitted after execution affect only future runs.

### US-7.3 — Real-Time Dividend Estimator (M)

**Scenario 1 — Happy path: projection with behavior linkage**
* **Given** Member A has current-year factor data and a cooperative surplus forecast exists
* **When** they open the Dividend Estimator
* **Then** a projected annual Patronage Dividend is displayed, labeled "estimated" (DEC-15), refreshed at least daily with the refresh timestamp shown
* **And** behavior-linked suggestions quantify effects, each also labeled "estimated" (e.g., "voting in the open ballot raises your estimate by ~$1.20").

**Scenario 2 — Negative: forecast inputs unavailable**
* **Given** the surplus-forecast input feed is unreachable
* **When** Member A opens the estimator
* **Then** the last successfully computed projection is shown with its as-of timestamp and a clear staleness notice
* **And** if no projection has ever been computed, the screen explains estimates are unavailable rather than showing $0.00 as if it were a result.

**Scenario 3 — Edge: zero or negative forecast surplus**
* **Given** the forecast surplus is $0.00 (or negative)
* **When** the estimator computes
* **Then** the projection displays $0.00 labeled "estimated" with an explanation that dividends depend on the cooperative generating a surplus
* **And** no behavior suggestion promises a positive dividend effect.

**Scenario 4 — Edge: brand-new member**
* **Given** Member E activated yesterday with no factor history
* **When** they open the estimator
* **Then** an onboarding-friendly state explains how patronage factors build the dividend, with a near-$0.00 estimate rather than an error.

### US-7.4 — Dividend & Tax Statements (M)

**Scenario 1 — Happy path: annual statement retrieval**
* **Given** the payout run completed and Member A received $84.60 to savings
* **When** statements generate post-payout
* **Then** Member A can view and download an annual statement showing the dividend amount, factor breakdown, and payout destination, plus the jurisdictional tax artifact from the configured template
* **And** a delivery notification is sent via US-11.1.

**Scenario 2 — Happy path: aggregate extract for P-5**
* **Given** statements are generated
* **When** Operator A requests the aggregate reporting extract
* **Then** the extract totals reconcile exactly to the payout run's reconciliation report
* **And** the extract is available only to authorized P-5 roles.

**Scenario 3 — Negative (security): cross-member statement access**
* **Given** Member B is authenticated
* **When** they request Member A's statement by document ID
* **Then** the API responds `403 Forbidden`/`404 Not Found` and the attempt is audit-logged.

**Scenario 4 — Edge: member closed after payout**
* **Given** Member C received a dividend in the run and later became `CLOSED`
* **When** the annual statements are issued
* **Then** Member C's statement and tax artifact are still generated and delivered via the retained contact channel per US-13.6 retention rules
* **And** financial-records retention overrides any deletion request for the statutory period.

---

## EP-8 — Democratic Governance & Voting (CAP-8)

### EP-8 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** One member, one vote; secret ballot; `VoteChoice = FOR | AGAINST | ABSTAIN` (DEC-1); `BallotType = PROPOSAL | BOARD_ELECTION` (DEC-2); `ProposalStatus` per DEC-9 with quorum failures recorded as `REJECTED` with reason `QUORUM_NOT_MET`.
* **[CONFIRMED]** Eligibility per the ballot-open snapshot (US-2.3); step-up authentication at vote submission (US-1.4); verifiable receipt that never reveals vote content; a delegator's direct vote supersedes the delegate-cast vote for that ballot only (DEC-8).
* **[CONFIRMED]** Proxy Delegation: scoped per `ProposalCategory` and/or `BOARD_ELECTION`, exactly one ACTIVE delegate per scope, single-level (no re-delegation), instantly revocable, delegate consent required; delegated participation counts toward the delegator's Governance Participation Rate (DEC-8, DEC-16).
* **[CONFIRMED]** Discussion threads lock automatically at `OPEN_FOR_VOTING`; moderation actions audit-logged (US-8.6). Voting windows and quorum are US-12.4 configuration.
* **[PROPOSED]** Co-signature threshold: 500 signatures within a 30-day gathering window. (Sprint 3 draft; the backlog only says "configured threshold".) [ADJUDICATED → see DEC-57 in 05_prd_and_roadmap.md: final value greater of 25 signatures or 0.5% of ACTIVE members, 30-day window (config seed)]
* **[PROPOSED]** Proposal field lengths: title 10–100 characters, summary 50–500, body 100–5,000. (Sprint 3 draft.)
* **[PROPOSED]** The proposal author is counted as sponsor and cannot co-sign their own proposal. (Sprint 3 draft.)
* **[PROPOSED]** Co-signatures cannot be withdrawn once given. (Sprint 3 draft — PO to confirm; interacts with the threshold automation.)
* **Superseded — do not implement:** `YES/NO` vote choices (DEC-1); transitive/liquid delegation and circular-delegation traversal (DEC-8 single-level makes cycles structurally impossible); point-allocation grant voting (Sprint 2 draft — grants are decided by ordinary `COMMUNITY_GRANT` ballots per US-9.3); "Archived" proposal status (DEC-9 has no such value — an expired draft is `WITHDRAWN` or remains `DRAFT` per PO decision, flagged for confirmation).

### US-8.1 — Voting Portal: Browse Ballots & Cast a Secret Ballot (L)

**Scenario 1 — Happy path: browse with full context**
* **Given** Member A is `ACTIVE` and three ballots are open
* **When** they open the voting portal
* **Then** each ballot lists title, category, rationale, discussion link, closing time, and live participation percentage
* **And** filters for open / voted / closed each return the correct sets.

**Scenario 2 — Happy path: cast a secret ballot with receipt**
* **Given** Member A is in the eligibility snapshot for ballot G-42 and has not voted
* **When** they select `FOR`, pass step-up authentication, and submit
* **Then** the vote is recorded with the tally incremented and the member marked as having participated
* **And** Member A receives a verifiable receipt confirming inclusion in the tally without revealing the choice
* **And** the stored participation record is decoupled from the stored choice (secret ballot) — no API or admin view joins member identity to `VoteChoice`.

**Scenario 3 — Negative: double vote**
* **Given** Member A already voted on ballot G-42
* **When** a second vote submission arrives (UI bypass, direct POST)
* **Then** the API responds `409 Conflict` "already voted"
* **And** tallies are unchanged.

**Scenario 4 — Negative: vote after close**
* **Given** ballot G-42 closes at 20:00:00
* **When** a submission reaches the server at 20:00:01
* **Then** it is rejected with "voting has closed" and the tally is unchanged
* **And** closing-time comparison uses server time, not client time.

**Scenario 5 — Negative (security): ineligible voter**
* **Given** Member B is not in ballot G-42's snapshot (activated after open, or `SUSPENDED`)
* **When** they submit a vote
* **Then** the API responds `403 Forbidden` with the eligibility reason
* **And** the attempt is audit-logged without creating any tally effect.

**Scenario 6 — Edge: direct vote supersedes delegated vote**
* **Given** Member A delegated `FINANCIAL_POLICY` to Member B, and Member B already cast `FOR` on Member A's behalf on ballot G-42
* **When** Member A votes `AGAINST` directly before close
* **Then** the delegate-cast vote for Member A is voided for this ballot only and the tally moves accordingly (FOR −1, AGAINST +1)
* **And** Member B is not informed how Member A voted; the delegation itself remains intact for other ballots (DEC-8).

### US-8.2 — Proposal Builder with Co-Signature Gathering (L)

**Scenario 1 — Happy path: draft → co-sign → SUBMITTED at threshold**
* **Given** Member A (P-4) drafts a proposal with title, summary, body, and `ProposalCategory = COMMUNITY_GRANT`
* **When** they publish the `DRAFT` for co-signature
* **Then** members see the draft with a progress bar toward the configured threshold (seed per DEC-57 in 05_prd_and_roadmap.md: greater of 25 signatures or 0.5% of ACTIVE members)
* **And when** the distinct ACTIVE co-signature count reaches the configured threshold
* **Then** the status transitions automatically `DRAFT → SUBMITTED` and the proposal enters the US-12.4 review/scheduling queue with the author notified.

**Scenario 2 — Happy path: withdrawal before ballot open**
* **Given** Member A's proposal is `SUBMITTED` but not yet scheduled
* **When** the author withdraws it
* **Then** the status becomes `WITHDRAWN` (available to the author any time before ballot open, DEC-9)
* **And** co-signers are notified and the proposal leaves the scheduling queue.

**Scenario 3 — Negative: duplicate co-signature**
* **Given** Member B already co-signed the draft
* **When** Member B signs again
* **Then** the API responds `409 Conflict` and the count is unchanged
* **And** the author cannot co-sign their own proposal [PROPOSED rule] — attempting returns `403 Forbidden` with "authors are the sponsor".

**Scenario 4 — Negative: invalid category or field bounds**
* **Given** a client submits a draft with category "FUNDING_ALLOCATION" (a superseded value) or a 6-character title
* **When** validation runs
* **Then** the API responds `422 Unprocessable Content` listing valid `ProposalCategory` values and field bounds [PROPOSED lengths]
* **And** nothing is persisted.

**Scenario 5 — Edge: status transitions guarded**
* **Given** a proposal is `OPEN_FOR_VOTING`
* **When** the author attempts `WITHDRAWN`, or any client attempts to edit the body
* **Then** both are rejected with `409 Conflict` — content and lifecycle are frozen from ballot open
* **And** `OPEN_FOR_VOTING` can only ever be set by US-12.4 ballot scheduling, enforced server-side.

### US-8.3 — Board Elections (L)

**Scenario 1 — Happy path: choose-up-to-N ballot**
* **Given** a `BOARD_ELECTION` ballot with 2 open seats and 5 candidates, each with profile and statement
* **When** Member A reviews candidates, selects 2, passes step-up, and submits
* **Then** both candidate tallies increment, Member A is marked as having participated once, and a receipt is issued (same secret-ballot engine as US-8.1)
* **And** selecting fewer than 2 (e.g., 1) is also valid — "up to" N.

**Scenario 2 — Negative: over-selection**
* **Given** the 2-seat ballot
* **When** Member A attempts to select a 3rd candidate
* **Then** the client blocks the selection and the server independently rejects a 3-candidate payload with `422 Unprocessable Content` "maximum 2 selections"
* **And** no partial ballot is recorded.

**Scenario 3 — Negative: double ballot**
* **Given** Member A already submitted their election ballot
* **When** a second submission arrives
* **Then** the API responds `409 Conflict` and tallies are unchanged (one member, one ballot).

**Scenario 4 — Negative: submission after the window**
* **Given** the election closes at 18:00:00 server time
* **When** a ballot arrives at 18:00:02
* **Then** it is rejected with "the election has closed" and is not recorded.

**Scenario 5 — Edge: certified results and term tracking**
* **Given** the election closed and US-12.4 certification completed under maker-checker
* **When** results publish
* **Then** members see per-candidate totals, turnout (Governance Participation Rate per DEC-16), and the elected directors
* **And** term records are created for the winners with start/end dates, and the certified result is archived immutably (US-8.7).

### US-8.4 — Proxy Delegation Setup (M)

**Scenario 1 — Happy path: category-scoped delegation with consent**
* **Given** Member A is `ACTIVE` and Member B is `ACTIVE` and has consented to receive delegations
* **When** Member A selects scope `FINANCIAL_POLICY`, picks Member B per DEC-3, and confirms with step-up authentication
* **Then** the delegation is recorded for that scope only and appears on Member A's governance dashboard
* **And** Member A's participation via Member B counts toward Member A's Governance Participation Rate (DEC-16).

**Scenario 2 — Negative: delegate has not consented or is not ACTIVE**
* **Given** Member C has not opted in to receive delegations (or is `SUSPENDED`)
* **When** Member A attempts to delegate to Member C
* **Then** the request is rejected with the applicable reason ("member does not accept delegations" / "no active member found")
* **And** no delegation record is created.

**Scenario 3 — Negative: self-delegation**
* **Given** Member A selects an identifier resolving to themselves
* **When** the delegation is submitted
* **Then** it is rejected with `422 Unprocessable Content` "cannot delegate to yourself".

**Scenario 4 — Negative (security): single-level enforcement**
* **Given** Member B holds Member A's `FINANCIAL_POLICY` delegation
* **When** Member B attempts to delegate their `FINANCIAL_POLICY` scope onward to Member D
* **Then** Member B's own vote may be delegated, but the received (Member A's) voting power is never transitively passed — on any ballot Member D casts at most Member B's own delegated vote
* **And** the server enforces single-level semantics (DEC-8); no delegation chain longer than one hop can affect any tally.

### US-8.5 — Proxy Revocation & Direct-Vote Override (M)

**Scenario 1 — Happy path: one-tap revocation**
* **Given** Member A has an active `FINANCIAL_POLICY` delegation to Member B
* **When** Member A taps "Revoke" and confirms with step-up
* **Then** the delegation ends immediately; direct voting is restored for the scope, effective for all ballots not yet voted by the delegate and all future ballots
* **And** the dashboard reflects the change instantly.

**Scenario 2 — Happy path: direct override on an open ballot**
* **Given** Member B cast `FOR` on ballot G-50 carrying Member A's delegated vote
* **When** Member A votes `AGAINST` directly before close
* **Then** Member A's delegated contribution to `FOR` is voided and `AGAINST` gains their direct vote — for this ballot only (DEC-8)
* **And** the delegation itself stays active for other ballots, and Member B cannot see Member A's choice (secret ballot preserved).

**Scenario 3 — Negative: override after close**
* **Given** ballot G-50 has closed with the delegate's vote counted
* **When** Member A attempts a direct override
* **Then** the submission is rejected with "voting has closed"; the certified tally is unchanged.

**Scenario 4 — Edge: delegate becomes SUSPENDED**
* **Given** Member B (holding delegations from Members A and E) transitions `ACTIVE → SUSPENDED`
* **When** the status change is processed
* **Then** all delegations to Member B auto-void immediately, delegators are notified with a prompt to vote directly or re-delegate
* **And** votes Member B validly cast on their behalf before suspension on still-open ballots remain per PO-confirmed policy [PROPOSED: they stand unless overridden].

### US-8.6 — Proposal Discussion Threads (M)

**Scenario 1 — Happy path: threaded debate**
* **Given** a proposal is published for co-signature
* **When** Member A posts a comment and Member B replies
* **Then** the thread displays nested replies with author Member IDs/display names and timestamps
* **And** posting requires an ACTIVE membership; threads exist only on proposals (no general feed).

**Scenario 2 — Happy path: report and moderate**
* **Given** Member C posts content violating community standards
* **When** Member B reports it and a moderator hides it with a recorded reason
* **Then** the post shows as hidden-with-reason (not silently deleted), the reporter is notified of the outcome
* **And** the moderation action (actor, reason, timestamp) is written to the audit log (US-13.3).

**Scenario 3 — Negative: posting to a locked thread**
* **Given** the proposal transitions to `OPEN_FOR_VOTING`, which locks the thread automatically
* **When** any member attempts a new post or reply
* **Then** the API responds `409 Conflict` "thread locked at ballot open"
* **And** the full thread remains readable as a read-only record.

**Scenario 4 — Edge: reporter/author boundary**
* **Given** Member C's post was hidden
* **When** Member C views the thread
* **Then** they see their own post's hidden status and the standards reason, with the appeal route
* **And** other members cannot see the hidden content; moderators retain access via the moderation queue.

### US-8.7 — Governance Archive & Audit Trail (M)

**Scenario 1 — Happy path: complete, searchable archive**
* **Given** a proposal completed its DEC-9 lifecycle and a board election was certified
* **When** any member searches the archive
* **Then** they can retrieve the proposal's full history (statuses with timestamps, ballot, turnout as Governance Participation Rate, certified outcome `PASSED`/`REJECTED`), certified election results, and uploaded minutes
* **And** the archive is readable by all members regardless of whether they voted.

**Scenario 2 — Happy path: quorum failure recorded transparently**
* **Given** a ballot closed with participation below the configured quorum
* **When** US-12.4 certifies the outcome
* **Then** the archive records `REJECTED` with reason `QUORUM_NOT_MET`, the actual participation rate, and the quorum requirement in force.

**Scenario 3 — Negative (security): archive immutability**
* **Given** an archived certified result
* **When** any API client — including a P-5 role — attempts to modify or delete the archived record
* **Then** the request is rejected (`403 Forbidden`); corrections may only be appended as annotated amendments referencing the original
* **And** the underlying storage is the US-13.3 append-only log, so tamper evidence applies.

---

## EP-9 — Community Funding Hub (CAP-9)

### EP-9 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** DEC-14 noun set verbatim: Community Project, Backing, Community Grant, Surplus Match (≤ 1:1). Community Grant pool funded at 10% of annual surplus (KPI-4.2). Match release is governed by `COMMUNITY_GRANT` ballots, not staff discretion (US-9.3). Admin review precedes any publication (US-9.1). Backing refunds if a project misses its goal by deadline follow a configurable all-or-nothing rule (US-9.2). All modeled impact figures labeled "estimated" (DEC-15).
* **[PROPOSED]** Pitch validation: title 10–100 characters; funding goal between $1,000.00 and $100,000.00; at least one supporting document (PDF). (Sprint 2 draft.)
* **[PROPOSED]** Campaign duration: Sprint 2 proposed 30–365 days; Sprint 3 proposed 1–90 days. **Conflicting drafts.** [ADJUDICATED → see DEC-64 in 05_prd_and_roadmap.md: final value 14–120 days (config seed)]
* **[PROPOSED]** Per-project Surplus Match cap default $500.00 until configured otherwise. (Sprint 3 draft example; cap existence is confirmed.) [ADJUDICATED → see DEC-65 in 05_prd_and_roadmap.md: default cap 10% of the project's funding goal, capped at $10,000 (config seed)]
* **[PROPOSED]** Backings are held in a project-specific escrow ledger until goal/deadline resolution. (Sprint 2/3 drafts; consistent with the refund rule, mechanism needs PO confirmation.)
* **Superseded — do not implement:** "investment certificates" with yield/maturity terms (Sprint 2 draft) — a Backing is a contribution per DEC-14, and any yield/return language must be labeled "estimated" per DEC-15; point-allocation grant voting (see EP-8 note).

### US-9.1 — Community Project Pitch Submission & Review (M)

**Scenario 1 — Happy path: submit, review, publish**
* **Given** Member A (P-4) completes the structured pitch form — goals, budget $50,000.00, timeline, impact description — and uploads a project brief PDF
* **When** they submit
* **Then** the Community Project is created in a pending-review state, invisible to members
* **And when** an admin approves it in the review queue
* **Then** it publishes to the Pitch Board with funding progress at $0.00 and the submitter is notified.

**Scenario 2 — Negative: decline with reasons**
* **Given** a submitted project fails review (e.g., budget unsubstantiated)
* **When** the admin declines with reasons
* **Then** the project is not published, the submitter receives the reasons and may revise and resubmit
* **And** the decision is audit-logged.

**Scenario 3 — Negative: validation failure**
* **Given** Member A submits a pitch with a $500.00 goal and no supporting document
* **When** validation runs
* **Then** the API responds `422 Unprocessable Content` with both errors ("goal must be at least $1,000.00" [PROPOSED], "at least one supporting document is required" [PROPOSED])
* **And** nothing enters the review queue.

**Scenario 4 — Negative (security): ineligible submitter**
* **Given** a `SUSPENDED` member, or an organization not registered with the cooperative
* **When** they POST a project submission
* **Then** the API responds `403 Forbidden`
* **And** no draft project is created.

### US-9.2 — Backing a Community Project from Savings (M)

**Scenario 1 — Happy path: one-time Backing with live progress**
* **Given** Member A has $800.00 available in their Primary Savings Account and a published project "Neighborhood Solar" seeks $20,000.00
* **When** they back it with $100.00
* **Then** $100.00 debits savings (idempotency-keyed) into the project's escrow, funding progress updates in real time
* **And** the Backing appears in Member A's contribution history, and project-poster updates are pushed to them thereafter.

**Scenario 2 — Negative: insufficient available balance**
* **Given** Member B's savings balance is $250.00 with $200.00 locked as a guarantee pledge (available $50.00)
* **When** they attempt a $100.00 Backing
* **Then** the Backing is rejected with "amount exceeds available balance $50.00"
* **And** locked pledge funds and membership share equity are never usable for Backings.

**Scenario 3 — Edge: goal missed — all-or-nothing refund**
* **Given** the project's configurable all-or-nothing rule is on, the goal is $20,000.00, and only $18,000.00 is raised at deadline
* **When** the deadline job runs
* **Then** the project is marked unsuccessful and every Backing is refunded in full to each backer's Primary Savings Account, each refund linked to its original Backing
* **And** backers are notified; the escrow ledger drains to exactly $0.00.

**Scenario 4 — Edge: goal already reached / duplicate submission**
* **Given** the project reached 100% of its goal and is closed to new Backings
* **When** Member C attempts a further Backing, it is rejected with "this project is fully funded"
* **And** a network-retry duplicate of an earlier accepted Backing (same idempotency key) posts exactly once.

### US-9.3 — Surplus Matching Engine (L)

**Scenario 1 — Happy path: 1:1 match accrual with traceability**
* **Given** the Community Grant pool holds $150,000.00 (10% of surplus, KPI-4.2) and project "Neighborhood Solar" is match-eligible with a $5,000.00 project cap
* **When** Member A backs the project with $100.00
* **Then** a Surplus Match of $100.00 (1:1, ≤ cap) accrues against the pool for the project
* **And** every matched dollar is traceable: Backing ID → match entry → pool debit, and the project page shows member Backing and Surplus Match separately.

**Scenario 2 — Negative: release only via COMMUNITY_GRANT ballot**
* **Given** accrued matches for the project total $4,000.00
* **When** any operator attempts to disburse the match without a certified `COMMUNITY_GRANT` ballot authorizing the release
* **Then** the disbursement is rejected with `403 Forbidden` "release requires a certified COMMUNITY_GRANT ballot"
* **And when** the ballot passes and is certified (US-12.4)
* **Then** the release executes with the ballot reference stored on every disbursement entry.

**Scenario 3 — Edge: per-project cap reached — partial match**
* **Given** the project has $4,950.00 of its $5,000.00 cap matched
* **When** Member B backs it with $100.00
* **Then** only $50.00 of match accrues (cap boundary exact), the Backing itself is unaffected
* **And** the project page indicates matching is exhausted for this project.

**Scenario 4 — Edge: pool exhaustion halts matching globally**
* **Given** the Community Grant pool balance falls to $10.00
* **When** a member backs any eligible project with $100.00
* **Then** $10.00 accrues and the matching engine halts for all projects with a P-5 alert
* **And** subsequent Backings proceed unmatched with the UI stating matching is paused; the pool can never go negative.

**Scenario 5 — Negative: reconciliation invariant**
* **Given** any point in time
* **When** the pool reconciliation runs
* **Then** pool opening balance − Σ accrued/released matches = current pool balance to the minor unit; any mismatch freezes further accrual and alerts US-12.6/P-5.

### US-9.4 — Project Allocation & Impact Tracker (M)

**Scenario 1 — Happy path: allocation and outcomes per backed project**
* **Given** Member A backed "Neighborhood Solar", which raised $20,000.00 + $5,000.00 Surplus Match and has disbursed $18,000.00
* **When** Member A opens the project's tracker
* **Then** they see raised, matched, disbursed, and spent-by-category figures reconciling to the project ledger
* **And** owner-supplied outcome reports (e.g., "12 tonnes CO2 offset equivalent — estimated") with every modeled figure labeled "estimated" (DEC-15).

**Scenario 2 — Negative: unlabeled modeled figures blocked**
* **Given** a project owner submits an outcome report containing a modeled figure without the "estimated" designation
* **When** the report is processed for publication
* **Then** publication is blocked until the figure is labeled (or reclassified as a verified actual with evidence)
* **And** the rule is enforced at the content pipeline, not by editorial memory.

**Scenario 3 — Edge: missing conversion factors**
* **Given** a project has no impact-conversion factors supplied
* **When** the tracker renders
* **Then** it falls back to monetary figures only ("$100.00 contributed") with no fabricated physical metrics
* **And** aggregates still feed the Transparent Capital Ledger (US-13.4) and Impact Scorecard (US-13.5) correctly.

---

## EP-10 — Round-Up Savings (CAP-10)

### EP-10 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** "Round-Up" per DEC-12: each settled card transaction is rounded to the nearest dollar and the difference routed to the member's chosen destination — a Savings Goal or a published Community Project (the only two destinations). Whole-dollar transactions produce $0.00. Optional 1x/2x/3x multiplier and monthly cap. Changes take effect on the next card transaction. Insufficient funds are skipped gracefully. Impact figures labeled "estimated".
* **[CONFIRMED]** Locked guarantee pledges are excluded from Round-Up sweeps (US-6.4).
* **[PROPOSED]** Accumulated Round-Ups transfer in a batch when the pending balance reaches $5.00 (story gives $5.00 as an example only). (Sprint 2 draft value.)
* **[PROPOSED]** A skipped (insufficient-funds) batch is retried when the balance next allows, without overdrafting. (Sprint 2 draft.)
* **Superseded — do not implement:** rounding thresholds of $2.00/$5.00 (Sprint 1 draft — DEC-12 fixes nearest dollar; the multiplier is the only amplification); trigger on authorization (capture is on settlement per US-10.2).

### US-10.1 — Round-Up Enrollment & Destination Choice (S)

**Scenario 1 — Happy path: enroll with multiplier and cap**
* **Given** Member A has a virtual card (US-5.1) and a Savings Goal "New Laptop" (US-3.3)
* **When** they switch Round-Ups on, choose the "New Laptop" goal as destination, set multiplier 2x and a $50.00 monthly cap, and save
* **Then** the settings persist and take effect from the next settled card transaction
* **And** the destination picker offers only Savings Goals and published Community Projects (DEC-12).

**Scenario 2 — Negative: enable without a destination / invalid cap**
* **Given** Member A toggles Round-Ups on
* **When** they save with no destination selected, or a negative monthly cap
* **Then** the save is blocked with `422 Unprocessable Content` naming the field ("a destination is required" / "cap must be $0.00 or more")
* **And** Round-Ups remain off.

**Scenario 3 — Edge: destination becomes unavailable**
* **Given** Member A's destination Community Project closes (fully funded or ended)
* **When** the next Round-Up would route to it
* **Then** capture pauses for routing, Member A is notified to pick a new destination, and no funds are sent to a closed project
* **And** already-transferred amounts are unaffected.

### US-10.2 — Round-Up Capture & Routing Execution (M)

**Scenario 1 — Happy path: capture, accumulate, batch at threshold**
* **Given** Member A has Round-Ups at 1x with a pending accumulated balance of $4.60
* **When** a card transaction of $3.45 settles
* **Then** the capture engine computes $0.55, raising the pending balance to $5.15
* **And** the $5.00 batch threshold [PROPOSED] being reached, $5.15 transfers from the Transaction Account to the destination in one idempotency-keyed batch, the pending balance resets to $0.00
* **And** the ledger shows clearly labeled entries linking each purchase to its Round-Up and the batch.

**Scenario 2 — Edge: whole-dollar transaction**
* **Given** Round-Ups are active at 1x
* **When** a $15.00 transaction settles
* **Then** the computed Round-Up is $0.00, the pending balance is unchanged, and no transfer is initiated.

**Scenario 3 — Edge: multiplier arithmetic**
* **Given** Member A's multiplier is 2x
* **When** a $12.40 transaction settles
* **Then** the base Round-Up $0.60 is doubled to $1.20 and added to the pending balance
* **And** the running total display attributes $1.20 to that purchase.

**Scenario 4 — Negative: insufficient funds at batch time**
* **Given** the pending balance reaches $5.00 but the Transaction Account holds $3.00
* **When** the batch transfer attempts
* **Then** it is skipped gracefully — no overdraft, no card decline, the pending balance is retained
* **And** the batch retries when the balance next covers it [PROPOSED], with a silent backend log rather than an alarming member error.

**Scenario 5 — Edge: monthly cap reached**
* **Given** Member A's monthly cap is $50.00 and $49.40 has been captured this month
* **When** a transaction producing a $0.90 Round-Up settles
* **Then** only $0.60 is captured (cap boundary exact) and capture stops until the next calendar month
* **And** the settings screen shows "monthly cap reached"; the running savings/impact total (impact labeled "estimated") stays accurate.

---

## EP-11 — Notifications & Engagement (CAP-11)

### EP-11 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** Channels: push, email, SMS, and in-app inbox. Governed event catalog spanning payments, cards, Group Pots, governance, delegation, loans, guarantees, dividends, and projects; every event carries a deep link; new event types are catalog configuration, not code forks (US-11.1).
* **[CONFIRMED]** Per-category, per-channel preferences with timezone-aware quiet hours; regulatory/security notices are exempt from suppression and clearly marked (US-11.2).
* **[PROPOSED]** Failed push delivery falls back to the member's next enabled channel for that category after a short retry window. (Draft-implied; policy needs PO confirmation.)
* **[PROPOSED]** Quiet-hours-deferred notifications are delivered at the member's quiet-hours end, oldest first, collapsed into a digest when more than 5 accumulate. (No draft value; needs PO confirmation.)

### US-11.1 — Notification Delivery & Event Catalog (L)

**Scenario 1 — Happy path: payment event, multi-channel with deep link**
* **Given** Member B's preferences enable push and in-app inbox for payment events
* **When** Member A sends them $25.00 via US-4.1
* **Then** Member B receives a push notification and an inbox entry, each deep-linking to the transaction detail
* **And** Member A receives the sender-side confirmation event; both deliveries are recorded with status per channel.

**Scenario 2 — Happy path: catalog-driven event addition**
* **Given** a new event type "guarantee pledge released" is added to the event catalog by configuration
* **When** the next pro-rata release (US-6.4) occurs
* **Then** the notification dispatches using the configured template, category, and channels without any code deployment
* **And** the catalog entry records its category mapping for US-11.2 preferences.

**Scenario 3 — Negative: channel delivery failure**
* **Given** Member B's device push token is expired
* **When** a ballot-closing reminder dispatches
* **Then** the push fails, the failure is recorded, and delivery falls back per policy [PROPOSED] (e.g., email)
* **And** the in-app inbox entry exists regardless, so no event is silently lost.

**Scenario 4 — Edge: event ordering and deduplication**
* **Given** a Group Pot approval request (US-3.5) is approved and executed within seconds
* **When** "approval requested", "approved", and "executed" events dispatch
* **Then** each member receives them without duplicates (event IDs deduplicated at dispatch)
* **And** an event retried after a transient dispatcher failure does not produce a second push for the same event ID.

### US-11.2 — Notification Preferences & Quiet Hours (S)

**Scenario 1 — Happy path: per-category channel matrix honored**
* **Given** Member A sets governance events to email-only and payment events to push + inbox
* **When** a ballot opens and a P2P transfer arrives
* **Then** the ballot notice arrives by email only and the payment by push and inbox
* **And** preferences persist against the profile (US-1.5) and are evaluated by US-11.1 at dispatch time.

**Scenario 2 — Happy path: quiet hours defer non-urgent notices**
* **Given** Member A's quiet hours are 22:00–07:00 in their profile timezone
* **When** a dividend-estimator milestone event fires at 23:30
* **Then** push/SMS delivery is deferred until 07:00 [PROPOSED digest policy]; the in-app inbox entry is created immediately.

**Scenario 3 — Edge: regulatory/security notices are exempt**
* **Given** the same quiet hours
* **When** a suspected-fraud card decline or a mandated disclosure fires at 02:00
* **Then** it is delivered immediately on all enabled channels, visibly marked as a security/regulatory notice that cannot be suppressed
* **And** preference screens display these categories as non-suppressible rather than hiding them.

---

## EP-12 — Admin & Back-Office (CAP-12)

### EP-12 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** Every mutating action in this epic operates under four-eyes/maker-checker and is written to the immutable audit log (US-13.3). The maker and checker must be different operators; self-approval is impossible by construction.
* **[CONFIRMED]** Admin status transitions execute the DEC-4 machine via the US-2.2 domain rules; `DEFAULTED → WRITTEN_OFF` requires dual approval (US-12.3); certification computes `PASSED`/`REJECTED` with `QUORUM_NOT_MET` where applicable (US-12.4); configuration changes governed by `FINANCIAL_POLICY`/`GOVERNANCE_BYLAW` outcomes must link to the certified ballot (US-12.5).
* **[CONFIRMED]** Back-office access is role-based over a secure web console; P-5 logins require MFA (US-1.4) plus maker-checker on mutations.
* **[PROPOSED]** Queue SLA seed values: KYC `PENDING_REVIEW` cases resolved within 24 business hours; AML alerts triaged within 72 hours. (Seeds protect KPI-1.1/1.2.) [ADJUDICATED → see DEC-71 in 05_prd_and_roadmap.md: KYC ≤ 24 business hours confirmed; AML ≤ 72 h with HIGH-severity alerts triaged ≤ 24 h]
* **[PROPOSED]** Pending maker-checker approvals expire if unactioned after 7 days and must be re-initiated. (No draft value; needs PO confirmation.)

### US-12.1 — Member Management Console (360° View, Maker-Checker Status Changes) (L)

**Scenario 1 — Happy path: 360° view and unified timeline**
* **Given** Operator A has the member-services role
* **When** they search for Member A by Member ID and open the record
* **Then** they see profile, `MembershipStatus` and `KycStatus`, accounts, loans, guarantees, governance activity (participation facts only — never vote content), cases, and a unified timeline ordered by time
* **And** the console read access itself is audit-logged with operator identity and the record viewed.

**Scenario 2 — Happy path: suspension under maker-checker**
* **Given** Operator A initiates `ACTIVE → SUSPENDED` for Member A with a documented reason
* **When** Operator B reviews and approves
* **Then** the transition executes via US-2.2, Member A's vote/borrow/guarantee rights are revoked, and Member A is notified with the appeal route
* **And** the audit log records maker, checker, reason, and before/after status.

**Scenario 3 — Negative: self-approval blocked**
* **Given** Operator A initiated the suspension
* **When** Operator A attempts to approve their own initiation
* **Then** the approval is rejected with `403 Forbidden` "maker and checker must differ"
* **And** the transition remains pending for a different operator.

**Scenario 4 — Negative (security): role without permission**
* **Given** Operator C holds a read-only analyst role
* **When** they attempt to initiate any status transition or edit a case note
* **Then** the API responds `403 Forbidden`
* **And** an unauthenticated console request receives `401 Unauthorized` before any authorization evaluation.

**Scenario 5 — Edge: case notes are append-only**
* **Given** Operator A wrote a case note yesterday
* **When** any operator attempts to edit or delete it
* **Then** the note is immutable; corrections are new notes referencing the original
* **And** notes never store secret-ballot content or full card PANs (content validation rejects PAN-patterned strings).

### US-12.2 — KYC / AML Case Management Queues (M)

**Scenario 1 — Happy path: KYC escalation approved**
* **Given** Member A's onboarding case sits in the KYC queue with `KycStatus = PENDING_REVIEW` and the Persona evidence bundle attached
* **When** Operator A reviews the evidence and approves
* **Then** `KycStatus` transitions to `APPROVED`, the applicant advances to `PENDING_PAYMENT` and is notified to complete the share purchase
* **And** the case closes with decision, reviewer, and evidence references recorded; queue SLA timers (24 business hours [PROPOSED]) stop.

**Scenario 2 — Negative: rejection requires four-eyes and reason codes**
* **Given** Operator A recommends rejection of Member B's case
* **When** Operator A submits the rejection alone
* **Then** it remains pending until Operator B concurs (four-eyes on rejections)
* **And** the final rejection requires selected reason codes, sets `KycStatus = REJECTED`, ends the application per DEC-4, and stores the full decision audit trail.

**Scenario 3 — Happy path: AML alert triage against the 360°**
* **Given** US-13.1 raises an alert on Member C's transfer pattern
* **When** Operator A triages it using the member 360° view and escalates to the SAR workflow
* **Then** the alert links into a SAR case (US-13.1) with the evidence carried over
* **And** no member-visible trace of the investigation exists (tipping-off safeguard).

**Scenario 4 — Edge: SLA breach escalation**
* **Given** a KYC case ages past the 24-business-hour SLA [PROPOSED]
* **When** the SLA timer fires
* **Then** the case is flagged, escalated to the queue supervisor, and counted in the KPI-1.1/1.2 protection dashboard
* **And** assignment history shows every operator who held the case.

### US-12.3 — Loan Operations Console (L)

**Scenario 1 — Happy path: referral approved under maker-checker**
* **Given** Member A's application sits in the referral queue with full inputs and the engine's recommendation
* **When** Operator A approves and Operator B confirms
* **Then** `LoanStatus` transitions `UNDER_REVIEW → APPROVED` and the borrower is notified with the offer
* **And** the human decision, rationale, and both operators are logged for fair-lending review (US-13.3).

**Scenario 2 — Happy path: counter-offer**
* **Given** the same referral
* **When** Operators A and B approve a counter-offer of $400.00 instead of the requested $500.00
* **Then** the borrower receives the revised conditional offer with the changed terms highlighted, free to accept or decline
* **And** the original request and counter-offer are both retained.

**Scenario 3 — Happy path: hardship restructuring executed**
* **Given** Member B's hardship request (US-6.8) proposes reduced installments for two months
* **When** Operator A prepares the reschedule and Operator B approves
* **Then** the new schedule takes effect in servicing (US-6.7), borrower and guarantors are notified, and the collections case updates
* **And** the loan's full schedule history is preserved.

**Scenario 4 — Negative: single-operator write-off blocked**
* **Given** Member C's loan is `DEFAULTED`
* **When** Operator A attempts `DEFAULTED → WRITTEN_OFF` without a second approver
* **Then** the transition is rejected — dual approval is mandatory
* **And when** Operator B approves, the write-off executes, feeds portfolio-quality reporting (US-13.2, KPI-2.5), and the guarantee-pledge disposition per US-6.4 rules is recorded.

**Scenario 5 — Edge: guarantee-pledge administration**
* **Given** Member D's pledge backs a restructured loan
* **When** Operators A and B approve a partial pledge release of $50.00 consistent with US-6.4 rules
* **Then** the lock reduces by exactly $50.00, the guarantor is notified
* **And** a release attempt exceeding the rules-derived releasable amount is rejected with the computed maximum shown.

### US-12.4 — Governance Administration (Scheduling, Quorum, Certification) (M)

**Scenario 1 — Happy path: schedule a ballot**
* **Given** a proposal is `SUBMITTED` with its co-signature threshold verified
* **When** Operator A schedules a `PROPOSAL` ballot (window, quorum, result-visibility rules) and Operator B approves
* **Then** at window open the proposal transitions `SUBMITTED → OPEN_FOR_VOTING`, the US-2.3 snapshot is taken, and the discussion thread locks (US-8.6)
* **And** members are notified of the ballot opening (US-11.1).

**Scenario 2 — Happy path: certification with quorum met**
* **Given** the ballot closed with participation above quorum and FOR outnumbering AGAINST per the configured rule
* **When** Operator A computes certification and Operator B approves
* **Then** the outcome `PASSED` publishes to the archive (US-8.7) with tallies and the Governance Participation Rate recorded per DEC-16
* **And** the certified record is immutable thereafter.

**Scenario 3 — Happy path: quorum not met**
* **Given** a closed ballot with 18% participation against a 25% quorum
* **When** certification runs under maker-checker
* **Then** the outcome is `REJECTED` with reason `QUORUM_NOT_MET`, published with the participation figure and the quorum in force.

**Scenario 4 — Negative: certify before close / tamper with a scheduled window**
* **Given** a ballot still open
* **When** any operator attempts certification, it is rejected with `409 Conflict` "ballot not closed"
* **And when** an operator attempts to shorten the voting window after votes have been cast
* **Then** the change is rejected; window changes after open require a documented, dual-approved exceptional procedure and are prominently recorded.

### US-12.5 — Product & Fee Configuration (M)

**Scenario 1 — Happy path: effective-dated rate change with dual approval**
* **Given** Operator A drafts a savings-rate change from 2.00% to 2.50% effective the 1st of next month
* **When** Operator B approves before the effective date
* **Then** the registry stores a new version with effective-dating; consumers (US-3.1) switch automatically at the effective moment
* **And** the version history shows who changed what, when, and why.

**Scenario 2 — Negative: governed parameter without ballot linkage**
* **Given** the patronage factor weights are governed by `FINANCIAL_POLICY`
* **When** Operator A submits a weight change with no certified-ballot reference
* **Then** the change is rejected with "certified ballot linkage is mandatory for governed parameters"
* **And** a linkage to a ballot that is not `PASSED`/certified is equally rejected.

**Scenario 3 — Negative (security): unauthorized configuration access**
* **Given** Operator C lacks the product-configuration role
* **When** they attempt any parameter change
* **Then** the API responds `403 Forbidden` and the attempt is audit-logged.

**Scenario 4 — Edge: pending future version superseded**
* **Given** an approved change is pending its effective date
* **When** a newer dual-approved version with an earlier effective date is created
* **Then** the registry resolves precedence deterministically by effective date then approval time, and both versions remain in history
* **And** consumers never read a mixture of two versions within a single calculation.

### US-12.6 — Dividend Run Administration (M)

**Scenario 1 — Happy path: end-to-end run inside 5 business days**
* **Given** the AGM ratified the annual accounts, and Operator A inputs the ratified surplus with linkage to the AGM record, including the 10% Community Grant pool split (KPI-4.2)
* **When** the dry run completes with sample-level review and no blocking exceptions, Operators A and B dual-approve, and the payout executes (US-7.2)
* **Then** live monitoring shows postings progressing, and the reconciliation report proves entitlements = postings + documented exceptions, with the pool split accounted
* **And** the entire run (inputs, approvals, execution, reconciliation) is one immutable record; completion falls within 5 business days of ratification (KPI-4.3).

**Scenario 2 — Negative: execution without dual approval**
* **Given** a dry run is complete
* **When** Operator A alone attempts to execute the payout
* **Then** execution is rejected — dual approval is mandatory
* **And** the attempt is audit-logged.

**Scenario 3 — Negative: reconciliation mismatch halts the run**
* **Given** the live run's postings drift from entitlements by $12.40 beyond documented exceptions
* **When** the reconciliation check detects the variance
* **Then** the run halts for investigation, no further postings execute, and P-5 is alerted with the affected member list
* **And** resumption requires a fresh dual approval referencing the investigation outcome.

**Scenario 4 — Edge: dry-run exception surfacing**
* **Given** the dry run detects 3 members with `CLOSED` status since the factor snapshot and 1 member with a negative computed entitlement (defect)
* **When** the dry-run report renders
* **Then** each exception is itemized with member reference and reason; the negative entitlement is a blocking exception that prevents approval until resolved
* **And** the `CLOSED`-member items carry the configured disposition path (per US-7.2 Scenario 3).

---

## EP-13 — Compliance, Risk & Transparency (CAP-13)

### EP-13 Business Rules

> **Note:** Adjudications for all [PROPOSED] rules: see §Business Rule Adjudication in `05_prd_and_roadmap.md`.

* **[CONFIRMED]** AML monitoring covers all money movement (P2P, external, cards, Group Pots, Loan Circles, Backings) in real time and batch; alerts route to US-12.2; SAR assembly under dual review with tipping-off safeguards (US-13.1). Report definitions are configuration-driven (US-13.2; Open Item 3).
* **[CONFIRMED]** Audit log is append-only with cryptographic tamper evidence (hash chaining per the story's cited example) and a standardized envelope: actor, action, subject, before/after, timestamp (US-13.3).
* **[CONFIRMED]** Transparent Capital Ledger reconciles to 100% of managed funds, refreshed daily or better; DEC-15 naming and "estimated" labeling apply to it and to the Impact Scorecard (US-13.4/US-13.5).
* **[CONFIRMED]** Consent records enforced across processing; retention/erasure by record class; financial-records retention obligations override deletion; SAR/DSAR fulfilment within statutory deadlines (US-13.6).
* **[PROPOSED]** Seed monitoring scenario: aggregate outbound transfers ≥ $10,000.00 within 24 hours, or patterns of sub-threshold amounts consistent with structuring, raise an alert. (Illustrative seed — compliance officer must define the production rule set.)
* **[PROPOSED]** DSAR fulfilment deadline seed: 30 calendar days (statutory deadline depends on jurisdiction/charter; configuration, not code).
* **[PROPOSED]** Audit-log retention: 7 years minimum for financial and governance events. (No draft value; statutory confirmation required.)

### US-13.1 — Ongoing AML Transaction Monitoring & SAR Workflow (L)

**Scenario 1 — Happy path: pattern alert raised and routed**
* **Given** the tuned rule set includes the structuring scenario [PROPOSED seed]
* **When** Member A receives nine P2P credits of $980.00 from distinct senders within 24 hours
* **Then** an alert is created with the triggering scenario, scored, and routed to the US-12.2 AML queue with the linked transactions attached
* **And** none of the transfers is blocked or annotated in any member-visible way (tipping-off safeguard).

**Scenario 2 — Happy path: SAR assembly under dual review**
* **Given** an escalated alert on Member A
* **When** Operator A assembles the SAR case — narrative, evidence bundle, filing-ready output — and Operator B reviews and approves
* **Then** the filing-ready artifact is produced and the case records both reviewers and every evidence item
* **And** case access is restricted to compliance roles; even the US-12.1 member timeline shows no SAR trace.

**Scenario 3 — Negative: alert dismissal requires a reason**
* **Given** a triaged alert judged a false positive
* **When** Operator A dismisses it without a disposition reason
* **Then** the dismissal is rejected; with a reason it closes and feeds rule-tuning statistics
* **And** dismissed alerts remain queryable for look-back investigations.

**Scenario 4 — Edge: coverage across constructs**
* **Given** monitoring spans Group Pots, Pooled Loan Circles, and project Backings
* **When** a Group Pot receives rapid contributions from 15 members followed by an immediate maximal outbound request
* **Then** the batch scenario evaluates pot-level flows and raises an alert referencing the pot and its members
* **And** rule-set changes (P-5 configuration) are versioned, and each alert records the rule version that fired.

### US-13.2 — Regulatory & Prudential Reporting Suite (M)

**Scenario 1 — Happy path: scheduled report from a point-in-time snapshot**
* **Given** the monthly deposit-to-loan report is scheduled for the 1st at 06:00 over the month-end snapshot
* **When** the schedule fires
* **Then** the report generates from the immutable snapshot (later corrections do not silently alter it), exports in the required format, and the submission log records generation and delivery
* **And** re-running the report over the same snapshot is byte-identical.

**Scenario 2 — Happy path: KPI threshold breach alert**
* **Given** thresholds monitor KPI-2.3 (deposit-to-loan 75–85%), KPI-2.4 (capital adequacy > 10%), KPI-2.5 (NPL)
* **When** the computed NPL rate reaches 1.9% against the ≤ 1.8% Year-1 target
* **Then** a breach alert is raised to P-5 naming the metric, value, threshold, and trend
* **And** the breach and its acknowledgment are logged.

**Scenario 3 — Negative (security): unauthorized report access**
* **Given** an operator without the reporting role
* **When** they request a prudential report or its export
* **Then** the API responds `403 Forbidden`
* **And** report definitions are configuration-driven, so a charter-dependent new report (Open Item 3) is added without code change — with the definition change itself dual-approved and logged.

### US-13.3 — Immutable Audit Log (M)

**Scenario 1 — Happy path: standardized envelope appended**
* **Given** Operator B approves Member A's suspension (US-12.1)
* **When** the action commits
* **Then** an audit event appends with actor, action, subject, before/after state (`ACTIVE` → `SUSPENDED`), and timestamp, chained to the previous event's hash
* **And** the write is part of the action's transaction — the action cannot succeed without its audit event.

**Scenario 2 — Happy path: tamper evidence verifies**
* **Given** a stored chain of audit events
* **When** the integrity verifier recomputes the hash chain
* **Then** an unmodified chain verifies end to end; altering any single historical event breaks verification from that point forward and raises an operational alarm.

**Scenario 3 — Negative: mutation attempts rejected**
* **Given** any client, including privileged P-5 and DBA-level service roles exposed through the application layer
* **When** an update or delete is attempted against an audit event
* **Then** the service rejects it (`403 Forbidden`) — the store is append-only by interface and by storage policy
* **And** the rejected attempt is itself appended as an audit event.

**Scenario 4 — Edge: scoped query and export for audits**
* **Given** an external auditor engagement scoped to EP-8 governance events for Q1
* **When** an authorized operator runs the scoped export
* **Then** only events matching the scope are returned, with the export itself logged (who exported what scope, when)
* **And** secret-ballot protection holds: no audit event ever contains a member-identifiable `VoteChoice`.

### US-13.4 — Transparent Capital Ledger (M)

**Scenario 1 — Happy path: allocation view reconciles to 100%**
* **Given** the cooperative manages $25,000,000.00 across local loans, green lending, Community Grants, and liquidity reserves
* **When** Member A opens the Transparent Capital Ledger
* **Then** the allocation chart's categories sum to exactly 100% of managed funds, reconciling to the ledger, with the refresh timestamp shown (daily or better)
* **And** any modeled figure is labeled "estimated" (DEC-15).

**Scenario 2 — Happy path: drill-down with consented spotlights**
* **Given** the member taps the local-loans category
* **When** the drill-down loads
* **Then** category detail appears with funded-project spotlights shown only where anonymized or explicitly consented
* **And** no borrower-identifiable data is derivable from the drill-down (small-cell suppression applies).

**Scenario 3 — Negative/edge: refresh failure shows staleness, never invention**
* **Given** the daily refresh job fails
* **When** members view the ledger
* **Then** the last successful data renders with a clear as-of timestamp and staleness notice
* **And** the view never displays interpolated or fabricated allocations; a refresh older than the daily commitment raises an internal alert.

### US-13.5 — Personal Impact Scorecard (M)

**Scenario 1 — Happy path: attributed impact with methodology**
* **Given** Member A's deposits and Round-Ups participate in the pool behind the Transparent Capital Ledger and project outcomes (US-9.4)
* **When** they open their Impact Scorecard
* **Then** proportionally attributed figures display (e.g., "~0.4 tonnes CO2 offset — estimated"), every figure labeled "estimated" with methodology notes one tap away (DEC-15).

**Scenario 2 — Happy path (security): sharing without PII**
* **Given** Member A taps the optional share action
* **When** the share card generates
* **Then** it contains only the estimated impact statements — no balances, transaction history, Member ID, or account details
* **And** sharing is off by default and per-instance.

**Scenario 3 — Edge: insufficient underlying data**
* **Given** Member B activated this week, or an impact category lacks trustworthy US-13.4/US-9.4 data
* **When** the scorecard renders
* **Then** categories without sound data show an explanatory empty state rather than $0.00-derived or fabricated figures
* **And** monetary contribution totals may still display as facts (they are ledger facts, not models).

### US-13.6 — Data Privacy, Consent Enforcement & Subject-Access Requests (M)

**Scenario 1 — Happy path: DSAR fulfilled within deadline**
* **Given** Member A submits a subject-access request
* **When** the workflow compiles their data across systems, applies redaction (e.g., other members' PII in shared Group Pot records, any SAR-related material excluded per tipping-off rules)
* **Then** the package is delivered securely within the statutory deadline (seed 30 days [PROPOSED]) with deadline tracking visible to P-5 throughout
* **And** the fulfilment is audit-logged.

**Scenario 2 — Happy path: consent withdrawal enforced in processing**
* **Given** Member A withdraws marketing-analytics consent via US-1.5
* **When** the next processing run executes
* **Then** Member A's data is excluded from consent-gated processing from the withdrawal timestamp
* **And** processing required by law or contract (AML monitoring, loan servicing) continues and is documented as such.

**Scenario 3 — Negative: deletion request versus retention obligations**
* **Given** Member B (now `CLOSED`) requests erasure
* **When** the workflow evaluates record classes
* **Then** classes under financial-records retention (transactions, KYC evidence, audit events) are retained for their statutory periods with the legal basis recorded in the response to the member
* **And** classes with no retention obligation are erased or anonymized, and the differentiated outcome is reported to the requester.

**Scenario 4 — Edge: retention schedule executes post-closure**
* **Given** Member C closed their membership 7 years ago and the configured retention period for their remaining record classes has elapsed
* **When** the scheduled retention job runs
* **Then** those records are erased or irreversibly anonymized per class rules, with a class-level (not content-level) log of the disposal
* **And** the immutable audit log retains its own events per its retention policy [PROPOSED: 7 years minimum], with personal identifiers pseudonymized where the law requires.

---

## Story Coverage Checklist

Every story in `02_user_stories.md` is covered. Counts include all scenario types (happy, negative, edge, security).

| Story | Size | Scenarios | | Story | Size | Scenarios |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| US-1.1 | M | 4 | | US-7.1 | L | 5 |
| US-1.2 | L | 5 | | US-7.2 | M | 4 |
| US-1.3 | S | 3 | | US-7.3 | M | 4 |
| US-1.4 | M | 4 | | US-7.4 | M | 4 |
| US-1.5 | S | 3 | | US-8.1 | L | 6 |
| US-2.1 | M | 4 | | US-8.2 | L | 5 |
| US-2.2 | M | 4 | | US-8.3 | L | 5 |
| US-2.3 | M | 4 | | US-8.4 | M | 4 |
| US-2.4 | M | 4 | | US-8.5 | M | 4 |
| US-3.1 | M | 4 | | US-8.6 | M | 4 |
| US-3.2 | M | 4 | | US-8.7 | M | 3 |
| US-3.3 | M | 4 | | US-9.1 | M | 4 |
| US-3.4 | L | 5 | | US-9.2 | M | 4 |
| US-3.5 | M | 4 | | US-9.3 | L | 5 |
| US-4.1 | M | 5 | | US-9.4 | M | 3 |
| US-4.2 | L | 5 | | US-10.1 | S | 3 |
| US-4.3 | M | 4 | | US-10.2 | M | 5 |
| US-4.4 | M | 4 | | US-11.1 | L | 4 |
| US-5.1 | M | 4 | | US-11.2 | S | 3 |
| US-5.2 | M | 4 | | US-12.1 | L | 5 |
| US-5.3 | S | 3 | | US-12.2 | M | 4 |
| US-6.1 | M | 4 | | US-12.3 | L | 5 |
| US-6.2 | L | 5 | | US-12.4 | M | 4 |
| US-6.3 | M | 4 | | US-12.5 | M | 4 |
| US-6.4 | L | 5 | | US-12.6 | M | 4 |
| US-6.5 | XL | 5 | | US-13.1 | L | 4 |
| US-6.6 | M | 4 | | US-13.2 | M | 3 |
| US-6.7 | L | 5 | | US-13.3 | M | 4 |
| US-6.8 | M | 4 | | US-13.4 | M | 3 |
| | | | | US-13.5 | M | 3 |
| | | | | US-13.6 | M | 4 |

**Totals: 60 / 60 stories covered; 247 scenarios.** Every story has ≥ 1 happy path and ≥ 1 negative/error scenario; every M/L/XL story has ≥ 1 edge case; every S story also carries a third scenario for uniform depth.

**Open confirmations for the PO:** all rules tagged **[PROPOSED]** in the per-epic Business Rules blocks (including the two explicitly conflicting draft pairs — the lending base rate 8.00% vs 12.00% APR, and the Community Project campaign duration 30–365 vs 1–90 days) plus the inline-flagged decisions: whether a Group Pot outbound initiator counts toward the m-of-n threshold (US-3.5), payment-request reminder cadence (US-4.4), the PIN denylist (US-5.2), the fate of delegate-cast votes on open ballots when the delegate is suspended (US-8.5), and the terminal status of an expired co-signature draft (EP-8 note). No scenario may be automated against a [PROPOSED] value until it is confirmed or replaced via US-12.5 configuration. **[ADJUDICATED — all items above have been resolved as DEC-21…DEC-75; see §Business Rule Adjudication in 05_prd_and_roadmap.md. The two conflict pairs resolve to a 12.00% APR unsecured base rate with Loan Circle discounts to 6.00% (DEC-48/DEC-49) and a 14–120 day campaign duration (DEC-64).]**

*End of document.*
