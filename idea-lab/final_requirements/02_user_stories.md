# User Story Backlog — Digital Coop Bank

**Document ID:** 02_user_stories
**Status:** Final (single authoritative backlog; supersedes the sprint_1–sprint_3 user story documents)
**Upstream source of truth:** `01_business_analysis.md` — personas P-1…P-5, capabilities CAP-1…CAP-13, features F-101…F-152, and the Canonical Glossary & Decision Log (DEC-1…DEC-20), all used verbatim here.

## Conventions

* **Story IDs:** `US-<epic>.<n>`, freshly numbered. IDs from the sprint drafts (US-1.1a, MIM-1, DGV-3, CAT-1, …) are retired and must not be referenced.
* **Personas:** referenced only by canonical ID (P-1 Values-Driven Saver, P-2 Digital-Native Member, P-3 Flexible Earner, P-4 Community Organizer, P-5 Cooperative Operations Administrator). Where a story serves several personas, the primary persona voices the story and others are noted in the description.
* **Enums and terms** are used verbatim per the glossary: `MembershipStatus = PENDING_KYC | PENDING_PAYMENT | ACTIVE | SUSPENDED | CLOSED`; `KycStatus = NOT_STARTED | IN_PROGRESS | PENDING_REVIEW | APPROVED | REJECTED`; `VoteChoice = FOR | AGAINST | ABSTAIN`; `ProposalCategory = COMMUNITY_GRANT | FINANCIAL_POLICY | GOVERNANCE_BYLAW`; `ProposalStatus = DRAFT | SUBMITTED | OPEN_FOR_VOTING | PASSED | REJECTED | WITHDRAWN`; `BallotType = PROPOSAL | BOARD_ELECTION`; `RecipientIdentifierType = PHONE | EMAIL | MEMBER_ID`; `LoanStatus = DRAFT | SUBMITTED | UNDER_REVIEW | APPROVED | ACTIVE | DELINQUENT | PAID_OFF | DEFAULTED | WRITTEN_OFF`. All amounts MNT (₮, integer minor units, ISO 4217 numeric 496), displayed whole tögrög (DEC-18). A bounded set of values remains in USD pending downstream decisions, each explicitly marked.
* **T-shirt sizes:** S / M / L / XL relative implementation complexity. INVEST notes appear only where a story is at risk (typically L/XL) and give split hints.
* **Dependencies** list other US IDs that must be substantially complete first (build-order, not runtime coupling).

## Epic Index

| Epic | Name | Capabilities | Stories |
| :--- | :--- | :--- | :--- |
| EP-1 | Identity, Onboarding & KYC | CAP-1 | US-1.1 – US-1.5 |
| EP-2 | Membership Shares & Equity | CAP-2 | US-2.1 – US-2.4 |
| EP-3 | Savings & Deposit Accounts | CAP-3 | US-3.1 – US-3.5 |
| EP-4 | Payments & Transfers | CAP-4 | US-4.1 – US-4.4 |
| EP-5 | Card Management | CAP-5 | US-5.1 – US-5.3 |
| EP-6 | Lending & Loan Circles | CAP-6 | US-6.1 – US-6.8 |
| EP-7 | Dividends & Surplus Distribution | CAP-7 | US-7.1 – US-7.4 |
| EP-8 | Democratic Governance & Voting | CAP-8 | US-8.1 – US-8.7 |
| EP-9 | Community Funding Hub | CAP-9 | US-9.1 – US-9.4 |
| EP-10 | Round-Up Savings | CAP-10 | US-10.1 – US-10.2 |
| EP-11 | Notifications & Engagement | CAP-11 | US-11.1 – US-11.2 |
| EP-12 | Admin & Back-Office | CAP-12 | US-12.1 – US-12.6 |
| EP-13 | Compliance, Risk & Transparency | CAP-13 | US-13.1 – US-13.6 |

**Total: 60 stories.**

---

## EP-1 — Identity, Onboarding & KYC (CAP-1)

Everything from first app screen to a KYC-approved applicant, plus authentication and profile management. Onboarding time is measured per DEC-17 (first app-flow screen → `MembershipStatus = ACTIVE`); the epic-level budget is median ≤ 8 min, p90 ≤ 10 min (KPI-1.1). Share purchase and activation itself lives in EP-2.

### US-1.1 — Start, Save and Resume the Digital Onboarding Journey

* **As a** P-2 (Digital-Native Member), **I want to** begin membership application on my phone, see my progress, and resume exactly where I left off if I am interrupted, **so that** I can become a member without branch visits, paper, or restarting the flow.
* **Description:** Covers the application shell: step sequence (personal details per DEC-6 structured name/address model, eligibility, KYC, share purchase), progress indicator, and server-side save/resume keyed to the applicant's verified contact channel. `KycStatus` starts at `NOT_STARTED` and moves to `IN_PROGRESS` when document capture begins. Out of scope: the verification itself (US-1.2), eligibility rules (US-1.3), and payment (US-2.1). Instrumentation must emit the timestamps needed to measure KPI-1.1/1.2.
* **Maps to:** F-101; CAP-1.1
* **Size:** M
* **Dependencies:** none (backlog root)

### US-1.2 — eKYC Verification via Persona (Document, Biometric, Screening)

* **As a** P-2 (Digital-Native Member), **I want to** photograph my government ID and pass a live selfie check in-app, **so that** my identity is verified in minutes with no manual document handling.
* **Description:** Integration with the Persona verification service (DEC-5) for document capture with OCR extraction into the DEC-6 name/address fields, biometric selfie match with liveness detection, and automated sanctions/PEP watchlist screening. Clear pass → `KycStatus = APPROVED`; ambiguous results → `PENDING_REVIEW` and routing to the CAP-12.2 queue (US-12.2); hard fail → `REJECTED`, which ends the application (per DEC-4, no member record reaches a "rejected" membership status). Retry guidance (blur, glare, lighting) is in scope; manual review tooling is not (US-12.2).
* **Maps to:** F-101; CAP-1.2, CAP-1.3
* **Size:** L
* **Dependencies:** US-1.1
* **INVEST note:** At risk on Independent/Small — vendor-integration story. If it exceeds a sprint, split by verification stage: (a) document OCR, (b) selfie/liveness match, (c) watchlist screening + `KycStatus` state handling. Merged from three near-identical draft stories (Sprint 1 US-1.1a/US-1.1b, Sprint 2 Story 1.1, Sprint 3 MIM-1).

### US-1.3 — Membership Eligibility & Common-Bond Validation

* **As a** P-2 (Digital-Native Member), **I want to** confirm during sign-up that I meet the cooperative's membership eligibility criteria, **so that** I don't invest time (or the 10,000₮ share payment (provisional, pending DEC-11 / legal)) in an application that cannot be approved.
* **Description:** Automated common-bond and eligibility check executed within onboarding, before the share-purchase step, with a clear explanation and remediation path when criteria are not met. Eligibility rules are data-driven so the cooperative can amend them via GOVERNANCE_BYLAW decisions without code change. Also serves P-1, P-3, P-4. Rule administration UI is out of scope (configuration via US-12.5 seeds).
* **Maps to:** F-102; CAP-1.4
* **Size:** S
* **Dependencies:** US-1.1

### US-1.4 — Multi-Factor Authentication, Biometrics & Device Binding

* **As a** P-2 (Digital-Native Member), **I want to** sign in with device biometrics and be challenged with step-up authentication only for sensitive actions, **so that** my account stays secure without constant friction.
* **Description:** MFA enrollment during onboarding, device binding, session management, and a step-up policy applied to sensitive actions (external payments above limits, card credential reveal, vote submission, Proxy Delegation changes, guarantee pledges). Serves all personas including P-5 back-office logins (which additionally require maker-checker, handled in EP-12). Fraud/risk scoring of logins is out of scope for this story.
* **Maps to:** F-104; CAP-1.5
* **Size:** M
* **Dependencies:** US-1.1

### US-1.5 — Member Profile, Consents & Communication Preferences

* **As a** P-1 (Values-Driven Saver), **I want to** view and maintain my profile — structured name and address, contact details, consents, and communication preferences — and see my `MembershipStatus`, Member ID, and join date, **so that** I control my data and always know my standing in the cooperative.
* **Description:** Read/write profile screens using the DEC-6 model (`ner`, `etsgiin_ner`, optional `ovog`, structured postal address); `mrz_name_latin` and `registration_number` are read-only, KYC-sourced, and never member-editable; the derived `legal_name` (composition of `ovog` `etsgiin_ner` `ner`) is display-only and never independently editable. Changes to KYC-relevant attributes (name, address, phone, email) trigger re-verification or admin review as required. Consent capture/withdrawal is recorded for CAP-13.5 processing (US-13.6). Notification channel preferences live in US-11.2.
* **Maps to:** F-105; CAP-1.6
* **Size:** S
* **Dependencies:** US-1.2

---

## EP-2 — Membership Shares & Equity (CAP-2)

The equity backbone: the mandatory 10,000₮ membership share (DEC-11), the DEC-4 membership status machine, the share registry, and voting-eligibility determination.

### US-2.1 — Initial Membership Share Purchase & Member Activation

* **As a** P-2 (Digital-Native Member), **I want to** buy my one mandatory membership share (10,000₮ par value) inside the onboarding flow by card or bank transfer, **so that** my membership activates immediately and my voting rights switch on.
* **Description:** On `KycStatus = APPROVED` the applicant transitions to `MembershipStatus = PENDING_PAYMENT` and is presented the share purchase (card, bank transfer, and wallet-funded card payments). On settlement, funds post to the Membership Share Account as non-withdrawable equity, the member transitions `PENDING_PAYMENT → ACTIVE`, receives their Member ID and a digital confirmation (share record, bylaws copy), and voting/borrowing/guaranteeing rights activate. Merges Sprint 1 US-2.1b, Sprint 2 Stories 1.2/1.3, Sprint 3 MIM-2; the Sprint 2 "membership token" concept is retired per DEC-4 — activation is simply the `PENDING_PAYMENT → ACTIVE` transition. Additional/voluntary share purchases are out of scope for launch.
* **Maps to:** F-103; CAP-2.1, CAP-2.2
* **Size:** M
* **Dependencies:** US-1.2, US-1.3

### US-2.2 — Membership Lifecycle Enforcement (Status Machine)

* **As a** P-5 (Cooperative Operations Administrator), **I want** the platform to enforce the canonical membership status machine — `PENDING_KYC → PENDING_PAYMENT → ACTIVE`, `ACTIVE ↔ SUSPENDED`, `ACTIVE/SUSPENDED → CLOSED` — with admin-controlled transitions under maker-checker, **so that** member rights (vote, borrow, guarantee) are granted and revoked correctly and auditably.
* **Description:** Server-side enforcement that only ACTIVE members may vote, borrow, or guarantee; SUSPENDED blocks those rights while preserving the record and is appealable; illegal transitions are rejected everywhere. Members see their current status and its practical meaning in-app (via US-1.5). The admin UI executing suspend/close actions is US-12.1; this story delivers the domain rules, events, and APIs it calls.
* **Maps to:** F-106; CAP-2.3
* **Size:** M
* **Dependencies:** US-2.1

### US-2.3 — Share Registry & Voting-Eligibility Snapshots

* **As a** P-5 (Cooperative Operations Administrator), **I want** an authoritative registry of shares held per member that produces a point-in-time eligibility snapshot when each ballot opens, **so that** one-member-one-vote is provably enforced and results are defensible to auditors and regulators.
* **Description:** The registry records share issuance and redemption with full history, reconciles to the equity ledger, and exposes a snapshot API that captures the set of ACTIVE members at ballot open (consumed by US-8.1/US-8.3 and by US-12.4 for certification). Eligibility is binary — holding the one mandatory share while ACTIVE confers exactly one vote regardless of any future additional holdings. Registry queries are also surfaced to P-4 for group-governance transparency.
* **Maps to:** F-107; CAP-2.4
* **Size:** M
* **Dependencies:** US-2.1

### US-2.4 — Voluntary Membership Closure & Share Redemption

* **As a** P-1 (Values-Driven Saver), **I want to** close my membership from the app and have my membership share redeemed at par, **so that** I can exit the cooperative cleanly without paperwork.
* **Description:** Guided closure flow: preconditions checked (no `ACTIVE`/`DELINQUENT` loans, no locked guarantee pledges, Group Pot memberships resolved, balances swept to an external account), then transition to `MembershipStatus = CLOSED` and redemption of the share at 10,000₮ par subject to bylaws (DEC-11; redemption terms flagged as Open Item 1 in the business analysis — implement behind a configurable rule). Involuntary closure (expulsion) is executed by P-5 through US-12.1 using the same domain machinery. Data retention post-closure follows US-13.6.
* **Maps to:** F-106; CAP-2.2, CAP-2.3
* **Size:** M
* **Dependencies:** US-2.2, US-4.2

---

## EP-3 — Savings & Deposit Accounts (CAP-3)

The four deposit constructs per DEC-13: Primary Savings Account, Transaction Account, Savings Goal (personal), Group Pot (shared, m-of-n).

### US-3.1 — Primary Savings Account with Interest Accrual & Posting

* **As a** P-1 (Values-Driven Saver), **I want** an interest-bearing Primary Savings Account opened automatically the moment my membership becomes ACTIVE, with daily interest accrual and monthly posting, **so that** my money starts working for the cooperative and for me immediately.
* **Description:** Automatic account opening at activation; balance and accrued-interest visibility; deposit/withdrawal via internal transfers and external rails (EP-4); interest engine with daily accrual, monthly posting, and rate parameters administered via US-12.5. A member-facing yield history view (earned to date, last posting) is in scope, absorbing Sprint 1 US-6.3a. Statements are standard account artifacts here; dividend/tax statements are separate (US-7.4).
* **Maps to:** F-108; CAP-3.1, CAP-3.5
* **Size:** M
* **Dependencies:** US-2.1

### US-3.2 — Transaction (Checking) Account with Categorized History

* **As a** P-2 (Digital-Native Member), **I want** a day-to-day Transaction Account that backs my cards and payments and shows a clean, categorized, searchable transaction history, **so that** I can run my daily finances entirely from the app.
* **Description:** Account opening (at activation or on demand), real-time balance, automatic transaction categorization, search/filter, and per-transaction detail with a shareable confirmation receipt (absorbing Sprint 1 US-3.1b). This account is the funding source for cards (EP-5), P2P (US-4.1), and Round-Ups (EP-10). Budgeting analytics beyond categorization are out of scope.
* **Maps to:** F-109; CAP-3.2
* **Size:** M
* **Dependencies:** US-2.1

### US-3.3 — Savings Goals (Personal Pots)

* **As a** P-2 (Digital-Native Member), **I want to** create named Savings Goals with target amounts and dates, progress visuals, and automated recurring transfers, **so that** saving for specific things feels motivating and automatic.
* **Description:** CRUD for personal sub-account pots under the Primary Savings Account; per-goal target, image/emoji, progress bar, and scheduled auto-transfers from the Transaction Account; withdraw-from-goal with a gentle confirmation. Savings Goals are also valid Round-Up destinations (US-10.1). Group (multi-member) money is explicitly out of scope — that is the Group Pot (US-3.4, DEC-13).
* **Maps to:** F-110; CAP-3.3
* **Size:** M
* **Dependencies:** US-3.1

### US-3.4 — Group Pot Creation, Membership & Verifiable Ledger

* **As a** P-4 (Community Organizer), **I want to** create a Group Pot, invite members by `PHONE | EMAIL | MEMBER_ID`, and configure an m-of-n collective approval rule for outbound transactions, **so that** my group can pool and oversee a collective treasury with a ledger every member can verify.
* **Description:** Pot creation with named purpose, invitations to ACTIVE members, configurable m-of-n approval threshold, contribution tracking per member, and a shared sub-ledger (balance, history, per-member contribution breakdown) visible to all pot members in real time. Inbound contributions need no approval; outbound execution is US-3.5. Roles are creator/member only at launch; delegated treasurer roles are a later enhancement.
* **Maps to:** F-111; CAP-3.4
* **Size:** L
* **Dependencies:** US-3.1, US-4.1
* **INVEST note:** Sprint 3 sized this XL as one story (CAT-1+CAT-2); it is pre-split here into US-3.4 (structure/ledger) and US-3.5 (approval workflow). If still too large, split invitations/membership from ledger visibility.

### US-3.5 — Group Pot Outbound Approval Workflow (m-of-n)

* **As a** P-4 (Community Organizer), **I want** every outbound transfer from a Group Pot to require the configured m-of-n approvals before execution, **so that** no individual can move the group's money unilaterally.
* **Description:** Outbound requests enter a pending-approval state; all designated approvers are notified with amount, recipient, and purpose; approvals/rejections are collected in-app; on reaching threshold the transfer executes and all pot members are notified, and if the threshold becomes unreachable the request is cancelled. Every decision is written to the pot's ledger and the immutable audit log (US-13.3). Time-outs and reminder nudges are in scope; approval delegation is not.
* **Maps to:** F-111; CAP-3.4
* **Size:** M
* **Dependencies:** US-3.4, US-11.1

---

## EP-4 — Payments & Transfers (CAP-4)

### US-4.1 — Instant Internal P2P Transfer

* **As a** P-2 (Digital-Native Member), **I want to** send money instantly and free to another member addressed by registered phone number, email address, or Member ID, **so that** I can pay people without exchanging account numbers.
* **Description:** Recipient lookup strictly via `RecipientIdentifierType = PHONE | EMAIL | MEMBER_ID` (usernames/handles are not supported, DEC-3); recipient display-name confirmation before send; instant ledger settlement with 0₮ fees; notifications to both parties; per-transaction and velocity limits configurable via US-12.5. Transfers feed AML monitoring (US-13.1). Requests for payment are US-4.4.
* **Maps to:** F-112; CAP-4.1
* **Size:** M
* **Dependencies:** US-3.2, US-1.4

### US-4.2 — External Payments (ACH, Wire, Real-Time Rails)

* **As a** P-3 (Flexible Earner), **I want to** move money between my cooperative accounts and external bank accounts — including same-day and real-time options where rails permit — **so that** I can receive client income and pay external obligations from one place.
* **Description:** Inbound and outbound ACH, outbound wire, and real-time rails (FedNow / SEPA Instant as available); external account linking with verification; cut-off times, status tracking, returns/failure handling, and step-up authentication above thresholds (US-1.4). Fees and limits configured via US-12.5; all flows monitored by US-13.1. FX/multi-currency is out of scope (MNT only, DEC-18).
* **Maps to:** F-113; CAP-4.2
* **Size:** L
* **Dependencies:** US-3.2, US-1.4
* **INVEST note:** Multi-rail integration; if it exceeds a sprint, split by rail (ACH first, then wire, then real-time) — each rail is independently shippable.

### US-4.3 — Bill Pay & Scheduled / Recurring Transfers

* **As a** P-3 (Flexible Earner), **I want to** schedule future-dated and recurring payments with automatic retry and failure notifications, **so that** my regular obligations are met even when my income timing varies.
* **Description:** One-off future-dated and recurring schedules over internal (US-4.1) and external (US-4.2) payments; payee management; insufficient-funds retry policy with member notification (US-11.1); pause/edit/cancel of schedules. Payee bill-presentment (e-bills) is out of scope for launch.
* **Maps to:** F-114; CAP-4.3
* **Size:** M
* **Dependencies:** US-4.1, US-4.2

### US-4.4 — Expense Splitting & Payment Requests

* **As a** P-2 (Digital-Native Member), **I want to** split a transaction among other members and send payment requests they can settle in one tap, **so that** shared costs get repaid without awkward reminders.
* **Description:** Select a Transaction Account entry (or enter an ad-hoc amount), split equally or by custom shares among members addressed per DEC-3, and issue payment requests; recipients settle via US-4.1 with the request auto-reconciled; requester sees who has paid, with optional reminder nudges. Splitting with non-members (external links) is out of scope.
* **Maps to:** F-115; CAP-4.4
* **Size:** M
* **Dependencies:** US-4.1

---

## EP-5 — Card Management (CAP-5)

### US-5.1 — Instant Virtual Debit Card & Wallet Tokenization

* **As a** P-2 (Digital-Native Member), **I want** a virtual debit card issued instantly at account opening and added to Apple Pay / Google Pay in a few taps, **so that** I can spend from my Transaction Account the moment I join.
* **Description:** Automatic virtual card issuance on Transaction Account opening; secure in-app PAN/CVV reveal behind step-up authentication (US-1.4); wallet tokenization for Apple Pay and Google Pay; card transactions post to the Transaction Account and drive Round-Ups (EP-10). Issuer-processor integration is in scope; disputes/chargebacks are handled operationally via US-12.1 case notes at launch.
* **Maps to:** F-116; CAP-5.1, CAP-5.4
* **Size:** M
* **Dependencies:** US-3.2, US-1.4

### US-5.2 — Physical Debit Card Ordering, Fulfilment & Activation

* **As a** P-3 (Flexible Earner), **I want to** order an optional physical debit card, track its delivery, and activate it and manage its PIN in-app, **so that** I can pay where wallets and virtual cards are not accepted.
* **Description:** Order flow using the DEC-6 structured address; embossed name taken verbatim from `mrz_name_latin` (never transliterated from the Cyrillic name fields — see DEC-6(b)); if `mrz_name_latin` is absent the physical order is blocked rather than guessed; fulfilment status tracking; in-app activation and PIN set/change; lost/stolen replacement reusing the same flow. Card artwork/personalization options are out of scope.
* **Maps to:** F-117; CAP-5.2
* **Size:** M
* **Dependencies:** US-5.1

### US-5.3 — Card Controls (Freeze, Limits, Category Blocks)

* **As a** P-2 (Digital-Native Member), **I want to** instantly freeze/unfreeze any of my cards and set spending limits and online/ATM/merchant-category toggles, **so that** I control exactly how my cards can be used.
* **Description:** Per-card controls applied at authorization time: freeze (declines with an explanatory notification), per-period spending limits, and channel/merchant-category toggles. Changes take effect in seconds and are logged to US-13.3. Applies to both virtual and physical cards.
* **Maps to:** F-118; CAP-5.3
* **Size:** S
* **Dependencies:** US-5.1

---

## EP-6 — Lending & Loan Circles (CAP-6)

Origination through servicing, including the cooperative's signature peer-guaranteed constructs per DEC-7: the **Loan Circle** (3–5 guarantors pledging savings/share capital) and the **Pooled Loan Circle** (ROSCA variant). Loan lifecycle uses `LoanStatus` (DEC-20) throughout.

### US-6.1 — Digital Loan Application & Instant Conditional Offers

* **As a** P-3 (Flexible Earner), **I want to** apply in-app for a personal or micro-business loan, state my purpose and affordability inputs, and receive an instant conditional offer, **so that** I can access fair credit without paperwork or branch appointments.
* **Description:** Product selection, amount/term inputs with a live repayment estimator, purpose capture, and affordability declarations; submission moves the loan `DRAFT → SUBMITTED` and into decisioning (US-6.2). The offer screen shows rate, schedule, and — where a Loan Circle is attached (US-6.3) — the standard rate versus the peer-guaranteed discounted rate side by side. Only ACTIVE members may apply (US-2.2).
* **Maps to:** F-119; CAP-6.1
* **Size:** M
* **Dependencies:** US-3.2, US-2.2

### US-6.2 — Automated Underwriting with Cooperative History

* **As a** P-3 (Flexible Earner), **I want** underwriting that weighs my open-banking transaction data, optional bureau data, and my cooperative history (savings, repayment record, governance participation) rather than payroll income alone, **so that** my irregular gig income doesn't disqualify me from fair credit.
* **Description:** Decision engine combining open-banking analysis, optional bureau pulls, and cooperative-history factors; produces approve (`UNDER_REVIEW → APPROVED`), decline with reasons and adverse-action notice, or referral to the manual queue (US-12.3). Rate discounts earned through cooperative engagement are itemized to the applicant (absorbing Sprint 1 US-5.1b). Model parameters are configurable (US-12.5) and decisions are fully logged (US-13.3) for fair-lending review.
* **Maps to:** F-120; CAP-6.2
* **Size:** L
* **Dependencies:** US-6.1
* **INVEST note:** At risk on Small. Split hint: (a) rules-based decisioning on cooperative history, (b) open-banking data ingestion, (c) bureau integration — shippable in that order.

### US-6.3 — Loan Circle Creation & Guarantor Invitations

* **As a** P-3 (Flexible Earner), **I want to** create a Loan Circle for my application and invite 3–5 ACTIVE members to vouch for me, **so that** community trust can reduce my interest rate where my credit file is thin.
* **Description:** Circle creation from a loan application; invitations addressed per DEC-3 with full disclosure of amount, term, and requested pledge; a circle forms when 3–5 invitees accept (DEC-7). Invitees see the borrower's request and the risks before accepting; declining is frictionless and private. The pledge itself, and its financial consequences, are US-6.4. Merges Sprint 2 Story 2.1 and Sprint 3 PSL-2 (invitation half).
* **Maps to:** F-121; CAP-6.3
* **Size:** M
* **Dependencies:** US-6.1

### US-6.4 — Guarantee Pledge Locking, Rate Reduction & Release

* **As a** P-4 (Community Organizer acting as guarantor), **I want to** pledge a stated portion of my savings or share capital for a borrower in my Loan Circle, see it locked for the loan term, and get it released pro-rata as they repay, **so that** I can responsibly back members of my community.
* **Description:** Pledge amount selection up to available balance; e-signed pledge agreement (via US-6.6) spelling out default consequences; immediate lock of the guarantee pledge (excluded from withdrawal, transfer, and Round-Up sweeps); underwriting (US-6.2) applies the tiered rate reduction based on pledged coverage; pro-rata release on principal repayment and defined treatment on `DEFAULTED`. Guarantors get a dashboard of outstanding pledges and exposure. Legal enforceability of pledged share capital is Open Item 2 — implement the hold mechanics behind a jurisdiction flag. Merges Sprint 2 Stories 2.2/2.3 and Sprint 3 PSL-2 (pledge half).
* **Maps to:** F-121; CAP-6.3
* **Size:** L
* **Dependencies:** US-6.3, US-6.6
* **INVEST note:** At risk on Independent (touches ledger holds, underwriting pricing, and servicing release). Split hint: (a) pledge capture + lock, (b) pricing integration, (c) pro-rata release/default handling.

### US-6.5 — Pooled Loan Circle (ROSCA)

* **As a** P-3 (Flexible Earner), **I want to** join a Pooled Loan Circle where each member contributes a fixed monthly amount and we take turns receiving the lump sum on a schedule agreed at creation, **so that** I can access interest-free capital through disciplined group saving.
* **Description:** Circle creation with contribution amount, duration, participant list, and payout order (agreed or randomized) fixed at creation; automated monthly collection from each participant's account and lump-sum payout to that month's beneficiary; missed-contribution handling (alerts to the circle, retry, and configurable backstop rules); full circle ledger visible to all participants. From Sprint 3 PSL-1; P3 priority — build after core lending is stable.
* **Maps to:** F-122; CAP-6.4
* **Size:** XL
* **Dependencies:** US-4.1, US-3.1, US-11.1
* **INVEST note:** XL — must be split before scheduling. Suggested slices: (a) circle setup and rotation schedule, (b) automated collection + payout engine, (c) missed-payment risk handling, (d) circle ledger/transparency views. Slice (a)+(b) is a shippable minimum.

### US-6.6 — E-Signature & Loan Document Vault

* **As a** P-3 (Flexible Earner), **I want to** e-sign my loan agreement in-app and retrieve all my signed agreements and related documents any time, **so that** borrowing is legally sound and paper-free.
* **Description:** Legally compliant e-signature ceremony (identity-bound via US-1.4, timestamped, tamper-evident) for loan agreements and guarantee pledge agreements; encrypted document vault with member access to their own documents and admin access via US-12.3. Applies to any future agreement types; document generation templates are configuration, not code.
* **Maps to:** F-123; CAP-6.5
* **Size:** M
* **Dependencies:** US-6.2

### US-6.7 — Loan Servicing, Disbursement & Flexible Repayment

* **As a** P-3 (Flexible Earner), **I want** my approved loan disbursed to my account and repaid on a schedule that can flex with seasonal or irregular income — with autopay and payoff quotes — **so that** repayment fits how I actually earn.
* **Description:** Disbursement on signing (`APPROVED → ACTIVE`); standard, seasonal, and income-linked repayment schedules; direct-debit autopay with retry; extra-payment and full-payoff quotes; amortization and history views; transitions to `PAID_OFF`, and to `DELINQUENT` on missed payments (hand-off to US-6.8). Guarantee-pledge release hooks call US-6.4. Restructuring by staff is US-12.3.
* **Maps to:** F-124; CAP-6.6
* **Size:** L
* **Dependencies:** US-6.6, US-6.2
* **INVEST note:** Split hint if needed: (a) disbursement + standard schedule + autopay, (b) flexible/seasonal schedules, (c) payoff quotes and early repayment.

### US-6.8 — Arrears Monitoring, Guarantor Alerts & Hardship Rescheduling

* **As a** P-3 (Flexible Earner), **I want** early, non-punitive warnings when a repayment is at risk or missed, a self-service hardship rescheduling request, and — where a Loan Circle backs my loan — timely notice to my guarantors, **so that** temporary trouble doesn't spiral into default.
* **Description:** Early-warning triggers (upcoming payment vs. low balance, failed collection), borrower notifications with clear options, guarantor notifications at defined `DELINQUENT` milestones before any pledge is drawn, and a hardship workflow that routes a proposed reschedule to US-12.3 for approval. Creates and updates collections cases in the staff queue; supports KPI-2.5 (NPL ≤ 1.8% Year 1). Write-offs (`WRITTEN_OFF`) are admin-only via US-12.3.
* **Maps to:** F-125; CAP-6.7
* **Size:** M
* **Dependencies:** US-6.7, US-11.1

---

## EP-7 — Dividends & Surplus Distribution (CAP-7)

The annual **Patronage Dividend** cycle per DEC-10: surplus tracked all year, member-facing **Dividend Estimator** in real time, calculation and payout after AGM ratification (within 5 business days, KPI-4.3).

### US-7.1 — Patronage Calculation Engine

* **As a** P-5 (Cooperative Operations Administrator), **I want** an engine that computes each member's annual Patronage Dividend from the ratified surplus using weighted patronage factors — savings balances, transaction volume, loan repayment performance, and governance participation — **so that** the distribution is accurate, explainable, and reproducible.
* **Description:** Year-long accumulation of per-member patronage factor data; a calculation run that takes the AGM-ratified surplus and factor weights as inputs and produces a per-member entitlement statement with a full explainability breakdown; deterministic re-runs and reconciliation totals (sum of entitlements = distributable pool). Factor weights are configuration subject to FINANCIAL_POLICY proposals (via US-8.2/US-12.5), never hard-coded. Execution/approval workflow is US-12.6; payout is US-7.2.
* **Maps to:** F-126; CAP-7.1, CAP-7.2
* **Size:** L
* **Dependencies:** US-3.1, US-6.7, US-8.1
* **INVEST note:** Split hint: (a) patronage data accumulation, (b) calculation + explainability, (c) reconciliation and re-run controls.

### US-7.2 — Automated Dividend Payout with Member Election

* **As a** P-3 (Flexible Earner), **I want** my approved Patronage Dividend deposited automatically — to my Primary Savings Account or reinvested as share capital, per my standing election — **so that** I receive my share of the surplus without claiming anything.
* **Description:** Member election (savings vs. share reinvestment) set any time before the run; batch payout executing the approved calculation within 5 business days of AGM ratification (KPI-4.3); per-member notification with the amount and explainability link; failed-posting handling and full reconciliation report to US-12.6. Merges Sprint 3 DMA-2 with the reinvestment option from the feature catalog.
* **Maps to:** F-127; CAP-7.3
* **Size:** M
* **Dependencies:** US-7.1, US-12.6

### US-7.3 — Real-Time Dividend Estimator

* **As a** P-2 (Digital-Native Member), **I want** a live projection of my annual Patronage Dividend that shows exactly which behaviors — saving, transacting, repaying on time, voting — raise it, **so that** I can see the payoff of participating in the cooperative all year, not just at the AGM.
* **Description:** Member dashboard projecting the annual dividend from current patronage factors and a cooperative surplus forecast, refreshed at least daily; behavior-linked suggestions (e.g., estimated effect of additional savings or of voting in the open ballot); all projected figures labeled "estimated" per DEC-15's no-invented-facts rule. Merges Sprint 1 US-6.3b, Sprint 2 Stories 4.1/4.2, Sprint 3 DMA-1; the drafts' quarterly-payout framing is superseded by DEC-10 (annual cycle, real-time estimator).
* **Maps to:** F-128; CAP-7.4
* **Size:** M
* **Dependencies:** US-3.1, US-7.1 (factor data model; can ship against interim forecast inputs)

### US-7.4 — Dividend & Tax Statements

* **As a** P-1 (Values-Driven Saver), **I want** an annual statement of my Patronage Dividend and any required tax documents available in-app, **so that** I can file taxes correctly without contacting support.
* **Description:** Post-payout generation of member statements (dividend amount, factor breakdown, payout destination) and jurisdictional tax reporting artifacts; in-app retrieval and download; P-5 receives the aggregate reporting extract for filing. Statement templates are configuration; delivery notifications via US-11.1.
* **Maps to:** F-129; CAP-7.5
* **Size:** M
* **Dependencies:** US-7.2

---

## EP-8 — Democratic Governance & Voting (CAP-8)

One member, one vote; secret ballot; `VoteChoice = FOR | AGAINST | ABSTAIN` (DEC-1); `BallotType = PROPOSAL | BOARD_ELECTION` (DEC-2); Proxy Delegation per DEC-8. Supports KPI-3.1 (Governance Participation Rate ≥ 40% Year 1).

### US-8.1 — Voting Portal: Browse Ballots & Cast a Secret Ballot

* **As a** P-1 (Values-Driven Saver), **I want to** browse open ballots with their full context and cast a secret ballot of `FOR`, `AGAINST`, or `ABSTAIN` from my phone, **so that** I exercise my democratic voice in minutes.
* **Description:** Ballot list and detail views (title, category, rationale, discussion link, closing time, live participation percentage), filtered by open/voted/closed; eligibility checked against the ballot's snapshot (US-2.3); step-up authentication at submission (US-1.4); double-vote prevention; a verifiable receipt that never reveals vote content; a member's direct vote supersedes any delegated vote on that ballot (DEC-8). Merges Sprint 1 US-4.2a/US-4.2b, Sprint 2 Story 3.1, Sprint 3 DGV-1; the drafts' "Yes/No" wording is superseded by DEC-1.
* **Maps to:** F-130; CAP-8.2
* **Size:** L
* **Dependencies:** US-2.3, US-1.4
* **INVEST note:** Split hint: (a) read-only ballot browsing, (b) secret-ballot casting with receipt — (a) is independently demoable.

### US-8.2 — Proposal Builder with Co-Signature Gathering

* **As a** P-4 (Community Organizer), **I want to** draft a proposal, classify it as `COMMUNITY_GRANT`, `FINANCIAL_POLICY`, or `GOVERNANCE_BYLAW`, gather the required member co-signatures, and submit it for scheduling, **so that** members set the cooperative's agenda, not just react to it.
* **Description:** Structured drafting (title, summary, body, category per DEC-2); lifecycle per DEC-9 (`DRAFT → SUBMITTED`, with `WITHDRAWN` available to the author before ballot open); publication of drafts for co-signature with a progress bar toward the configured threshold; automatic transition to `SUBMITTED` at threshold, entering the US-12.4 review/scheduling queue; `OPEN_FOR_VOTING` is set only by ballot scheduling. Supports KPI-3.3 (≥ 1 member proposal reaching ballot per month from Month 6). Merges Sprint 3 DGV-3 with the feature-catalog scope.
* **Maps to:** F-131; CAP-8.1
* **Size:** L
* **Dependencies:** US-2.2
* **INVEST note:** Split hint: (a) drafting + category + DEC-9 lifecycle, (b) co-signature gathering and threshold automation.

### US-8.3 — Board Elections

* **As a** P-1 (Values-Driven Saver), **I want to** review board candidate profiles and statements and vote for up to the allowed number of seats in a `BOARD_ELECTION` ballot, **so that** the cooperative's leadership is chosen by its members.
* **Description:** Candidate slates with profiles and statements; choose-up-to-N-seats ballot on the same secret-ballot engine as US-8.1 (eligibility snapshot, receipt, one member one ballot); certified results published with turnout; term tracking for elected directors. Election scheduling, candidate administration, and certification are P-5 duties in US-12.4. Candidate nomination/self-service applications are out of scope for launch.
* **Maps to:** F-132; CAP-8.3
* **Size:** L
* **Dependencies:** US-8.1, US-12.4

### US-8.4 — Proxy Delegation Setup

* **As a** P-3 (Flexible Earner), **I want to** delegate my vote — per `ProposalCategory` and/or for `BOARD_ELECTION` — to one trusted ACTIVE member per scope, **so that** my voice counts even in months when I have no time to study ballots.
* **Description:** Delegation management screen: pick a scope, pick exactly one ACTIVE member (addressed per DEC-3), confirm with step-up auth; delegate consent to receive delegations; strictly single-level per DEC-8 (a delegate cannot re-delegate a received vote, enforced server-side); the governance dashboard always shows current delegations. Delegated participation counts toward the delegator's Governance Participation Rate (DEC-16). Supports KPI-3.2 (≥ 20% adoption).
* **Maps to:** F-133; CAP-8.4
* **Size:** M
* **Dependencies:** US-8.1

### US-8.5 — Proxy Revocation & Direct-Vote Override

* **As a** P-1 (Values-Driven Saver), **I want to** revoke any delegation instantly and override my delegate on any individual ballot by voting directly before it closes, **so that** I always retain final control of my vote.
* **Description:** One-tap revocation restoring direct voting for the scope; on any open ballot, the delegator's direct vote voids the delegate-cast vote for that ballot only and tallies update accordingly (DEC-8); the delegate is not shown how the delegator voted (secret ballot preserved). Edge cases in scope: delegate becomes SUSPENDED/CLOSED (delegation auto-voids with notification). Merges Sprint 2 Story 3.3.
* **Maps to:** F-133; CAP-8.4
* **Size:** M
* **Dependencies:** US-8.4

### US-8.6 — Proposal Discussion Threads

* **As a** P-1 (Values-Driven Saver), **I want** a threaded discussion attached to each proposal where members debate before voting, **so that** I can make an informed choice, not a blind one.
* **Description:** Per-proposal threads with replies and reporting; community-standards moderation tooling (hide/remove with reason, member reporting queue); automatic thread lock when the ballot opens (`OPEN_FOR_VOTING`), preserving the record read-only. Moderation actions are audit-logged (US-13.3). General-purpose social feeds are out of scope — threads exist only on proposals.
* **Maps to:** F-134; CAP-8.5
* **Size:** M
* **Dependencies:** US-8.2

### US-8.7 — Governance Archive & Audit Trail

* **As a** P-4 (Community Organizer), **I want** a permanent, member-visible archive of every proposal, ballot, turnout figure, certified outcome, and meeting minutes, **so that** the cooperative's democratic record is transparent and tamper-proof.
* **Description:** Immutable governance record (backed by US-13.3) covering the full DEC-9 lifecycle of each proposal, `PASSED`/`REJECTED` outcomes (including `QUORUM_NOT_MET` rejections), certified election results, Governance Participation Rate per ballot, and uploaded minutes; searchable and readable by all members. Certification itself is performed in US-12.4; this story delivers storage and the member-facing archive.
* **Maps to:** F-135; CAP-8.6
* **Size:** M
* **Dependencies:** US-8.1

---

## EP-9 — Community Funding Hub (CAP-9)

The DEC-14 noun set applies verbatim: **Community Project** (listed initiative), **Backing** (member's direct contribution), **Community Grant** (surplus-funded pool), **Surplus Match** (≤ 1:1 cooperative match). Supports KPI-4.4 (≥ $1.5M community capital in Year 1).

### US-9.1 — Community Project Pitch Submission & Review

* **As a** P-4 (Community Organizer), **I want to** submit a Community Project — goals, budget, timeline, impact description, supporting documents — to the Pitch Board and have it reviewed before publication, **so that** my initiative can raise capital from members who share its values.
* **Description:** Submission by members or registered local organizations; structured pitch form with document upload; admin review queue (approve/decline with reasons) before anything is published; published projects appear on the member-facing Pitch Board with funding progress. Merges Sprint 2 Story 5.1 and Sprint 3 CIF-1 (listing half); the drafts' "Pitch Desk"/"Crowdfunding Hub" names are superseded by DEC-14.
* **Maps to:** F-136; CAP-9.1
* **Size:** M
* **Dependencies:** US-2.2

### US-9.2 — Backing a Community Project from Savings

* **As a** P-1 (Values-Driven Saver), **I want to** back a Community Project directly from my Primary Savings Account and follow its progress and updates in-app, **so that** my money visibly builds the community I live in.
* **Description:** One-time (and optionally recurring) Backing from savings with balance validation; per-project funding progress in real time; contribution history in the member's profile; project-poster updates pushed to backers; refund of Backings if a project misses its goal by deadline (configurable all-or-nothing rule). Any yield/return language must be labeled "estimated" per DEC-15. Merges Sprint 2 Story 5.2 and Sprint 3 CIF-1 (contribution half).
* **Maps to:** F-137; CAP-9.2
* **Size:** M
* **Dependencies:** US-9.1, US-3.1

### US-9.3 — Surplus Matching Engine

* **As a** P-4 (Community Organizer), **I want** approved projects to receive up to a 1:1 Surplus Match from the Community Grant pool, released under `COMMUNITY_GRANT` ballot decisions, **so that** member Backing is amplified by the cooperative's collective surplus.
* **Description:** Community Grant pool funded at 10% of annual surplus (KPI-4.2); match accrual against eligible member Backings up to per-project caps and the pool budget; match release governed by `COMMUNITY_GRANT` ballots (US-8.1/US-8.2) rather than staff discretion; automatic halt when a project cap or the pool is exhausted; full traceability of every matched dollar. Merges Sprint 2 Story 5.3 and Sprint 3 CIF-2.
* **Maps to:** F-138; CAP-9.3
* **Size:** L
* **Dependencies:** US-9.2, US-8.1
* **INVEST note:** Split hint: (a) pool accounting + match calculation, (b) ballot-governed release workflow.

### US-9.4 — Project Allocation & Impact Tracker

* **As a** P-1 (Values-Driven Saver), **I want to** see, per project I backed, how funds were used and what outcomes resulted, **so that** I can verify the impact claims that drew me to this cooperative.
* **Description:** Per-project fund-allocation reporting (raised, matched, disbursed, spent by category) and outcome reporting supplied by project owners; every modeled figure (e.g., CO2 offset equivalents) labeled "estimated" per DEC-15; aggregate feeds into the Transparent Capital Ledger (US-13.4) and Impact Scorecard (US-13.5). Social sharing of project impact is a nice-to-have within this story.
* **Maps to:** F-139; CAP-9.4
* **Size:** M
* **Dependencies:** US-9.2

---

## EP-10 — Round-Up Savings & Micro-Contributions (CAP-10)

**Round-Up** per DEC-12: card transactions rounded to the nearest dollar, the difference routed to a member-chosen destination — a Savings Goal or a Community Project.

### US-10.1 — Round-Up Enrollment & Destination Choice

* **As a** P-2 (Digital-Native Member), **I want to** switch Round-Ups on, choose whether the spare change goes to one of my Savings Goals or to a Community Project, and set an optional multiplier and monthly cap, **so that** saving or giving happens automatically as I spend.
* **Description:** Settings screen: on/off toggle, destination picker (Savings Goal from US-3.3 or published Community Project from US-9.1 — the only two destinations, per DEC-12), optional 1x/2x/3x multiplier and monthly cap; changes take effect on the next card transaction. Merges Sprint 1 US-2.3a and Sprint 2 Story 6.1; the drafts' "Smart Savings"/"Ethical Round-Ups" names are superseded by DEC-12.
* **Maps to:** F-140; CAP-10.2
* **Size:** S
* **Dependencies:** US-5.1, US-3.3

### US-10.2 — Round-Up Capture & Routing Execution

* **As a** P-2 (Digital-Native Member), **I want** each settled card transaction rounded to the nearest dollar and the difference accumulated and transferred to my chosen destination, with a running total of what my Round-Ups have achieved, **so that** my micro-contributions add up without me thinking about them.
* **Description:** Capture engine computing the round-up on each settled card transaction (whole-dollar transactions produce $0.00); accumulation and batched transfer at a threshold (e.g., $5.00) from the Transaction Account to the destination, skipping gracefully on insufficient funds; clearly labeled ledger entries linking purchase and Round-Up; running savings/impact total in the app (impact figures labeled "estimated"). Merges Sprint 1 US-2.3b and Sprint 2 Stories 6.2/6.3.
* **Maps to:** F-140; CAP-10.1, CAP-10.2
* **Size:** M
* **Dependencies:** US-10.1

---

## EP-11 — Notifications & Engagement (CAP-11)

### US-11.1 — Notification Delivery & Event Catalog

* **As a** P-2 (Digital-Native Member), **I want** real-time notifications — push, email, SMS, and an in-app inbox — for payments, governance deadlines, loan milestones, and dividend events, **so that** I never miss money movement or a chance to vote.
* **Description:** Multi-channel delivery service plus a governed event catalog with triggers spanning the platform: payment sent/received, card authorization/decline, Group Pot approval requests, ballot opening/closing reminders, delegation events, loan disbursement/due/`DELINQUENT` alerts, guarantee-pledge events, dividend estimator milestones and payout, and project updates. Each event carries a deep link to the relevant screen. New event types must be added via catalog configuration, not code forks.
* **Maps to:** F-141; CAP-11.1, CAP-11.2
* **Size:** L
* **Dependencies:** US-2.1
* **INVEST note:** Cross-cutting platform service. Split hint: (a) delivery infrastructure + in-app inbox, (b) event catalog with the payments/governance trigger sets, then extend per epic.

### US-11.2 — Notification Preferences & Quiet Hours

* **As a** P-2 (Digital-Native Member), **I want to** choose channels per notification category and set quiet hours, **so that** I stay informed without being nagged at midnight.
* **Description:** Per-category, per-channel preference matrix; quiet hours with timezone awareness; regulatory/security notices (e.g., fraud alerts, mandated disclosures) are exempt from suppression and clearly marked as such. Preferences stored against the member profile (US-1.5) and honored by US-11.1 at dispatch.
* **Maps to:** F-141; CAP-11.3
* **Size:** S
* **Dependencies:** US-11.1

---

## EP-12 — Admin & Back-Office (CAP-12)

All P-5 stories. Every mutating action in this epic operates under four-eyes/maker-checker and is written to the immutable audit log (US-13.3).

### US-12.1 — Member Management Console (360° View, Maker-Checker Status Changes)

* **As a** P-5 (Cooperative Operations Administrator), **I want** a 360° member view — profile, `MembershipStatus` and `KycStatus`, accounts, loans, guarantees, governance activity, cases, and a unified timeline — with status transitions (suspend, reinstate, close) executed under maker-checker, **so that** I can serve and govern members from one place instead of swivel-chair systems.
* **Description:** Web back-office console with role-based access; member search; the unified timeline; case notes; and initiation/approval separation for every DEC-4 status transition (a second operator must approve before SUSPENDED/CLOSED takes effect). Consumes the domain rules delivered in US-2.2. Financial adjustments and loan actions live in US-12.3; product parameters in US-12.5.
* **Maps to:** F-142; CAP-12.1
* **Size:** L
* **Dependencies:** US-2.2, US-1.5
* **INVEST note:** Split hint: (a) read-only 360° view + search, (b) maker-checker status transitions + case notes.

### US-12.2 — KYC / AML Case Management Queues

* **As a** P-5 (Cooperative Operations Administrator), **I want** work queues for KYC escalations (`KycStatus = PENDING_REVIEW`) and AML alerts, with assignment, SLA timers, evidence view, decisioning, and escalation, **so that** manual reviews are resolved quickly and consistently.
* **Description:** Queue management for onboarding escalations from US-1.2 (review Persona evidence, approve → `APPROVED`, or reject → `REJECTED` with reason codes) and for AML alerts raised by US-13.1 (triage, investigate against the member 360°, escalate to SAR workflow); four-eyes on rejections; complete decision audit trail. Directly protects KPI-1.1/1.2 by keeping manual-review turnaround short.
* **Maps to:** F-142; CAP-12.2
* **Size:** M
* **Dependencies:** US-1.2, US-12.1

### US-12.3 — Loan Operations Console

* **As a** P-5 (Cooperative Operations Administrator), **I want** a console for manual underwriting review, loan restructuring, guarantee-pledge administration, collections cases, and write-offs, **so that** edge-case lending decisions are handled by humans with full context and control.
* **Description:** Referral queue from US-6.2 with the full application, data inputs, and recommendation; approve/decline/counter-offer under maker-checker; restructuring tools executing hardship reschedules from US-6.8; guarantee-pledge administration (view, partial release, default application per US-6.4 rules); collections case management; `DEFAULTED → WRITTEN_OFF` under dual approval. Feeds portfolio-quality data to US-13.2 (KPI-2.5).
* **Maps to:** F-143; CAP-12.3
* **Size:** L
* **Dependencies:** US-6.2, US-6.7, US-12.1

### US-12.4 — Governance Administration (Scheduling, Quorum, Certification)

* **As a** P-5 (Cooperative Operations Administrator), **I want to** review `SUBMITTED` proposals, schedule ballots and elections with voting windows and quorum configuration, and certify and publish results, **so that** every ballot is procedurally sound and its outcome is authoritative.
* **Description:** Scheduling of both `BallotType = PROPOSAL` and `BOARD_ELECTION` ballots (window, quorum, result-visibility rules); moving proposals `SUBMITTED → OPEN_FOR_VOTING`; candidate-slate administration for elections; certification workflow computing `PASSED`/`REJECTED` (with `QUORUM_NOT_MET` reason where applicable) under maker-checker; publication to the archive (US-8.7). Governance Participation Rate (DEC-16) is computed and recorded per ballot.
* **Maps to:** F-144; CAP-12.4
* **Size:** M
* **Dependencies:** US-8.1, US-8.2, US-12.1

### US-12.5 — Product & Fee Configuration

* **As a** P-5 (Cooperative Operations Administrator), **I want to** administer interest rates, fees, share par value, transaction limits, underwriting parameters, and patronage factor weights with effective-dating, maker-checker approval, and full audit, **so that** ratified policy changes reach production safely without releases.
* **Description:** Configuration registry with versioning, effective dates, and dual approval; consumers include US-3.1 (rates), US-4.1/US-4.2 (limits/fees), US-2.1 (share par), US-6.2 (underwriting parameters), and US-7.1 (factor weights). Where a parameter is governed by a `FINANCIAL_POLICY` or `GOVERNANCE_BYLAW` outcome, the change record links to the certified ballot — configuration is the execution of democracy, and the link is mandatory.
* **Maps to:** F-145; CAP-12.5
* **Size:** M
* **Dependencies:** US-12.1

### US-12.6 — Dividend Run Administration

* **As a** P-5 (Cooperative Operations Administrator), **I want to** input the AGM-ratified surplus, run and review the patronage calculation, obtain approval, execute the payout, and reconcile the run, **so that** 100% of approved Patronage Dividends are distributed within 5 business days of ratification.
* **Description:** End-to-end run workflow over US-7.1/US-7.2: surplus and Community Grant pool (10%) input with linkage to the ratifying AGM record; dry-run with sample-level review and exception surfacing; dual approval to execute; live payout monitoring; reconciliation report (entitlements vs. postings vs. pool) and exception handling; immutable record of the whole run. Anchors KPI-4.1/4.2/4.3.
* **Maps to:** F-146; CAP-12.6
* **Size:** M
* **Dependencies:** US-7.1, US-12.1

---

## EP-13 — Compliance, Risk & Transparency (CAP-13)

### US-13.1 — Ongoing AML Transaction Monitoring & SAR Workflow

* **As a** P-5 (Cooperative Operations Administrator), **I want** continuous rules/ML monitoring of all money movement with alert triage and a suspicious-activity report preparation workflow, **so that** the cooperative meets its AML obligations and bad actors are caught early.
* **Description:** Real-time and batch monitoring across P2P, external payments, card activity, Group Pots, Loan Circles, and project Backings; tunable rule sets and scenario management; alerts routed to the US-12.2 queue; SAR case assembly (narrative, evidence bundle, filing-ready output) with dual review; tipping-off safeguards (no member-visible traces). Rule tuning is P-5 configuration; model governance documentation is in scope.
* **Maps to:** F-147; CAP-13.1
* **Size:** L
* **Dependencies:** US-4.1, US-4.2, US-12.2
* **INVEST note:** Split hint: (a) rules-based monitoring + alerting, (b) SAR case workflow, (c) ML scenario expansion.

### US-13.2 — Regulatory & Prudential Reporting Suite

* **As a** P-5 (Cooperative Operations Administrator), **I want** scheduled, one-click prudential and lending reports — capital adequacy, liquidity, deposit-to-loan ratio, portfolio quality/NPL — **so that** regulator and auditor requests are met from the system of record, not spreadsheets.
* **Description:** Report catalog with scheduling, point-in-time data snapshots, export in required formats, and a submission log; monitors KPI-2.3/2.4/2.5 thresholds with breach alerts to P-5. Report definitions are configuration-driven to absorb charter-dependent requirements (Open Item 3: deposit-insurance representation depends on the final charter).
* **Maps to:** F-148; CAP-13.2
* **Size:** M
* **Dependencies:** US-3.1, US-6.7

### US-13.3 — Immutable Audit Log

* **As a** P-5 (Cooperative Operations Administrator), **I want** an append-only, tamper-evident log of every financial, governance, and administrative action, **so that** any past state or decision can be reconstructed and defended.
* **Description:** Platform-wide audit service: append-only storage with cryptographic tamper evidence (e.g., hash chaining), standardized event envelope (actor, action, subject, before/after, timestamp), retention policy, and scoped query/export for audits. Consumed by every epic (notably US-2.2, US-3.5, US-8.7, US-12.x). Build early — retrofitting audit logging is the costliest sequencing mistake in this backlog.
* **Maps to:** F-149; CAP-13.3
* **Size:** M
* **Dependencies:** none (foundational; schedule alongside EP-1)

### US-13.4 — Transparent Capital Ledger

* **As a** P-1 (Values-Driven Saver), **I want** a visual, drill-down breakdown of how the cooperative's collective funds are deployed — local loans, green lending, Community Grants, liquidity reserves — refreshed at least daily, **so that** I can verify the ethical claims that made me join.
* **Description:** Member-facing allocation view (chart totals reconciling to 100% of managed funds) with drill-down to category detail and anonymized/consented funded-project spotlights; daily-or-better refresh from the ledger (superseding the Sprint 1 draft's weekly cache); DEC-15 naming and "estimated" labeling for any modeled figures. Merges Sprint 1 US-7.1a/US-7.1b and Sprint 3 CIF-3.
* **Maps to:** F-150; CAP-13.4
* **Size:** M
* **Dependencies:** US-3.1, US-6.7

### US-13.5 — Personal Impact Scorecard

* **As a** P-1 (Values-Driven Saver), **I want** a personal Impact Scorecard estimating the community and environmental impact attributable to my own deposits and Round-Ups, **so that** I can see — and share — what my money does.
* **Description:** Per-member proportional attribution over the Transparent Capital Ledger and project outcomes (US-9.4); every figure explicitly labeled "estimated" with methodology notes one tap away (DEC-15); optional social sharing of the scorecard. P3 priority — ship after US-13.4 has trustworthy underlying data.
* **Maps to:** F-151; CAP-13.4
* **Size:** M
* **Dependencies:** US-13.4, US-9.4

### US-13.6 — Data Privacy, Consent Enforcement & Subject-Access Requests

* **As a** P-5 (Cooperative Operations Administrator), **I want** consent records enforced across processing, retention schedules applied automatically, and a workflow to fulfil subject-access and deletion requests within statutory deadlines, **so that** the cooperative honors members' data rights by design.
* **Description:** Consent registry backing US-1.5; retention/erasure rules by record class (respecting financial-records retention obligations that override deletion); SAR/DSAR intake, compilation, redaction, and delivery workflow with deadline tracking; post-closure (`CLOSED`) data handling for US-2.4. Covers CAP-13.5 via its dedicated feature F-152 (Data Privacy & Consent Management), with consent capture anchored to F-105's scope.
* **Maps to:** F-152; F-105 (consent scope); CAP-13.5, CAP-1.6
* **Size:** M
* **Dependencies:** US-1.5, US-12.1

---

## Feature → Story Coverage Table

Every feature F-101…F-152 is covered by at least one story. No feature is intentionally story-less.

| Feature | Name (short) | Covered by | Notes |
| :--- | :--- | :--- | :--- |
| F-101 | Instant Digital Onboarding & eKYC | US-1.1, US-1.2 | Journey vs. Persona verification split |
| F-102 | Eligibility & Common-Bond Check | US-1.3 | |
| F-103 | Initial Membership Share Purchase | US-2.1 | |
| F-104 | MFA & Biometrics | US-1.4 | |
| F-105 | Member Profile & Consents | US-1.5, US-13.6 | US-13.6 extends consent scope to CAP-13.5 |
| F-106 | Membership Lifecycle Management | US-2.2, US-2.4 | Domain machine + member-initiated closure |
| F-107 | Share Registry & Voting Eligibility | US-2.3 | |
| F-108 | Primary Savings Account | US-3.1 | |
| F-109 | Transaction (Checking) Account | US-3.2 | |
| F-110 | Savings Goals | US-3.3 | |
| F-111 | Group Pots | US-3.4, US-3.5 | Structure/ledger + m-of-n approval |
| F-112 | Instant Internal P2P Transfer | US-4.1 | |
| F-113 | External Payments | US-4.2 | |
| F-114 | Bill Pay & Scheduled Transfers | US-4.3 | |
| F-115 | Expense Splitting & Payment Requests | US-4.4 | |
| F-116 | Virtual Debit Card | US-5.1 | |
| F-117 | Physical Debit Card | US-5.2 | |
| F-118 | Card Controls | US-5.3 | |
| F-119 | Digital Loan Application & Offers | US-6.1 | |
| F-120 | Automated Underwriting Engine | US-6.2 | |
| F-121 | Loan Circles (Peer Guarantees) | US-6.3, US-6.4 | Circle formation + pledge mechanics |
| F-122 | Pooled Loan Circles (ROSCA) | US-6.5 | XL, split hints given |
| F-123 | E-Signature & Document Vault | US-6.6 | |
| F-124 | Loan Servicing & Flexible Repayment | US-6.7 | |
| F-125 | Arrears Monitoring & Alerts | US-6.8 | Staff-side collections in US-12.3 |
| F-126 | Patronage Calculation Engine | US-7.1 | |
| F-127 | Automated Dividend Payout | US-7.2 | |
| F-128 | Real-Time Dividend Estimator | US-7.3 | |
| F-129 | Dividend & Tax Statements | US-7.4 | |
| F-130 | Voting Portal | US-8.1 | |
| F-131 | Proposal Builder | US-8.2 | |
| F-132 | Board Elections | US-8.3 | Admin side in US-12.4 |
| F-133 | Proxy Delegation | US-8.4, US-8.5 | Setup + revocation/override |
| F-134 | Proposal Discussion Threads | US-8.6 | |
| F-135 | Governance Archive & Audit Trail | US-8.7 | |
| F-136 | Community Project Pitch Board | US-9.1 | |
| F-137 | Member Backing & Co-Investment | US-9.2 | |
| F-138 | Surplus Matching Engine | US-9.3 | |
| F-139 | Project Impact Tracker | US-9.4 | |
| F-140 | Round-Up Savings | US-10.1, US-10.2 | Enrollment + capture/routing |
| F-141 | Notification Center & Preferences | US-11.1, US-11.2 | Delivery/catalog + preferences |
| F-142 | Admin Member Console | US-12.1, US-12.2 | 360° console + KYC/AML queues |
| F-143 | Admin Loan Operations Console | US-12.3 | |
| F-144 | Governance Administration | US-12.4 | |
| F-145 | Product & Fee Configuration | US-12.5 | |
| F-146 | Dividend Run Administration | US-12.6 | |
| F-147 | AML Monitoring & SAR Workflow | US-13.1 | |
| F-148 | Regulatory Reporting Suite | US-13.2 | |
| F-149 | Immutable Audit Log | US-13.3 | |
| F-150 | Transparent Capital Ledger | US-13.4 | |
| F-151 | Personal Impact Scorecard | US-13.5 | |
| F-152 | Data Privacy & Consent Management | US-13.6 | Consent scope shared with F-105 (US-1.5) |

**Capability gap note (resolved):** CAP-13.5 (Data Privacy & Records Management) previously had no feature ID; F-152 (Data Privacy & Consent Management, CAP-13.5) has been added to the `01_business_analysis.md` §4 catalog and US-13.6 covers it, with consent capture still anchored to F-105's scope.

## Reconciliation Notes (Draft Stories Merged or Excluded)

* **Merged duplicates:** onboarding/eKYC (3 drafts → US-1.1/US-1.2), share purchase/activation (3 drafts → US-2.1), voting (3 drafts → US-8.1), dividend estimation (3 drafts → US-7.3), round-ups (2 drafts → US-10.1/US-10.2), loan circles/pledges (2 drafts → US-6.3/US-6.4), crowdfunding/matching (2 drafts → US-9.1–US-9.3), capital ledger/impact dashboard (2 drafts → US-13.4).
* **Superseded draft concepts, not carried forward:** Sprint 2's "membership token" (replaced by the DEC-4 `PENDING_PAYMENT → ACTIVE` transition); usernames as P2P identifiers (DEC-3); `YES/NO` vote choices (DEC-1); quarterly dividends (DEC-10, replaced by the annual cycle + Dividend Estimator); "Liquid Democracy" transitive delegation (DEC-8, replaced by single-level Proxy Delegation); Sprint 1's variable membership tiers ("Founding Member" etc.) and multi-share voting weight (contradict one-member-one-vote and DEC-11); Sprint 3's $5 share (DEC-11 fixes 10,000₮).
* **Intentionally excluded distinct draft story:** Sprint 3 CAT-3 "Ethical Yield Allocation" (routing a percentage of interest yield to a community project). It maps to no canonical feature or capability, and DEC-12/DEC-14 define Round-Ups and Backing as the canonical contribution mechanisms. If the product team wants it, it requires a business-analysis change first; it must not enter the backlog silently.
* **Sprint 1's $1,000 microloan cap and specific rate figures** were draft-level details not ratified in the business analysis; loan caps and pricing are configuration under US-12.5, subject to `FINANCIAL_POLICY` governance.

*End of document.*
