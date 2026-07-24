# Product Requirements Document & Release Roadmap — Digital Coop Bank

**Document ID:** 05_prd_and_roadmap
**Status:** Final (Product Owner capstone; closes the requirements baseline)
**Upstream sources of truth:** `00_market_research.md`, `01_business_analysis.md` (P-1…P-5, CAP-1…CAP-13, F-101…F-152, DEC-1…DEC-20), `02_user_stories.md` (US-1.1…US-13.6, 60 stories, 13 epics), `03_acceptance_criteria.md` (247 scenarios; per-epic Business Rules blocks), `04_technical_architecture.md` (59 entities, ~192 endpoints, integrations, NFRs).
**Authority note:** Section 3 of this document adjudicates every rule tagged **[PROPOSED]** in `03_acceptance_criteria.md`, including the two explicitly conflicting draft pairs, and extends the canonical Decision Log as **DEC-21 … DEC-75**. Sections 4–5 fix the MoSCoW priority and sprint allocation of all 60 stories. Where this document and any upstream document disagree on priority or a previously [PROPOSED] value, **this document prevails**; all other terminology, enums, and decisions DEC-1…DEC-20 remain governed by `01_business_analysis.md` §6.

---

## 1. Executive Summary & Product Vision

### 1.1 Vision

**Digital Coop Bank is the first purely digital cooperative bank that treats member ownership as a product feature, not a legal footnote.** It occupies the intersection no incumbent covers (per `00_market_research.md` §5): the regulatory safety and full product set of a credit union, the mobile-first UX of a leading neobank, and the participatory governance and transparent treasury of the best Web3 communities — delivered inside regulated, USD, fiat banking.

Members join in minutes through fully digital eKYC onboarding, buy one 10,000₮ membership share (provisional, pending DEC-11 / legal), and immediately hold three things no neobank gives them: **a vote** (one member, one vote, from their phone, with Proxy Delegation), **a dividend** (an annual Patronage Dividend they can watch grow in real time), and **verifiable transparency** (a Transparent Capital Ledger showing exactly where the cooperative's collective funds are deployed).

### 1.2 The five differentiators (from market research), and where this PRD delivers them

| Differentiator (00 §4) | Delivered by | Roadmap phase |
| :--- | :--- | :--- |
| Embedded democratic governance with Proxy Delegation | EP-8 (US-8.1–US-8.7), EP-12 (US-12.4) | Voting Portal + archive in **MVP**; proposals, elections, delegation in Phase 2 |
| Loan Circles — community-vouched, peer-guaranteed lending | EP-6 (US-6.3, US-6.4; ROSCA US-6.5) | Core lending in **MVP**; Loan Circles Phase 2; ROSCA deferred |
| Community Funding Hub with Surplus Matching | EP-9 (US-9.1–US-9.4) | Phase 2–3 |
| Real-Time Patronage Dividend Engine & Tracker | EP-7 (US-7.1–US-7.4) | Dividend Estimator in **MVP**; full annual run Phase 2–3 |
| Transparent Capital Ledger & Impact Reporting | EP-13 (US-13.4, US-13.5), EP-9 (US-9.4) | Capital Ledger in **MVP**; Impact Scorecard Phase 3 |

### 1.3 Strategy in one paragraph

The MVP (Sprints S1–S3) must win on **neobank parity plus visible ownership**: 8-minute onboarding (KPI-1.1), instant P2P, virtual cards, savings and Round-Ups — and, from day one, a working secret-ballot Voting Portal, a live Dividend Estimator, and the Transparent Capital Ledger, because those three are the acquisition story for P-1 and P-2 and cost comparatively little. Phase 2 (S4–S5) ships the cooperative's structural moat — Loan Circles, member proposals, elections, Proxy Delegation, Group Pots, the Community Funding Hub, and the Patronage Calculation Engine — the features that raise switching costs and drive KPI-3.x/4.x. Phase 3 (S6) completes the first annual dividend cycle machinery, Surplus Matching release, and impact reporting. The Aspiration collapse (00 §2.5) is the standing caution: every ethical claim in the product must be structurally honest — hence "estimated" labeling (DEC-15), ballot-governed grant release (US-9.3), and the immutable audit spine (US-13.3) are non-negotiable from Sprint 1.

### 1.4 Success measures

The committed KPI framework is `01_business_analysis.md` §2 and is not restated in full. The roadmap below is explicitly anchored to: KPI-1.1 (median onboarding ≤ 8 min), KPI-1.3 (50k members Year 1), KPI-2.5 (NPL ≤ 1.8% Year 1), KPI-3.1 (Governance Participation Rate ≥ 40%), KPI-4.3 (dividends paid within 5 business days of AGM ratification), KPI-4.4 (≥ $1.5M community capital Year 1), and KPI-5.2 (≥ 99.9% availability for core payment/account services).

---

## 2. PRD Synthesis by Epic

Each subsection is a self-contained requirement statement a stakeholder can read without opening the other documents, with pointers into them. Conventions: features per `01` §4; stories and sizes per `02`; acceptance-criteria themes per `03` (per-epic Business Rules blocks + scenarios); API surface per `04` §3.

### EP-1 — Identity, Onboarding & KYC (CAP-1)

**Requirement.** A fully digital, resumable onboarding journey (US-1.1) that takes an applicant from first screen to KYC-approved in minutes: Persona-powered document OCR, biometric selfie/liveness match, and sanctions/PEP screening (US-1.2, DEC-5), an eligibility/common-bond check executed *before* any payment (US-1.3), MFA/biometric authentication with device binding and step-up for sensitive actions (US-1.4), and member-controlled profile, consents, and structured name/address data per DEC-6 (US-1.5).
**Features / stories:** F-101, F-102, F-104, F-105 → US-1.1–US-1.5 (sizes M/L/S/M/S).
**Acceptance-criteria themes (03 EP-1, 19 scenarios):** KPI-1.1 instrumentation timestamps mandatory; `KycStatus` state handling per DEC-19 with `PENDING_REVIEW` routed to the US-12.2 queue and `REJECTED` ending the application (never a member status); retry guidance on capture failures; ambiguous biometrics (e.g., 87% match) never auto-approve; step-up on the confirmed sensitive-action list; profile changes to KYC-relevant fields trigger re-verification.
**API surface (04 §3.1):** `/onboarding/applications*`, `/onboarding/eligibility-check`, `/onboarding/kyc/*`, `/auth/mfa/*`, `/auth/step-up`, `/auth/devices`, `/members/me*`, plus the Persona webhook (§3.14).

### EP-2 — Membership Shares & Equity (CAP-2)

**Requirement.** The equity backbone: in-flow purchase of the one mandatory 10,000₮ membership share (US-2.1, DEC-11) via Stripe card/wallet or bank transfer, activating `PENDING_PAYMENT → ACTIVE` and switching on vote/borrow/guarantee rights; server-side enforcement of the DEC-4 status machine (US-2.2); an auditable share registry producing point-in-time voting-eligibility snapshots at ballot open (US-2.3); and voluntary closure with par redemption behind a configurable rule (US-2.4, Open Item 1).
**Features / stories:** F-103, F-106, F-107 → US-2.1–US-2.4 (all M).
**AC themes (03 EP-2, 16 scenarios):** amount must equal configured par (`422 AMOUNT_MISMATCH`); payment failure keeps `PENDING_PAYMENT` with retry paths; illegal status transitions rejected everywhere; suspended members blocked from vote/borrow/guarantee with `403` and no status leakage to third parties; closure preconditions (no active/delinquent loans, no locked pledges, Group Pots resolved, balances swept).
**API surface (04 §3.2):** `/onboarding/share-purchase*`, `/members/me/membership|shares|closure-*`, admin share registry, eligibility-snapshot, and maker-checker status-transition endpoints; Stripe webhook.

### EP-3 — Savings & Deposit Accounts (CAP-3)

**Requirement.** The four DEC-13 deposit constructs: an interest-bearing Primary Savings Account auto-opened at activation with daily accrual/monthly posting (US-3.1); a Transaction Account with categorized, searchable history backing cards and payments (US-3.2); personal Savings Goals with targets and auto-transfers (US-3.3); and Group Pots — shared multi-member treasuries with invitations per DEC-3, a verifiable real-time sub-ledger (US-3.4), and m-of-n collective approval on every outbound transfer (US-3.5).
**Features / stories:** F-108–F-111 → US-3.1–US-3.5 (M/M/M/L/M).
**AC themes (03 EP-3, 21 scenarios):** rate parameters from US-12.5 config; interest history views; 1 ≤ m ≤ n threshold validation; outbound holds, approval/rejection collection, cancellation when threshold unreachable, 24 h reminder and 48 h expiry; every pot decision written to the pot ledger and audit log.
**API surface (04 §3.3):** `/accounts*`, `/transactions*`, `/savings-goals*`, `/group-pots*` including `outbound-requests` and `decision` endpoints.

### EP-4 — Payments & Transfers (CAP-4)

**Requirement.** Instant, free internal P2P addressed strictly by `PHONE | EMAIL | MEMBER_ID` with display-name confirmation (US-4.1, DEC-3); external ACH/wire/real-time-rail payments with account linking, cut-offs, returns handling, and step-up above thresholds (US-4.2); bill pay and scheduled/recurring transfers with retry policy (US-4.3); and expense splitting with one-tap payment requests (US-4.4).
**Features / stories:** F-112–F-115 → US-4.1–US-4.4 (M/L/M/M).
**AC themes (03 EP-4, 18 scenarios):** 0₮ P2P fee; settlement < 3 s; velocity/limit checks server-side from US-12.5 config; idempotency keys on all money movement; uniform recipient-lookup responses (no membership enumeration); return-code handling with member notification; anti-spam reminder throttling on payment requests.
**API surface (04 §3.4):** `/payments/recipient-lookup`, `/payments/p2p`, `/external-accounts*`, `/payments/external`, `/payees*`, `/payments/schedules*`, `/payment-requests*`; BaaS and Plaid webhooks.

### EP-5 — Card Management (CAP-5)

**Requirement.** A virtual debit card issued automatically at Transaction Account opening with step-up-gated PAN/CVV reveal and Apple Pay / Google Pay tokenization (US-5.1); optional physical card ordering, fulfilment tracking, activation, and PIN management (US-5.2); and instant card controls — freeze/unfreeze, per-period limits, channel and merchant-category toggles — enforced at authorization time (US-5.3).
**Features / stories:** F-116–F-118 → US-5.1–US-5.3 (M/M/S).
**AC themes (03 EP-5, 11 scenarios):** Lithic-hosted PAN handling (PCI scope reduction — PAN never transits the platform); embossing from verbatim `mrz_name_latin` (never a platform-generated transliteration) and DEC-6 address; authorization decisioning ≤ 200 ms including controls; frozen-card declines carry a distinct reason and notify the member; control changes audit-logged.
**API surface (04 §3.5):** `/cards*` including `credentials`, `wallet-tokens`, `physical`, `fulfilment`, `activate`, `pin`, `freeze/unfreeze`, `controls`; Lithic authorization/events webhooks.

### EP-6 — Lending & Loan Circles (CAP-6)

**Requirement.** A full digital lending suite tolerant of irregular income: in-app application with live repayment estimation and instant conditional offers (US-6.1); underwriting that weighs open-banking data (Plaid), optional bureau data, and **cooperative history** — savings, repayment record, governance participation — with itemized engagement discounts, adverse-action notices, and manual referral (US-6.2); the signature **Loan Circle** — 3–5 ACTIVE guarantors pledging savings/share capital as partial security for a tiered rate reduction, with pledge locking and pro-rata release (US-6.3, US-6.4, DEC-7); e-signature and an encrypted document vault (US-6.6); servicing with standard/seasonal/income-linked schedules, autopay, and payoff quotes (US-6.7); non-punitive arrears handling with guarantor alerts and hardship rescheduling (US-6.8); and, later, the ROSCA-style Pooled Loan Circle (US-6.5).
**Features / stories:** F-119–F-125 → US-6.1–US-6.8 (M/L/M/L/XL/M/L/M).
**AC themes (03 EP-6, 36 scenarios):** `LoanStatus` per DEC-20 throughout; pledges excluded from withdrawals/transfers/Round-Up sweeps; frictionless private invitation declines; jurisdiction flag on share-capital pledging (Open Item 2); `DELINQUENT`/`DEFAULTED` milestones; write-off admin-only under dual approval; all pricing/caps as US-12.5 configuration (adjudicated values in §3 below).
**API surface (04 §3.6):** `/loan-products`, `/loan-applications*`, `/loan-circles*`, `/pooled-circles*`, `/documents*` + signature sessions, `/loans*` (schedule, autopay, payments, payoff-quote, hardship-requests); e-sign webhook.

### EP-7 — Dividends & Surplus Distribution (CAP-7)

**Requirement.** The annual Patronage Dividend cycle per DEC-10: year-long accumulation of patronage factors and a deterministic, explainable, reconciling calculation engine (US-7.1); automated payout to savings or share reinvestment per member election within 5 business days of AGM ratification (US-7.2, KPI-4.3); a member-facing real-time Dividend Estimator showing which behaviors raise the projection (US-7.3); and annual dividend/tax statements (US-7.4).
**Features / stories:** F-126–F-129 → US-7.1–US-7.4 (L/M/M/M).
**AC themes (03 EP-7, 17 scenarios):** sum of entitlements = distributable pool (hard invariant); factor weights are FINANCIAL_POLICY-governed configuration; estimator figures labeled "estimated" (DEC-15) with scenario bands; failed postings retried and reconciled; zero-activity members get a 0₮ statement, not an error.
**API surface (04 §3.7):** `/dividends/estimate`, `/members/me/patronage-factors`, `/members/me/dividend-election`, `/dividends/allocations|statements`; admin run endpoints (create/calculate/approve/execute/reconcile) under maker-checker.

### EP-8 — Democratic Governance & Voting (CAP-8)

**Requirement.** One member, one vote, secret ballot, from the phone: browse and cast `FOR | AGAINST | ABSTAIN` votes against a ballot-open eligibility snapshot with a content-free verifiable receipt (US-8.1, DEC-1); a Proposal Builder with DEC-2 categories and co-signature gathering to threshold (US-8.2); Board Elections on the same engine (US-8.3); category-scoped, single-level, instantly revocable Proxy Delegation with direct-vote override (US-8.4, US-8.5, DEC-8); moderated proposal discussion threads locked at ballot open (US-8.6); and a permanent member-visible governance archive (US-8.7).
**Features / stories:** F-130–F-135 → US-8.1–US-8.7 (L/L/L/M/M/M/M).
**AC themes (03 EP-8, 31 scenarios):** double-vote prevention; participation and vote content physically decoupled (04 §5.1 secret-ballot protocol — no role can ever read individual choices); delegated participation counts toward the delegator's Governance Participation Rate (DEC-16); quorum failures recorded as `REJECTED / QUORUM_NOT_MET`; thread lock and audit-logged moderation.
**API surface (04 §3.8):** `/ballots*` (votes, receipts), `/proposals*` (cosignatures, comments), `/proxy-delegations*`, `/governance/archive`.

### EP-9 — Community Funding Hub (CAP-9)

**Requirement.** Crowdfunding inside the bank, per the DEC-14 noun set: structured Community Project pitches with admin review before publication (US-9.1); member Backing directly from Primary Savings with escrowed all-or-nothing refunds (US-9.2); a Surplus Matching Engine releasing up to 1:1 matches from the Community Grant pool (10% of annual surplus) **only** under certified `COMMUNITY_GRANT` ballots — never staff discretion (US-9.3); and per-project allocation and outcome reporting feeding the Transparent Capital Ledger (US-9.4).
**Features / stories:** F-136–F-139 → US-9.1–US-9.4 (M/M/L/M).
**AC themes (03 EP-9, 16 scenarios):** pitch validation; funding progress in real time; automatic halt on cap/pool exhaustion; full traceability of every matched dollar; modeled impact figures labeled "estimated".
**API surface (04 §3.9):** `/community-projects*` (backings, match-status, impact), `/members/me/backings`; admin review and grant-pool/match endpoints.

### EP-10 — Round-Up Savings (CAP-10)

**Requirement.** Per DEC-12: opt-in rounding of each settled card transaction to the nearest dollar, optional 1×/2×/3× multiplier and monthly cap, routed to exactly one of two destinations — a Savings Goal or a published Community Project (US-10.1); a capture engine that accumulates, batch-transfers at a threshold, skips gracefully on insufficient funds, and shows a running savings/impact total (US-10.2).
**Features / stories:** F-140 → US-10.1, US-10.2 (S/M).
**AC themes (03 EP-10, 8 scenarios):** whole-dollar transactions produce $0.00; idempotency-keyed batches; ledger entries link purchase and Round-Up; locked guarantee pledges excluded from sweeps.
**API surface (04 §3.10):** `/round-ups/config`, `/round-ups/activity`; capture/routing is engine behavior on Lithic settlement events.

### EP-11 — Notifications & Engagement (CAP-11)

**Requirement.** A platform notification service — push, email, SMS, in-app inbox — over a governed event catalog spanning payments, cards, Group Pots, governance deadlines, delegation, loan milestones, guarantees, dividends, and projects, every event deep-linked, new event types added by configuration (US-11.1); per-category/per-channel preferences and timezone-aware quiet hours, with regulatory/security notices exempt from suppression (US-11.2).
**Features / stories:** F-141 → US-11.1, US-11.2 (L/S).
**AC themes (03 EP-11, 7 scenarios):** channel fallback on failed push; quiet-hours deferral with digest collapse; suppression never applied to `suppressible:false` notices.
**API surface (04 §3.11):** `/notifications*`, `/notifications/preferences`, push registrations; admin event-type catalog CRUD.

### EP-12 — Admin & Back-Office (CAP-12)

**Requirement.** The P-5 operating console, with four-eyes/maker-checker on every mutation and full audit logging: a 360° member view with maker-checker status transitions (US-12.1); KYC/AML case queues with SLA timers and evidence views (US-12.2); a loan operations console for referrals, restructures, pledge administration, collections, and dual-approval write-offs (US-12.3); governance administration — ballot scheduling, quorum config, candidate slates, certification, and publication (US-12.4); a versioned, effective-dated product/fee/parameter configuration registry whose FINANCIAL_POLICY/GOVERNANCE_BYLAW-governed changes must link to a certified ballot (US-12.5); and end-to-end dividend run administration (US-12.6).
**Features / stories:** F-142–F-146 → US-12.1–US-12.6 (L/M/L/M/M/M).
**AC themes (03 EP-12, 26 scenarios):** checker ≠ maker enforced at the data layer; SLA breach visibility; adverse-action artifacts on declines; certification computes turnout and Governance Participation Rate per ballot; configuration is "the execution of democracy" — ballot links mandatory where governed.
**API surface (04 §3.12):** `/admin/members*`, `/admin/approvals*`, `/admin/cases*`, `/admin/loan-referrals` + loan decision/restructure/pledge/write-off, `/admin/proposals`, `/admin/ballots*` + certify, `/admin/config-parameters`, dividend run endpoints (§3.7).

### EP-13 — Compliance, Risk & Transparency (CAP-13)

**Requirement.** The trust spine: continuous AML monitoring across every money-movement type with SAR workflow and tipping-off safeguards (US-13.1); a configuration-driven regulatory/prudential reporting suite with KPI-2.3/2.4/2.5 breach alerts (US-13.2); a platform-wide append-only, hash-chained audit log built from inception (US-13.3); the member-facing Transparent Capital Ledger reconciling to 100% of managed funds, refreshed at least daily (US-13.4); the per-member Impact Scorecard with "estimated" labeling and methodology notes (US-13.5); and consent enforcement, retention schedules, and DSAR fulfilment within statutory deadlines (US-13.6).
**Features / stories:** F-147–F-151 (+F-105 consent scope; CAP-13.5 feature-ID gap noted in `02`) → US-13.1–US-13.6 (L/M/M/M/M/M).
**AC themes (03 EP-13, 21 scenarios):** tunable rule sets with model governance; chain verification; drill-down allocation categories; erasure as cryptographic key destruction where WORM storage prevents physical deletion; financial-records retention overrides deletion and is itemized in DSAR responses.
**API surface (04 §3.13):** admin AML rules/alerts, report runs, audit-log query; member `/capital-ledger*`, `/members/me/impact-scorecard`, `/members/me/data-requests*`; admin DSAR workflow.

---

## 3. Business Rule Adjudication (DEC-21 … DEC-75)

**Scope and method.** `03_acceptance_criteria.md` tags 50 Business-Rules-block bullets as **[PROPOSED]**; two of those bullets each carry a pair of conflicting draft values (lending base rate 8.00% vs 12.00% APR; campaign duration 30–365 vs 1–90 days), giving **52 proposed values**, plus **5 inline-flagged open decisions** listed in that document's closing "Open confirmations for the PO" note. All 55 are adjudicated below and enter the canonical Decision Log as **DEC-21…DEC-75**. Unless stated otherwise, every monetary or threshold value below is a **US-12.5 configuration seed** (never hard-coded), changeable later under FINANCIAL_POLICY/GOVERNANCE_BYLAW governance where applicable.

**Tally: 41 CONFIRMED · 13 AMENDED · 1 REJECTED.**

### 3.1 Decision table

| DEC | Epic | Proposed rule (03) | Decision | Final value | Rationale (one line) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| DEC-21 | EP-1 | ID-capture formats JPEG/PNG/PDF, max 10 MB/file | **CONFIRM** | As proposed | Matches Persona capabilities and mobile capture reality; no reason to deviate. |
| DEC-22 | EP-1 | OCR confidence ≥ 80% to auto-populate DEC-6 fields | **CONFIRM** | ≥ 80% (vendor-tunable config) | Reasonable seed; member confirms extracted fields anyway, so risk is friction, not error. |
| DEC-23 | EP-1 | Selfie match ≥ 95% + liveness → auto `APPROVED`; ambiguous → `PENDING_REVIEW` | **CONFIRM** | As proposed | Conservative auto-pass bar protects against fraud while the US-12.2 queue absorbs ambiguity. |
| DEC-24 | EP-1 | Max 3 automated verification attempts per stage → forced `PENDING_REVIEW` | **CONFIRM** | 3 attempts | Protects KPI-1.1 (stops retry loops) and routes struggling applicants to a human. |
| DEC-25 | EP-1 | Minimum applicant age 18, from OCR date of birth | **CONFIRM** | 18 years | Standard contractual-capacity floor; remains subject to statutory confirmation (Risk R-1). |
| DEC-26 | EP-1 | KYC artifacts AES-256 at rest, **TLS 1.2+** in transit, isolated bucket | **AMEND** | AES-256-GCM at rest; **TLS 1.3** in transit (TLS 1.2 minimum for third-party integrations that do not yet support 1.3) | `04` §5.1 mandates TLS 1.3; the 1.2+ floor in `03` is a doc inconsistency — align upward, with a 1.2 floor only for third parties not yet on 1.3. |
| DEC-27 | EP-1 | 3 consecutive failed step-up attempts cancel the action; full re-auth required | **CONFIRM** | 3 attempts | Standard anti-brute-force posture consistent with `423 FACTOR_LOCKED` in the API spec. |
| DEC-28 | EP-2 | Member ID: system-issued, unique, non-guessable (e.g., 8-char alphanumeric + check char) | **AMEND** | Format `DCB-` + 8 non-sequential alphanumeric characters including a check character | Adopts `04`'s `DCB-` display prefix but overrides its sequential-looking example (`DCB-000123`), which violates the non-guessable requirement; IDs must not be enumerable. |
| DEC-29 | EP-3 | Group Pot outbound approvals expire after 48 h (reminder at 24 h) | **CONFIRM** | 48 h expiry, 24 h reminder | Long enough for a volunteer group across timezones, short enough that holds don't strand funds. |
| DEC-30 | EP-3 | Savings Goal auto-transfers skip on insufficient funds with notification; never overdraft | **CONFIRM** | As proposed | Mirrors the confirmed Round-Up skip rule; consistent no-overdraft policy platform-wide. |
| DEC-31 | EP-3 | Goal target > 0₮; target date, when set, in the future | **CONFIRM** | As proposed | Basic validation; no counter-case. |
| DEC-32 | EP-3 (inline, US-3.5) | Open question: does the outbound initiator's request count as their approval? | **CONFIRM** (as scenario written) | **Yes — the initiator counts as one of the m approvals** | The group chooses m knowing this; a group wanting m independent reviewers simply sets m one higher — simpler mental model, matches the drafted scenario. |
| DEC-33 | EP-4 | Default P2P daily velocity limit 1,150,000₮/sender | **CONFIRM** | 1,150,000₮/day seed | Sensible launch AML posture; per-member exceptions and revisions live in US-12.5. |
| DEC-34 | EP-4 | Internal P2P ledger settlement SLA < 3 s | **CONFIRM** | < 3 s end-to-end | Already committed in `04` §5.2 (≤ 3 s; p95 API ≤ 500 ms). |
| DEC-35 | EP-4 | Recipient confirmation shows first name + last initial ("Member B.") | **AMEND** | Recipient confirmation shows the standard Mongolian short form = **patronymic initial + given name** (e.g. Cyrillic "Ц. Бат", Latin "Ts. Bat"); the given name (`ner`, DEC-6) is shown in full. | "First name + last initial" does not translate to the DEC-6 three-part Mongolian name model: `ner` is the identity, not a low-cardinality family name, so initialing it would either be culturally wrong or expose the whole given name — inverting this rule's own anti-fishing intent. The anti-fishing defence therefore **moves from name-masking to a per-sender recipient-lookup velocity cap**, seeded in US-12.5 with no hard-coded value (PO to confirm). That cap is a **sibling to the DEC-33 P2P daily velocity limit** (05 §3, per-sender AML posture), not a duplicate — DEC-33 rate-limits *sends*, this rate-limits *lookups* — and is complementary to the existing uniform-response enumeration protection on the recipient-lookup endpoint (03 §US-4.1 Scenario 2; 04:810). |
| DEC-36 | EP-4 | Default step-up threshold for external payments: single transfer > 550,000₮ | **CONFIRM** | > 550,000₮ seed | Reasonable friction line: routine bills pass, account-draining transfers get challenged. |
| DEC-37 | EP-4 | External account linking via micro-deposits **or** instant verification (mechanism TBD) | **AMEND** | **Plaid instant verification primary; micro-deposit fallback** for unsupported institutions | Removes the "or" ambiguity by ratifying the mechanism `04` §4.2 already specifies. |
| DEC-38 | EP-4 | Failed recurring payments retry up to 2× at 24 h intervals, then occurrence marked failed | **CONFIRM** | 2 retries / 24 h apart | Bounded, predictable retry that suits P-3's variable income timing; member notified per US-11.1. |
| DEC-39 | EP-4 (inline, US-4.4) | Payment-request reminders: max 1 per request per 24 h | **CONFIRM** | 1 reminder / request / 24 h | Anti-spam protection preserving the "without awkward reminders" story intent. |
| DEC-40 | EP-5 | Virtual card expiry 3 years from issuance | **REJECT** | No platform-side expiry rule; **defer to the issuer-processor (Lithic) default** | Card expiry is issuer-processor domain; encoding a parallel platform rule invites drift and reissuance bugs for zero member value. |
| DEC-41 | EP-5 | Control-change propagation ≤ 500 ms to the authorization path | **CONFIRM** | ≤ 500 ms engineering target (member commitment stays "seconds") | Compatible with the 200 ms authorization ceiling and synchronous Lithic control writes in `04` §4.5. |
| DEC-42 | EP-5 | Full PAN never stored/logged outside PCI-scoped issuer integration; reveal on demand, never cached | **CONFIRM** | As proposed | Matches `04` PCI scope-reduction architecture exactly; mandatory. |
| DEC-43 | EP-5 | Frozen-card declines use a distinct "card frozen" decline reason + member notification | **CONFIRM** | As proposed | Turns a confusing decline into a self-service moment; trivial cost. |
| DEC-44 | EP-5 (inline, US-5.2) | PIN denylist for trivially weak PINs | **CONFIRM** (denylist defined) | Deny: all-same-digit (e.g., 0000), ascending/descending runs (e.g., 1234, 9876), and the card's last 4 digits | Fills the flagged gap with the standard weak-PIN classes; enforced in the issuer-hosted PIN widget handshake. |
| DEC-45 | EP-6 | Launch loan bounds min 100,000₮ / **max $1,000.00** | **AMEND** | Min 100,000₮ / **max 5,700,000₮** seed | A $1,000 cap (a de-ratified Sprint 1 draft) cannot serve P-3 equipment micro-loans, the 75–85% deposit-to-loan target (KPI-2.3), or a meaningful Loan Circle proposition; 5,700,000₮ stays prudent for an unproven book. |
| DEC-46 | EP-6 | Launch term options 3, 6, or 12 months | **CONFIRM** | 3 / 6 / 12 months | Keeps launch servicing simple; longer terms can be added via FINANCIAL_POLICY once arrears data exists. |
| DEC-47 | EP-6 | Loan purpose field required, 20–500 characters | **CONFIRM** | As proposed | Supports fair-lending review and the impact-lending classification behind KPI-4.5. |
| DEC-48 | EP-6 | **CONFLICT:** base rate 8.00% APR (Sprint 1) vs 12.00% APR unsecured (Sprint 2) | **RESOLVED (AMEND)** | **12.00% APR unsecured base rate** (seed; FINANCIAL_POLICY-governed). 8.00% is *earned*, not given: reachable via Loan Circle coverage ≥ 50% (−4 pp) | Thin-file unsecured lending at 8% underprices risk and threatens KPI-2.5/2.6 (the Aspiration lesson: ethics on unsound economics fails); pricing the discount path makes community trust visibly valuable — the floor of 6.00% at ≥ 75% coverage beats the 8% draft anyway. |
| DEC-49 | EP-6 | Tiered reduction: 25–49% coverage −2 pp; 50–74% −4 pp; ≥ 75% −6 pp; floor 4.00% APR | **CONFIRM** | As proposed | Coherent with DEC-48: effective range 6.00–12.00% for circle-backed loans; floor protects sustainability. |
| DEC-50 | EP-6 | Circle invitations expire 7 calendar days if the circle hasn't formed | **CONFIRM** | 7 days | Keeps loan applications from idling; borrower can re-invite. |
| DEC-51 | EP-6 | Pledges revocable before disbursement; locked from disbursement onward | **CONFIRM** | As proposed | Guarantor consent must be real; the lock boundary at disbursement is the correct legal moment. |
| DEC-52 | EP-6 | `DELINQUENT` at first missed installment after grace (grace TBD); `DEFAULTED` at 90 days past due | **AMEND** | **Grace period 10 calendar days** (fills the TBD); `DELINQUENT` thereafter; `DEFAULTED` at 90 DPD confirmed | 10 days absorbs gig-income timing without masking real distress; 90-DPD default aligns with standard NPL definitions behind KPI-2.5. |
| DEC-53 | EP-6 | Pooled Loan Circle 3–12 participants; equal same-day monthly contributions; payout order fixed at creation | **CONFIRM** | As proposed (applies when US-6.5 is built; see §4) | 3–12 is the workable ROSCA range; DEC-7's 3–5 bound correctly applies only to guarantor circles. |
| DEC-54 | EP-6 | Missed ROSCA contribution: alert circle, retry once after 3 days, then apply configured backstop (options undefined) | **AMEND** | Alert + 3-day retry confirmed; **backstop menu defined**: (a) circle absorbs shortfall pro-rata, (b) beneficiary payout reduced by the shortfall, or (c) member removed and forfeits position to the end of the rotation — chosen at circle creation | The rule was unimplementable without enumerated backstops; three options cover the ROSCA traditions the market research cites. |
| DEC-55 | EP-7 | Estimator scenario bands: Conservative 80% / Expected 100% / High 120% of forecast surplus | **CONFIRM** | As proposed | Honest range presentation reinforcing DEC-15 "estimated" labeling. |
| DEC-56 | EP-7 | Zero-patronage members receive a 0₮ entitlement statement (not an error) | **CONFIRM** | As proposed | Every member gets an explainable statement; reinforces reconciliation invariant. |
| DEC-57 | EP-8 | Co-signature threshold: 500 signatures within a 30-day window | **AMEND** | **Greater of 25 signatures or 0.5% of ACTIVE members**, 30-day window (config seed) | A flat 500 would silence member agenda-setting until far past 50k members and kill KPI-3.3 (≥ 1 member proposal/month from Month 6); the formula scales with the cooperative. |
| DEC-58 | EP-8 | Proposal field lengths: title 10–100, summary 50–500, body 100–5,000 chars | **CONFIRM** | As proposed | Forces readable, substantive proposals without blocking depth. |
| DEC-59 | EP-8 | Author counted as sponsor; cannot co-sign own proposal | **CONFIRM** | As proposed | Prevents trivial self-inflation of the signature count. |
| DEC-60 | EP-8 | Co-signatures cannot be withdrawn once given | **CONFIRM** | As proposed | A co-signature endorses *putting the question on the agenda*, not the outcome — minds change at the ballot; also prevents threshold oscillation in the automation. |
| DEC-61 | EP-8 (inline, US-8.5) | Open question: fate of delegate-cast votes on open ballots when the delegate becomes SUSPENDED/CLOSED | **AMEND** (semantics defined) | Delegation auto-voids **prospectively**; votes the delegate already cast on open ballots **remain valid** (cast while authorized), the delegator is notified immediately and may override by direct vote before close | Retroactive voiding silently disenfranchises delegators who cannot return in time; the existing direct-vote override (DEC-8) already provides the correction path. |
| DEC-62 | EP-8 (inline, EP-8 note) | Open question: terminal status of a draft whose 30-day signature window expires below threshold | **AMEND** (status defined) | Auto-transition to `WITHDRAWN` with reason `SIGNATURE_WINDOW_EXPIRED`; author may clone into a new `DRAFT` | Keeps DEC-9 closed (no new "Archived" status), keeps the proposal board clean, and preserves the author's ability to retry. |
| DEC-63 | EP-9 | Pitch validation: title 10–100 chars; funding goal $1,000–$100,000; ≥ 1 supporting document (PDF) | **CONFIRM** | As proposed | Meaningful floor keeps the board serious; $100k ceiling matches a launch cooperative's risk appetite. |
| DEC-64 | EP-9 | **CONFLICT:** campaign duration 30–365 days (Sprint 2) vs 1–90 days (Sprint 3) | **RESOLVED (AMEND)** | **14–120 days** (config seed) | 1-day campaigns are gameable before member scrutiny; 365-day campaigns strand escrowed member Backings and go stale — 14 days matches ballot-window deliberation rhythms, 120 accommodates larger projects while bounding escrow exposure. |
| DEC-65 | EP-9 | Per-project Surplus Match cap default $500.00 until configured | **AMEND** | Default cap = **10% of the project's funding goal, capped at $10,000** (config seed) | A flat $500 cap is incoherent with goals up to $100k and the $1.5M community-capital KPI-4.4; a proportional cap scales matching with project ambition inside the 10%-of-surplus pool. |
| DEC-66 | EP-9 | Backings held in a project-specific escrow ledger until goal/deadline resolution | **CONFIRM** | As proposed | Required to make the confirmed all-or-nothing refund rule mechanically true. |
| DEC-67 | EP-10 | Round-Up batch transfer at $5.00 pending balance | **CONFIRM** | $5.00 seed | Batching reduces ledger noise; $5 keeps the feedback loop frequent enough to stay motivating. |
| DEC-68 | EP-10 | Skipped (insufficient-funds) batch retried when balance next allows; never overdraft | **CONFIRM** | As proposed | Consistent with DEC-30 and the confirmed graceful-skip rule. |
| DEC-69 | EP-11 | Failed push falls back to next enabled channel after a short retry window | **CONFIRM** | As proposed | Delivery reliability for money and governance events outweighs duplicate-channel annoyance. |
| DEC-70 | EP-11 | Quiet-hours deferrals delivered at quiet-hours end, oldest first, digest when > 5 | **CONFIRM** | As proposed | Respects members' attention without losing information; regulatory notices already exempt. |
| DEC-71 | EP-12 | Queue SLAs: KYC `PENDING_REVIEW` ≤ 24 business hours; AML alert triage ≤ 72 h | **AMEND** | KYC ≤ 24 business hours confirmed; AML triage ≤ 72 h **with HIGH-severity alerts triaged ≤ 24 h** | A single 72 h clock is too slow for sanctions-adjacent or structuring alerts; severity tiering is standard compliance practice. |
| DEC-72 | EP-12 | Pending maker-checker approvals expire after 7 days; must be re-initiated | **CONFIRM** | 7 days | Stale approvals are a control weakness; re-initiation forces fresh context. |
| DEC-73 | EP-13 | Seed AML scenario: aggregate outbound ≥ 11,400,000₮/24 h, or structuring patterns, raise an alert | **CONFIRM** | As proposed (seed only) | Correct illustrative seed pending the compliance officer's production rule set; ownership stays with compliance. |
| DEC-74 | EP-13 | DSAR fulfilment deadline seed 30 calendar days | **CONFIRM** | 30 days (config; statutory value prevails per charter) | Matches the strictest common statutory regimes; configuration absorbs charter outcome. |
| DEC-75 | EP-13 | Audit-log retention minimum 7 years for financial and governance events | **CONFIRM** | 7 years minimum (pending statutory confirmation) | Meets or exceeds common financial-records regimes; WORM storage cost is acceptable for the trust spine. |

### 3.2 The two conflict resolutions, restated for visibility

1. **Loan base rate (DEC-48): 12.00% APR unsecured, with the cooperative discount path to 6.00–8.00%.** The 8% draft is rejected as the *base*; the cooperative's promise is not cheap unsecured credit, it is *community-earned* credit: a borrower with ≥ 50% Loan Circle pledge coverage pays 8.00%, and ≥ 75% coverage pays 6.00% (floor 4.00% per DEC-49). This prices risk honestly (KPI-2.5, KPI-2.6) while making the Loan Circle differentiator financially legible in every offer screen (US-6.1 shows both rates side by side).
2. **Community Project campaign duration (DEC-64): 14–120 days.** Both drafts are rejected at their extremes: the 1-day floor (Sprint 3) permits scrutiny-free flash campaigns; the 365-day ceiling (Sprint 2) strands escrowed member savings (DEC-66) for a year. 14–120 days aligns with governance deliberation windows and bounds escrow exposure. Configurable via US-12.5.

---

## 4. MoSCoW Prioritization (all 60 stories)

**Definitions used here.** **Must** = required for the MVP launch gate at the end of Sprint S3. **Should** = committed within this 6-sprint roadmap, after MVP. **Could** = scheduled in S6 but first to trade out if capacity is short. **Won't (this roadmap)** = not scheduled within S1–S6; revisit at the next planning horizon. Effort model throughout: **S = 1, M = 2, L = 3, XL = 5** points.

**Deliberate deviations from the F-catalog priorities in `01` §4** (each is required by the dependency graph in `02` and is flagged as an input-document inconsistency in §6.3):

* **US-12.4 (F-144, catalog P2) promoted to Must** — the MVP Voting Portal (US-8.1, MVP) is inoperable without ballot scheduling, quorum configuration, and certification. MVP scope of US-12.4 is *admin-initiated* ballots; the proposal-intake queue half (which depends on US-8.2) lands with US-8.2 in Phase 2.
* **US-12.5 (F-145, catalog P2) promoted to Must** — nearly every MVP story (rates, limits, share par, underwriting parameters) consumes US-12.5 configuration seeds, and §3's adjudicated values must live in configuration, not code.
* **US-12.3 (F-143, catalog P2) promoted to Must** — MVP automated underwriting (US-6.2, MVP) mandates a manual-referral queue and adverse-action handling; launching consumer lending without a human review console is not defensible for fair-lending compliance.
* **US-2.4 (F-106, catalog MVP) demoted to Should** — voluntary self-service closure depends on US-4.2 sweep mechanics and is exercisable via the admin console (US-12.1) in the interim; it does not gate launch.

| Story | Title (short) | Size | MoSCoW | Sprint | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| US-1.1 | Onboarding journey (save/resume) | M | Must | S1 | Backlog root; KPI-1.1 instrumentation |
| US-1.2 | eKYC via Persona | L | Must | S1 | Vendor integration; split hints available |
| US-1.3 | Eligibility & common-bond check | S | Must | S1 | Before share payment |
| US-1.4 | MFA, biometrics, device binding | M | Must | S1 | Step-up policy consumed platform-wide |
| US-1.5 | Profile, consents, preferences | S | Must | S1 | DEC-6 model |
| US-2.1 | Share purchase & activation | M | Must | S1 | Stripe + activation flow F-A |
| US-2.2 | Membership status machine | M | Must | S1 | Gates vote/borrow/guarantee everywhere |
| US-2.3 | Share registry & eligibility snapshots | M | Must | S1 | Prerequisite for voting |
| US-2.4 | Voluntary closure & redemption | M | Should | S5 | Demoted (see above); Open Item 1 |
| US-3.1 | Primary Savings + interest engine | M | Must | S1 | Auto-open at ACTIVE |
| US-3.2 | Transaction Account | M | Must | S1 | Funds cards, P2P, Round-Ups |
| US-3.3 | Savings Goals | M | Must | S2 | Round-Up destination |
| US-3.4 | Group Pot creation & ledger | L | Should | S4 | P-4 anchor feature |
| US-3.5 | Group Pot m-of-n approvals | M | Should | S4 | DEC-32 initiator rule |
| US-4.1 | Instant internal P2P | M | Must | S2 | DEC-3 addressing |
| US-4.2 | External payments (ACH/wire/RTP) | L | Must | S2 | Rail-by-rail split available |
| US-4.3 | Bill pay & scheduled transfers | M | Should | S4 | DEC-38 retry policy |
| US-4.4 | Expense splitting & requests | M | Should | S4 | DEC-39 reminder cap |
| US-5.1 | Virtual card & wallet tokenization | M | Must | S2 | Auto-issue at account opening |
| US-5.2 | Physical card | M | Should | S4 | Optional plastic |
| US-5.3 | Card controls | S | Must | S2 | Freeze/limits/MCC |
| US-6.1 | Loan application & offers | M | Must | S3 | Shows standard vs circle rate |
| US-6.2 | Automated underwriting | L | Must | S3 | Ship rules-based first per split hint |
| US-6.3 | Loan Circle creation & invitations | M | Should | S4 | DEC-50 expiry |
| US-6.4 | Pledge locking, rate reduction, release | L | Should | S4 | DEC-48/49 pricing; Open Item 2 flag |
| US-6.5 | Pooled Loan Circle (ROSCA) | XL | **Won't (this roadmap)** | — | P3; XL must be split before scheduling; DEC-53/54 pre-adjudicated for when it is picked up |
| US-6.6 | E-signature & document vault | M | Must | S3 | Also serves pledge agreements later |
| US-6.7 | Servicing & flexible repayment | L | Must | S3 | DEC-52 delinquency milestones |
| US-6.8 | Arrears, guarantor alerts, hardship | M | Should | S4 | Protects KPI-2.5 |
| US-7.1 | Patronage Calculation Engine | L | Should | S5 | Factor accumulation starts at launch via config |
| US-7.2 | Dividend payout with election | M | Should | S6 | Annual cycle; needed before first AGM |
| US-7.3 | Real-Time Dividend Estimator | M | Must | S3 | MVP differentiator; interim forecast inputs allowed per `02` |
| US-7.4 | Dividend & tax statements | M | Should | S6 | Post-payout artifacts |
| US-8.1 | Voting Portal (secret ballot) | L | Must | S2 | MVP differentiator |
| US-8.2 | Proposal Builder & co-signatures | L | Should | S4 | DEC-57 threshold formula |
| US-8.3 | Board Elections | L | Should | S5 | Required before first AGM |
| US-8.4 | Proxy Delegation setup | M | Should | S5 | KPI-3.2 |
| US-8.5 | Proxy revocation & override | M | Should | S5 | DEC-61 semantics |
| US-8.6 | Proposal discussion threads | M | Should | S5 | Locks at ballot open |
| US-8.7 | Governance archive | M | Must | S3 | Backed by US-13.3 |
| US-9.1 | Project pitch & review | M | Should | S5 | DEC-63/64 validation |
| US-9.2 | Backing from savings | M | Should | S5 | DEC-66 escrow |
| US-9.3 | Surplus Matching Engine | L | Should | S6 | DEC-65 cap; ballot-governed release |
| US-9.4 | Project impact tracker | M | Could | S6 | Feeds US-13.5 |
| US-10.1 | Round-Up enrollment | S | Must | S2 | Two destinations only (DEC-12) |
| US-10.2 | Round-Up capture & routing | M | Must | S3 | DEC-67 batch threshold |
| US-11.1 | Notification delivery & catalog | L | Must | S1 | Platform service; build infra + first trigger sets, extend per epic |
| US-11.2 | Preferences & quiet hours | S | Must | S2 | DEC-70 digest rule |
| US-12.1 | Member 360° console, maker-checker | L | Must | S2 | All admin flows hang off this |
| US-12.2 | KYC/AML case queues | M | Must | S2 | DEC-71 SLAs; protects KPI-1.1/1.2 |
| US-12.3 | Loan operations console | L | Must | S3 | Promoted (see above) |
| US-12.4 | Governance administration | M | Must | S3 | Promoted; MVP scope = admin-initiated ballots |
| US-12.5 | Product & fee configuration | M | Must | S2 | Promoted; carries all §3 seeds |
| US-12.6 | Dividend run administration | M | Should | S5 | Pairs with US-7.1 |
| US-13.1 | AML monitoring & SAR workflow | L | Must | S3 | Rules-based first per split hint |
| US-13.2 | Regulatory reporting suite | M | Should | S4 | Charter-dependent definitions (Open Item 3) |
| US-13.3 | Immutable audit log | M | Must | S1 | Foundational; costliest thing to retrofit |
| US-13.4 | Transparent Capital Ledger | M | Must | S3 | MVP differentiator |
| US-13.5 | Personal Impact Scorecard | M | Could | S6 | Needs trustworthy US-13.4/9.4 data |
| US-13.6 | Privacy, consent, DSAR | M | Should | S6 | Manual DSAR handling interim (Assumption A-4) |

**Counts: Must 34 · Should 23 · Could 2 · Won't (this roadmap) 1 — total 60.**
**Effort: Must 72 pts · Should 52 pts · Could 4 pts (in-plan 128 pts) · deferred 5 pts (US-6.5).**

---

## 5. Release Roadmap — 3 Phases, 6 Sprints (S1–S6)

**Planning basis.** Effort model S=1 / M=2 / L=3 / XL=5; in-plan load 128 points over six sprints (average ≈ 21.3/sprint). Relative sprint numbering only. Dependencies follow `02`'s build-order lists; where a story depends on another story *in the same sprint*, the sprint plan sequences them and this is noted. The one documented dependency deviation is US-12.4 (see §4).

### Phase 1 — MVP (Sprints S1–S3): "Join, bank, vote, see."

All 34 Must stories. A member can join in minutes, hold the share, save, spend (card + P2P + external), take a simple loan, cast a secret ballot on admin-scheduled proposals, watch a live dividend estimate, and verify fund deployment on the Transparent Capital Ledger — on a fully audited, AML-monitored, maker-checker-operated platform. **MVP launch gate: end of S3.**

#### Sprint S1 — Foundation: identity, equity, ledger, audit spine (12 stories, 24 pts)

| Stories | Pts |
| :--- | :--- |
| US-13.3 (audit log — first, per backlog note) · US-1.1 · US-1.2 · US-1.3 · US-1.4 · US-1.5 · US-2.1 · US-2.2 · US-2.3 · US-3.1 · US-3.2 · US-11.1 (delivery infra + in-app inbox + payments/onboarding trigger set) | 2+2+3+1+2+1+2+2+2+2+2+3 = **24** |

* **Goal:** an applicant becomes an ACTIVE member end-to-end (flow F-A in `04` §1.3) with accounts open, on a hash-chained audit spine.
* **In-sprint sequencing:** US-1.1 → US-1.2/US-1.3 → US-2.1 → US-2.2/US-2.3/US-3.1/US-3.2. US-13.3 and US-11.1 are platform services built in parallel from day one.
* **Exit criteria:** Persona sandbox pass/review/fail paths drive `KycStatus` per DEC-19; 10,000₮ Stripe settlement transitions `PENDING_PAYMENT → ACTIVE` and opens both accounts; KPI-1.1 timestamps emitted; illegal DEC-4 transitions rejected; every action above appears in the tamper-evident audit log; eligibility snapshot API returns the ACTIVE set.

#### Sprint S2 — Money movement, cards, back-office core, first vote (11 stories, 22 pts)

| Stories | Pts |
| :--- | :--- |
| US-3.3 · US-4.1 · US-4.2 · US-5.1 · US-5.3 · US-8.1 · US-10.1 · US-11.2 · US-12.1 · US-12.2 · US-12.5 | 2+2+3+2+1+3+1+1+3+2+2 = **22** |

* **Goal:** members transact (P2P, external rails, card) and cast their first secret ballot; staff operate members and cases from the 360° console with configuration in place.
* **In-sprint sequencing:** US-12.1 → US-12.2 and US-12.1 → US-12.5; US-5.1/US-3.3 → US-10.1.
* **Exit criteria:** P2P settles < 3 s at 0₮ fee with DEC-33 velocity seed enforced from config; first ACH round-trip (including a return) processed against the sponsor-bank sandbox; card authorization webhook answers ≤ 200 ms with US-5.3 controls applied; a test ballot opens against an S1 eligibility snapshot, prevents double voting, and issues content-free receipts; KYC `PENDING_REVIEW` cases resolved through the queue under the DEC-71 SLA timer; all §3 configuration seeds loaded in US-12.5 with maker-checker.

#### Sprint S3 — Lending, governance operations, transparency: MVP completion (11 stories, 26 pts — peak sprint)

| Stories | Pts |
| :--- | :--- |
| US-6.1 · US-6.2 · US-6.6 · US-6.7 · US-12.3 · US-12.4 · US-8.7 · US-7.3 · US-10.2 · US-13.1 · US-13.4 | 2+3+2+3+3+2+2+2+2+3+2 = **26** |

* **Goal:** the full simple-loan lifecycle (apply → underwrite → e-sign → disburse → repay) with human referral; governance becomes operable (schedule, certify, archive); the two remaining MVP differentiators (Dividend Estimator, Transparent Capital Ledger) ship; AML monitoring goes live.
* **In-sprint sequencing (the known risk of this sprint):** US-6.1 → US-6.2 → US-6.6 → US-6.7 → US-12.3 is a chain. Mitigation per `02` INVEST hints: US-6.2 ships rules-based decisioning on cooperative history first (bureau integration can slip past MVP), US-13.1 ships rules-based monitoring first (ML scenarios later). US-12.4 is scoped to admin-initiated ballots (§4 deviation note).
* **Exit criteria (= MVP launch gate):** a loan at the DEC-45/46/48 seed parameters completes the full lifecycle including autopay retry and DEC-52 delinquency transition to a collections case; adverse-action artifact generated on decline; an admin-scheduled ballot is certified (maker-checker) with turnout and Governance Participation Rate recorded and published to the member archive; Dividend Estimator renders DEC-55 bands with "estimated" labels; Capital Ledger reconciles to 100% of managed funds with daily refresh; the DEC-73 seed AML rule raises and routes an alert; NFR spot-checks green (KPI-5.2 availability posture, §5.2 SLAs); security review of step-up surface passed.

### Phase 2 — Cooperative Moat (Sprints S4–S5): "Community credit and member agenda."

19 Should stories (43 pts). Loan Circles make credit communal; proposals, elections, delegation, and discussion make governance member-driven; Group Pots and the Funding Hub serve P-4; the dividend engine and prudential reporting stand up.

#### Sprint S4 — Loan Circles, group money, payments completion (10 stories, 23 pts)

| Stories | Pts |
| :--- | :--- |
| US-6.3 · US-6.4 · US-6.8 · US-3.4 · US-3.5 · US-4.3 · US-4.4 · US-5.2 · US-8.2 · US-13.2 | 2+3+2+3+2+2+2+2+3+2 = **23** |

* **Goal:** the Loan Circle differentiator is live end-to-end (invite → pledge → e-sign → lock → discounted rate → pro-rata release → guarantor alerts); groups pool money under m-of-n control; members set the agenda via proposals; regulators get one-click reports.
* **In-sprint sequencing:** US-6.3 → US-6.4; US-3.4 → US-3.5.
* **Exit criteria:** a circle-backed loan prices at the DEC-49 tier matching pledged coverage and releases pledges pro-rata on repayment, with the jurisdiction flag honored for share-capital pledges (Open Item 2); guarantors receive DEC-52-milestone alerts before any pledge is drawn; a Group Pot outbound executes only at m-of-n (initiator counted per DEC-32), expires per DEC-29; a proposal reaches `SUBMITTED` via the DEC-57 threshold formula and enters the US-12.4 queue (completing that story's proposal-intake scope); scheduled payment retries per DEC-38; capital-adequacy/liquidity/NPL reports generate from point-in-time snapshots.

#### Sprint S5 — Governance depth, dividend engine, Funding Hub opens (9 stories, 20 pts)

| Stories | Pts |
| :--- | :--- |
| US-8.3 · US-8.4 · US-8.5 · US-8.6 · US-7.1 · US-12.6 · US-9.1 · US-9.2 · US-2.4 | 3+2+2+2+3+2+2+2+2 = **20** |

* **Goal:** full democratic toolkit (elections, Proxy Delegation with revocation/override, deliberation threads); the patronage calculation engine and its run administration are dry-run-ready ahead of the first AGM; community projects list and take Backings; members can self-serve closure.
* **In-sprint sequencing:** US-8.4 → US-8.5; US-7.1 → US-12.6; US-9.1 → US-9.2.
* **Exit criteria:** a `BOARD_ELECTION` ballot with candidate slates certifies with choose-up-to-N enforcement; delegation is single-level-enforced, revocable, override-tested, and DEC-61 suspension semantics verified; a dividend dry run over accumulated factor data reconciles (Σ entitlements = pool) with per-member explainability; a published project accepts escrowed Backings (DEC-66) within DEC-63/64 validation; closure flow enforces all preconditions and redeems at par.

### Phase 3 — First Full Cooperative Cycle (Sprint S6): "Close the loop."

Remaining 4 Should stories + 2 Could stories (13 pts), deliberately under-loaded as the roadmap's contingency buffer and hardening window before the first AGM.

#### Sprint S6 — Dividend cycle completion, Surplus Matching, impact & privacy (6 stories, 13 pts)

| Stories | Pts |
| :--- | :--- |
| US-7.2 · US-7.4 · US-9.3 · US-13.6 · US-9.4 (Could) · US-13.5 (Could) | 2+2+3+2+2+2 = **13** |

* **Goal:** everything the first AGM needs — payout execution, statements, ballot-governed Surplus Match release — plus automated privacy operations and the impact-reporting capstone.
* **In-sprint sequencing:** US-7.2 → US-7.4; US-9.4 → US-13.5.
* **Exit criteria:** a full rehearsal dividend run executes payout per member elections with reconciliation and statements/tax artifacts (5-business-day KPI-4.3 window demonstrated at 100k-member scale per `04` §5.2); a Surplus Match releases only on a certified `COMMUNITY_GRANT` ballot and auto-halts on the DEC-65 cap; DSAR intake-to-delivery works within the DEC-74 deadline with retention overrides itemized; Impact Scorecard renders only "estimated"-labeled figures with methodology links.
* **Contingency use:** if Phase 1–2 items slip, US-9.4 and US-13.5 (Could) are traded out first, then US-13.6 falls back to the manual interim process (Assumption A-4).

### Roadmap balance summary

| Sprint | S1 | S2 | S3 | S4 | S5 | S6 | Total |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Stories | 12 | 11 | 11 | 10 | 9 | 6 | 59 (+US-6.5 deferred) |
| Points | 24 | 22 | 26 | 23 | 20 | 13 | 128 |
| Phase | 1 | 1 | 1 (MVP gate) | 2 | 2 | 3 | — |

S3 is the acknowledged peak; its mitigation is the pre-agreed slippage of the US-6.2 bureau slice and US-13.1 ML slice, and the S6 buffer absorbs downstream drift.

---

## 6. Risks, Assumptions & Open Items

### 6.1 Open items (carried from `01` §6.3 — unresolved at requirements level, owners assigned)

| ID | Item | Impact if adverse | Handling in this plan |
| :--- | :--- | :--- | :--- |
| OI-1 | **Legal/regulatory confirmation of the 10,000₮ share par value and redemption terms (DEC-11)** — counsel review against the chartering jurisdiction's cooperative/credit-union statute | Onboarding flow copy, share accounting, and US-2.4 redemption change | Par value and redemption rule are US-12.5 configuration (confirmed in 03 EP-2); no code change needed on a legal outcome. Must close **before public launch (end of S3)**. |
| OI-2 | **Guarantee-pledge enforceability (DEC-7 / F-121 / US-6.4)** — whether pledged *share capital* may legally secure another member's loan varies by jurisdiction | Loan Circle value proposition weakens to savings-only pledges in some jurisdictions | Hold mechanics implemented behind a jurisdiction flag (`422 SHARE_PLEDGE_UNAVAILABLE_IN_JURISDICTION` already specified in `04` §3.6). Must close **before S4** (Loan Circle build). |
| OI-3 | **Deposit-insurance representation** — depends on the charter obtained (credit union vs bank vs e-money/BaaS partnership) | All member-facing insurance copy, and US-13.2 report definitions | Report definitions are configuration-driven (US-13.2); a copy audit is an S3 launch-gate item. No member-facing insurance claim ships before the charter is fixed. |
| OI-4 | **KPI-4.5 (≥ 60% impact-aligned lending share) is aspirational** | Overstated ethical claims — exactly the Aspiration failure mode | Retained as aspirational only; re-baseline after Year 1 underwriting data. It must never appear in member-facing copy as a commitment; DEC-15 "estimated" labeling governs all impact figures. |

### 6.2 Key risks

| ID | Risk | Likelihood / Impact | Mitigation |
| :--- | :--- | :--- | :--- |
| R-1 | **Regulatory/charter risk:** the charter route (credit union vs bank vs BaaS partnership) shifts compliance obligations (deposit insurance wording, prudential reports, DSAR deadlines, age floor DEC-25) | Med / High | Configuration-first design (US-12.5, US-13.2, DEC-74); OI-1/OI-3 gated before launch; regulatory counsel embedded in S1–S3 reviews. |
| R-2 | **BaaS / sponsor-bank dependency:** the entire money-rail stack (FBO structure, ACH/wire/FedNow, card settlement) rides one procurement decision (`04` §4.3); onboarding lead times and sponsor compliance reviews are notoriously long | High / High | Procurement must conclude **before S2** (US-4.2); daily three-way reconciliation and degradation modes are specified; Stripe path keeps share purchase (S1) independent of the BaaS timeline; abstract contracts in `04` make substitution "an integration change, not a requirements change". |
| R-3 | **Vendor concentration & outage:** Persona, Plaid, Lithic, Stripe, e-sign — five external dependencies on the critical path | Med / Med | `04` §4 mandates graceful degradation, queued retry, reconciliation pollers, and stand-in authorization rules; Jumio documented as KYC fallback (DEC-5). |
| R-4 | **S3 scope peak (26 pts) on the lending chain** US-6.1→6.2→6.6→6.7→12.3 | Med / Med | Pre-agreed slip lanes (bureau slice, ML monitoring slice); S6 buffer; MVP gate criteria written against the rules-based paths. |
| R-5 | **Governance cold start:** KPI-3.1 (≥ 40% participation) fails if early ballots are dull or scarce; conversely DEC-57's low threshold could flood the S4+ agenda | Med / Med | US-12.4 admin-initiated ballots from S3 create a voting habit before proposals open; threshold is a config seed tunable by observed volume; discussion threads (S5) deepen engagement. |
| R-6 | **Peer-guarantee credit risk:** Loan Circle pricing (DEC-48/49) is unproven; guarantor losses would poison the community-trust flywheel | Med / High | Conservative launch caps (DEC-45), guarantor exposure dashboards, DEC-52 early-warning milestones before any pledge draw, NPL breach alerts (US-13.2), Year-1 pricing review under FINANCIAL_POLICY governance. |
| R-7 | **Ethical-claims integrity (Aspiration lesson):** any unverifiable impact claim is an existential brand risk | Low / High | DEC-15 labeling enforced in acceptance criteria; Capital Ledger reconciles to 100%; Impact Scorecard ships last (S6), only on trustworthy data. |
| R-8 | **First-AGM hard deadline:** US-7.1/7.2/12.6/8.3 must all be production-ready before the first AGM, whose date is set by bylaws, not by sprint velocity | Med / High | Dividend engine dry-runs in S5, full rehearsal in S6; if the AGM date lands early, S6 scope trades out Could items first. |

### 6.3 Inconsistencies found between the input documents (resolved here, to be folded into the next baseline revision)

1. **TLS floor:** `03` EP-1 proposed TLS 1.2+; `04` §5.1 mandates TLS 1.3 everywhere → resolved upward by DEC-26.
2. **Member ID format:** `03` EP-2 requires non-guessable IDs; `04`'s example `DCB-000123` is sequential-looking → resolved by DEC-28 (prefix kept, enumeration forbidden).
3. **Feature-priority vs dependency-graph conflicts:** F-130/F-135 (MVP) depend operationally on US-12.4 (F-144, P2); MVP stories consume US-12.5 (F-145, P2) seeds; US-6.2 (MVP) requires the US-12.3 (F-143, P2) referral console → resolved by the three Must promotions in §4.
4. **US-12.4's build dependency on US-8.2** conflicts with the MVP need for admin-initiated ballots → resolved by scoping US-12.4 in S3 to admin-initiated ballots, completing proposal intake with US-8.2 in S4.
5. **US-2.4 marked MVP via F-106** but blocked on US-4.2 sweeps and non-essential for launch → demoted to Should (S5), with admin-executed closure as interim.
6. **Loan cap re-introduction:** `02`'s reconciliation notes de-ratified Sprint 1's $1,000 cap, yet `03` EP-6 re-proposed it as a seed → adjudicated to 5,700,000₮ (DEC-45).
7. **CAP-13.5 feature-ID gap:** `02` flags that Data Privacy & Records Management has no feature ID (US-13.6 anchors to F-105) → adopt the recommended **F-152** in the next `01` revision.
8. **E-signature vendor unnamed** ("Dropbox Sign or DocuSign class") while all other integrations are named vendors → procurement to name one before S3 (US-6.6); treated as procurement, not a requirements gap.

### 6.4 Assumptions

* **A-1:** Sprint capacity supports ≈ 21–26 points as sized; the S/M/L/XL → 1/2/3/5 mapping is the agreed planning currency.
* **A-2:** Sponsor-bank/BaaS and e-signature procurement conclude in time for S2 and S3 respectively (see R-2).
* **A-3:** The first AGM occurs after S6; the S5 dry run + S6 rehearsal sequence therefore precedes any live dividend obligation (see R-8).
* **A-4:** Until US-13.6 ships (S6), DSAR volume at early member counts is low enough for manual fulfilment within the DEC-74 deadline, supported by the audit log and member 360° view.
* **A-5:** All quantitative KPI targets remain management estimates per `01` §2, not market facts.

---

## 7. Document Map — How the Six Final-Requirements Documents Relate

```
00_market_research.md ────────────► WHY: market, competitors, 5 differentiators
        │  grounds vision & positioning
        ▼
01_business_analysis.md ──────────► WHAT & WHO: personas P-1..P-5, KPIs,
        │                            capabilities CAP-1..13, features F-101..151,
        │                            Canonical Glossary + DEC-1..DEC-20 (normative)
        ▼
02_user_stories.md ───────────────► WHAT, buildable: 60 stories US-x.y in 13 epics
        │                            (EP-1..EP-13), sizes, dependencies,
        │                            feature→story coverage
        ▼
03_acceptance_criteria.md ────────► WHEN IT'S DONE: 247 scenarios, per-epic
        │                            Business Rules ([CONFIRMED]/[PROPOSED]/Superseded)
        ▼
04_technical_architecture.md ─────► HOW: 59 entities, ~192 endpoints, services S-1..S-13,
        │                            integrations, NFRs, story→endpoint traceability
        ▼
05_prd_and_roadmap.md (this doc) ─► DECIDE & SEQUENCE: PRD synthesis, rule
                                     adjudication DEC-21..DEC-75, MoSCoW for all 60
                                     stories, Phases 1–3 across Sprints S1–S6,
                                     risks & open items
```

**Reading rules.**

* **Terminology and enums:** `01` §6 is normative for DEC-1…DEC-20; this document is normative for DEC-21…DEC-75. No other document may redefine a term or value.
* **Traceability chain:** differentiator (00) → capability/feature (01) → story (02) → scenarios & rules (03) → entities/endpoints/NFRs (04) → priority, adjudicated values, and sprint (05). Every link is by stable ID (CAP-n, F-1xx, US-x.y, DEC-n, E-n, EP-n, S1–S6).
* **Conflict precedence:** for priority, sequencing, and previously [PROPOSED] values — this document; for everything else — `01`, then the specialist document closest to the topic. The sprint_1–sprint_3 drafts remain superseded in full.
* **Next baseline revision actions recorded here:** add F-152 (CAP-13.5), fold DEC-21…DEC-75 into the canonical Decision Log, update F-143/F-144/F-145 to MVP and F-106's closure scope to P2, and correct the TLS floor and Member ID example (§6.3).

---

*End of document. With this file the final_requirements baseline (00–05) is complete: vision, scope, stories, acceptance criteria, architecture, and now decision, priority, and sequence.*
