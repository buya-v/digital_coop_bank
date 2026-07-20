# Business Analysis & Functional Scope — Digital Coop Bank

**Document ID:** 01_business_analysis
**Status:** Final (consolidated from Sprints 1–3 business analyst outputs)
**Scope:** Canonical target personas, reconciled business objectives and KPIs, the full-vision domain capability map, the feature catalog with stable IDs, and the **Canonical Glossary & Decision Log** that all downstream documents (user stories, API specs, data models, test plans) MUST reuse verbatim.

> **Authority note:** Where the three sprint documents conflicted (terminology, enums, targets), this document adjudicates the conflict. The decision and its rationale are recorded in Section 6. Downstream artifacts must not reintroduce superseded terms.

---

## 1. Target User Personas

The three sprints produced overlapping persona sets (four, three, and four personas respectively, some with placeholder names). They are merged here into **five canonical personas with stable IDs**. Placeholder personal names from the sprint docs are retired; personas are referenced by ID and role label only.

### P-1 — The Values-Driven Saver (Ethical Consumer)

*Merges: Sprint 1 "Values-Aligned Consumer", Sprint 2 "Ethical Consumer", Sprint 3 Persona A.*

* **Demographics:** Age 22–35; urban professional (e.g., marketing, software, creative fields); income approx. $55k–$90k/year (estimate); digitally fluent.
* **Needs & Goals:**
  * Full transparency on how deposits are deployed (green energy, social housing, local business, fair trade).
  * Divestment from banks that fund fossil fuels or predatory lending.
  * A democratic voice in how the institution operates — valued at least as highly as personal yield.
  * A premium mobile experience on par with leading neobanks.
* **Behaviors:** Researches corporate ethics and ESG ratings before choosing services; reads transparency disclosures; active in sustainability-focused social communities; shares brand affiliations that match personal ethics; shops local; prefers contactless/digital payments and clean dashboards.
* **Pain Points:** Cannot verify incumbent banks' ethical claims; ethical credit unions have outdated apps and branch-based processes; neobanks pass profits to venture capital, not members or communities.
* **Platform Fit:** Transparent Capital Ledger, impact scorecards, Round-Up contributions to community projects, proposal voting on lending policy.

### P-2 — The Digital-Native Member (Neobank Devotee)

*Merges: Sprint 1 "Gen Z Tech Enthusiast", Sprint 3 Persona B.*

* **Demographics:** Age 18–30; student, early-career tech worker, or part-time content creator; mobile-only banking behavior.
* **Needs & Goals:**
  * 100% digital, mobile-first experience — zero branch visits, zero paper.
  * Instant onboarding, instant P2P payments, real-time notifications, and clean data visualizations.
  * Gamified micro-savings (round-ups, goals), social payment features, modern security (biometrics, tokenization), zero hidden fees.
  * A sense of belonging — banking as a community asset, not a utility.
* **Behaviors:** Existing Monzo/Revolut-class app user; pays via digital wallets; learns finance through social media; responds to micro-interactions and dark-mode design; **abandons onboarding that exceeds ~10 minutes or requires manual document handling** (this behavior anchors the onboarding KPI — see Section 2, Objective 1).
* **Pain Points:** Impersonal legacy banking apps; negligible interest on static savings; no ownership stake or voice anywhere they bank.
* **Platform Fit:** Instant eKYC onboarding, P2P transfers and expense splitting, virtual cards, Round-Up savings, real-time dividend tracker, in-app voting as engagement.

### P-3 — The Flexible Earner (Gig Worker / Freelancer / Micro-Entrepreneur)

*Merges: Sprint 1 "Gig Economy Worker", Sprint 2 "Gig Worker & Small Entrepreneur", Sprint 3 Persona D.*

* **Demographics:** Age 25–45; independent contractor, freelancer, gig platform worker, or small independent producer (e.g., organic farmer); variable income approx. $35k–$60k/year (estimate); urban to rural-fringe.
* **Needs & Goals:**
  * Financial products tolerant of fluctuating monthly income; no punitive fees on volatile balances.
  * Access to fair consumer credit and business/equipment micro-loans **without** standard payroll-income verification.
  * Flexible repayment schedules matched to seasonal/non-linear income.
  * Community-based guarantees to offset thin or non-traditional credit files; dividends as a return on patronage.
* **Behaviors:** Manages multiple erratic income streams from several clients/platforms; runs business and personal finances from mobile apps; relies on peer networks and community reputation; participates in local/regional cooperative networks.
* **Pain Points:** Algorithmic credit scoring rejects irregular income and ignores community trust; high fees; no employer benefits; loan paperwork burdens; cannot attend physical AGMs.
* **Platform Fit:** Loan Circles (peer-guaranteed credit), ROSCA-style pooled circles, flexible loan servicing, contribution-based share/dividend growth, remote voting.

### P-4 — The Community Organizer (Cooperative Leader / Group Treasurer)

*Merges: Sprint 1 "Co-op Leader", Sprint 2 "Grassroots Organizer", Sprint 3 Persona C.*

* **Demographics:** Age 30–60; executive director of a food co-op, neighborhood non-profit director, housing cooperative treasurer, or community housing advocate; income approx. $45k–$70k/year (estimate).
* **Needs & Goals:**
  * A secure, low-fee vehicle to pool, track, and manage a group's collective treasury with shared oversight and verifiable ledgers.
  * Streamlined digital distribution of surpluses/dividends to group members (replacing manual accounting).
  * Accessible democratic governance tools that raise voter turnout; a transparent channel to raise community capital for local projects (gardens, community centers, housing).
  * Credit that leverages peer responsibility instead of heavy collateral.
* **Behaviors:** Manages shared budgets and group communications; coordinates volunteers and town halls; seeks consensus-based financial operations; acts as trusted liaison between members and institutions.
* **Pain Points:** Commercial accounts are expensive; banks demand heavy collateral and covenants for small community loans; paper governance depresses turnout; crowdfunding through traditional rails is slow and administratively heavy.
* **Platform Fit:** Group Pots with collective approval, Proposal Builder and voting portal, Community Funding Hub with surplus matching, automated dividend distribution.

### P-5 — The Cooperative Operations Administrator (Internal / Back-Office)

*New in consolidation. The sprint capability maps and compliance features imply an internal operator persona that no sprint made explicit; it is required to anchor the Admin/Back-Office and Compliance capabilities.*

* **Demographics:** Bank staff role, not a member segment: membership officer, KYC/AML analyst, loan operations officer, governance secretary, or compliance officer.
* **Needs & Goals:**
  * Work queues for KYC escalations, AML alerts, loan reviews, and disputed transactions.
  * Tools to configure products (rates, fees, share price), schedule ballots and elections, certify results, and administer the dividend run.
  * Complete audit trails and one-click regulatory reporting.
* **Behaviors:** Works from a secure web back-office console; operates under four-eyes/maker-checker controls; responds to regulator and auditor requests.
* **Pain Points (status quo):** Swivel-chair operations across disconnected systems; manual report assembly; no unified member timeline.
* **Platform Fit:** Admin console (CAP-12), compliance and reporting suite (CAP-13), governance administration (CAP-8.6).

### Persona ↔ Sprint Mapping (for traceability)

| Canonical ID | Sprint 1 | Sprint 2 | Sprint 3 |
| :--- | :--- | :--- | :--- |
| P-1 | Persona A (ethical consumer) | Persona 1 (ethical consumer) | Persona A |
| P-2 | Persona D (Gen Z digital native) | — | Persona B |
| P-3 | Persona B (gig worker) | Persona 2 (gig worker/entrepreneur) | Persona D |
| P-4 | Persona C (co-op leader) | Persona 3 (grassroots organizer) | Persona C |
| P-5 | — (implied) | — (implied) | — (implied) |

---

## 2. Business Objectives & KPIs (Reconciled)

The three sprints proposed overlapping and partly contradictory targets. The set below is a single, mutually consistent framework. **All monetary values are USD. All targets are management estimates, not market facts.** Where sprints conflicted, the adjudication is noted inline and logged in Section 6.

### Objective 1 — Frictionless, Compliant Member Acquisition

| KPI ID | KPI | Target | Frequency | Reconciliation Note |
| :--- | :--- | :--- | :--- | :--- |
| KPI-1.1 | **Median onboarding time** (app download → KYC approved → membership share purchased → account open) | **≤ 8 minutes median; ≤ 10 minutes at the 90th percentile** | Real-time | Sprints 1–2 said "< 5 min", Sprint 3 said "< 8 min", and Persona P-2 abandons at > 10 min. Decision: **8 min median** is the committed KPI (coherent with the 10-minute abandonment ceiling); 5 minutes is retained only as a stretch goal, not a commitment. |
| KPI-1.2 | Onboarding completion rate (started → member ACTIVE) | ≥ 85% | Monthly | Sprint 2 figure, uncontested. |
| KPI-1.3 | Total active members (KYC-complete, ≥ 3 transactions/month) | **50,000 by end of Year 1; 100,000 by Month 18** | Monthly | Sprint 1 (50k @ Y1) and Sprint 3 (100k @ 18 months) combined into one trajectory. |
| KPI-1.4 | Cost per acquisition (CPA) | ≤ $25 | Monthly | Sprint 2 figure; relies on referral loops through Loan Circles and community projects. |

### Objective 2 — Deposit Growth & Financial Sustainability

| KPI ID | KPI | Target | Frequency | Reconciliation Note |
| :--- | :--- | :--- | :--- | :--- |
| KPI-2.1 | Total assets under management (deposits + share capital) | **$25M by end of Year 1; $150M by end of Year 2** | Monthly | Sprint 1 (Y1) and Sprint 3 (Y2) combined into one trajectory. |
| KPI-2.2 | Average deposit balance per active member | ≥ $1,500 by end of Year 2 | Quarterly | Sprint 3 figure; consistent with KPI-2.1 ÷ KPI-1.3. |
| KPI-2.3 | Deposit-to-loan ratio | 75%–85% | Monthly | Sprint 2 figure, uncontested. |
| KPI-2.4 | Capital adequacy ratio | > 10% | Quarterly | Sprint 2 figure, uncontested. |
| KPI-2.5 | Non-performing loan (NPL) rate | **≤ 1.8% in Year 1; ≤ 1.5% from Year 2**, leveraging peer-guarantee models | Monthly | Sprint 2 said < 1.8%, Sprint 3 said < 1.5%; reconciled as a maturing target. |
| KPI-2.6 | Financial break-even | Within 18 months of launch | Quarterly | Sprint 1 figure, uncontested. |

### Objective 3 — Democratic Governance Engagement

| KPI ID | KPI | Target | Frequency | Reconciliation Note |
| :--- | :--- | :--- | :--- | :--- |
| KPI-3.1 | **Governance participation rate** (eligible members casting or delegating a vote per ballot) | **≥ 40% in Year 1; ≥ 45% steady state** | Per ballot | Sprints 1–2 said > 45%, Sprint 3 said ≥ 40%; reconciled as a ramp. Both far exceed the sub-5% turnout typical of traditional credit union AGMs (industry-cited estimate). |
| KPI-3.2 | Proxy Delegation adoption (members with ≥ 1 active delegation) | ≥ 20% | Quarterly | Sprint 2 figure, uncontested. |
| KPI-3.3 | Proposal throughput | ≥ 1 member-initiated proposal reaching ballot per month from Month 6 | Monthly | New consolidated KPI; makes CAP-8 measurable. |

### Objective 4 — Community Wealth & Impact

| KPI ID | KPI | Target | Frequency | Reconciliation Note |
| :--- | :--- | :--- | :--- | :--- |
| KPI-4.1 | Surplus redistribution rate (share of annual net surplus returned as Patronage Dividends) | ≥ 60% | Annual | Sprint 2 figure, uncontested. |
| KPI-4.2 | Community surplus matching allocation | 10% of annual surplus reserved for Community Grant matching | Annual | Sprint 3 figure; consistent with KPI-4.1 (60% dividends + 10% community + remainder to reserves). |
| KPI-4.3 | Dividend payout timeliness | 100% of approved Patronage Dividends distributed within **5 business days** of the AGM ratifying the annual accounts | Annual | Sprint 3 figure, uncontested; anchored to the annual dividend cycle decided in DEC-10. |
| KPI-4.4 | Community capital facilitated (member backing + matching through the Community Funding Hub, plus peer-guaranteed community loans) | ≥ $1.5M in Year 1 | Quarterly | Sprint 2 figure, uncontested. |
| KPI-4.5 | Impact-aligned lending share (loan portfolio in community/green categories) | ≥ 60% of loan book value — **aspirational, review after Year 1** | Quarterly | Sprint 1 figure; retained but flagged aspirational pending underwriting reality. |

### Objective 5 — Experience Quality

| KPI ID | KPI | Target | Frequency | Reconciliation Note |
| :--- | :--- | :--- | :--- | :--- |
| KPI-5.1 | Net Promoter Score (NPS) | **≥ 65 in Year 1; ≥ 75 aspirational from Year 2** | Semi-annual | Sprint 1 said > 65, Sprint 3 said > 75; reconciled as a ramp. |
| KPI-5.2 | App availability | ≥ 99.9% monthly for core payment and account services | Monthly | New consolidated KPI implied by neobank-parity positioning. |

---

## 3. Domain Capability Map

One consolidated hierarchy with **stable IDs (CAP-n / CAP-n.m)** covering the full vision. Sprint-level domain acronyms (MIAM, CASL, CTP, EDG, CLTN, DDE, TCL, MIM, CAT, DGV, PSL, CIF, DMA) are **retired**; use CAP IDs only.

```
Digital Coop Bank — Capability Map
│
├── CAP-1  Identity, Onboarding & KYC
│   ├── CAP-1.1  Digital Onboarding Journey (application, progress save/resume)
│   ├── CAP-1.2  eKYC & Identity Verification (document OCR, biometric selfie match — vendor: Persona; see DEC-5)
│   ├── CAP-1.3  AML / Sanctions / PEP Screening (onboarding-time)
│   ├── CAP-1.4  Membership Eligibility & Common-Bond Validation
│   ├── CAP-1.5  Authentication & Security (MFA, biometrics, device binding, session management)
│   └── CAP-1.6  Profile, Consent & Preference Management
│
├── CAP-2  Membership Shares & Equity
│   ├── CAP-2.1  Membership Share Account (non-withdrawable equity; one initial share at $25 par — see DEC-11)
│   ├── CAP-2.2  Share Purchase & Redemption Processing
│   ├── CAP-2.3  Membership Lifecycle Management (status machine — see DEC-4)
│   └── CAP-2.4  Share Registry & Voting-Eligibility Determination
│
├── CAP-3  Savings & Deposit Accounts
│   ├── CAP-3.1  Primary Savings Account (withdrawable, interest-bearing)
│   ├── CAP-3.2  Transaction (Checking) Account
│   ├── CAP-3.3  Savings Goals (personal sub-account "pots")
│   ├── CAP-3.4  Group Pots (shared multi-member accounts with collective approval rules)
│   └── CAP-3.5  Interest Accrual & Posting Engine
│
├── CAP-4  Payments & Transfers
│   ├── CAP-4.1  Internal P2P Transfers (instant, free; recipient identifiers per DEC-3)
│   ├── CAP-4.2  External Payments (ACH, wire; real-time rails: FedNow / SEPA Instant as available)
│   ├── CAP-4.3  Bill Pay & Recurring / Scheduled Transfers
│   └── CAP-4.4  Expense Splitting & Payment Requests
│
├── CAP-5  Card Management
│   ├── CAP-5.1  Virtual Debit Card Issuance
│   ├── CAP-5.2  Physical Debit Card Issuance & Fulfilment
│   ├── CAP-5.3  Card Controls (freeze/unfreeze, limits, merchant-category blocks)
│   └── CAP-5.4  Wallet Tokenization (Apple Pay / Google Pay)
│
├── CAP-6  Lending (incl. Social / Peer-Guaranteed Lending)
│   ├── CAP-6.1  Loan Origination (application, product selection, offers)
│   ├── CAP-6.2  Underwriting & Credit Decisioning (open-banking data, bureau data, cooperative history)
│   ├── CAP-6.3  Loan Circles — Peer Guarantees (3–5 vouching members; pledge of savings/share capital; rate reduction — see DEC-7)
│   ├── CAP-6.4  Pooled Loan Circles (ROSCA-style rotating pool variant)
│   ├── CAP-6.5  E-Signature & Loan Document Vault
│   ├── CAP-6.6  Loan Servicing (disbursement, repayment scheduling, flexible/seasonal schedules, direct debit)
│   └── CAP-6.7  Arrears Management & Collections Monitoring
│
├── CAP-7  Dividends & Surplus Distribution
│   ├── CAP-7.1  Cooperative Surplus Tracking
│   ├── CAP-7.2  Patronage Calculation Engine (per-member entitlement from savings, transactions, loan repayment, participation — see DEC-10)
│   ├── CAP-7.3  Dividend Payout Processing (to savings account or share reinvestment)
│   ├── CAP-7.4  Real-Time Dividend Estimator (member-facing projection)
│   └── CAP-7.5  Dividend & Tax Statement Generation
│
├── CAP-8  Democratic Governance & Voting
│   ├── CAP-8.1  Proposal Management (draft, co-signature gathering, submission, categories per DEC-2, status per DEC-9)
│   ├── CAP-8.2  Voting Engine (one member, one vote; secret ballot; choices per DEC-1)
│   ├── CAP-8.3  Board Elections (candidate slates, election ballots, term management)
│   ├── CAP-8.4  Proxy Delegation (category-scoped, instantly revocable delegation — see DEC-8)
│   ├── CAP-8.5  Deliberation Spaces (proposal discussion threads, comments, moderation)
│   └── CAP-8.6  Governance Records & Audit Trail (results certification, archives, minutes)
│
├── CAP-9  Community Funding & Crowdfunding
│   ├── CAP-9.1  Project Pitch Board (listing and review of community projects)
│   ├── CAP-9.2  Member Backing & Co-Investment (contributions from savings)
│   ├── CAP-9.3  Surplus Matching Engine (up to 1:1 match from the Community Grant pool)
│   └── CAP-9.4  Project Allocation & Impact Tracking (per-project fund use and outcomes)
│
├── CAP-10 Round-Up Savings & Micro-Contributions
│   ├── CAP-10.1 Round-Up Capture Engine (round card transactions to nearest dollar)
│   └── CAP-10.2 Round-Up Destination Routing (member's Savings Goal or a chosen community project)
│
├── CAP-11 Notifications & Engagement
│   ├── CAP-11.1 Notification Delivery (push, email, SMS, in-app inbox)
│   ├── CAP-11.2 Event Catalog & Triggers (payments, governance deadlines, dividend events, loan milestones)
│   └── CAP-11.3 Notification Preferences & Quiet Hours
│
├── CAP-12 Admin & Back-Office
│   ├── CAP-12.1 Member Management Console (360° member view, status changes with maker-checker)
│   ├── CAP-12.2 KYC / AML Case Management (manual review queues, escalations)
│   ├── CAP-12.3 Loan Operations Console (manual underwriting review, restructuring, write-offs)
│   ├── CAP-12.4 Governance Administration (ballot scheduling, quorum config, results certification)
│   ├── CAP-12.5 Product & Fee Configuration (rates, fees, share price, limits)
│   └── CAP-12.6 Dividend Run Administration (surplus input, calculation approval, payout execution)
│
└── CAP-13 Compliance, Risk & Reporting
    ├── CAP-13.1 Ongoing AML Transaction Monitoring & Suspicious Activity Reporting
    ├── CAP-13.2 Regulatory & Prudential Reporting (capital adequacy, liquidity, lending reports)
    ├── CAP-13.3 Immutable Audit Logging (financial, governance, and admin actions)
    ├── CAP-13.4 Transparent Capital Ledger (member-facing fund-allocation and impact reporting)
    └── CAP-13.5 Data Privacy & Records Management (consent, retention, subject-access requests)
```

---

## 4. Feature List

Stable feature IDs **F-101 …** in one continuous series, grouped by capability. Priorities: **MVP** (launch), **P2** (fast-follow), **P3** (later horizon). Persona references use the canonical IDs from Section 1.

### Identity, Onboarding & KYC (CAP-1) and Membership Shares (CAP-2)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-101 | Instant Digital Onboarding & eKYC | CAP-1.1, CAP-1.2, CAP-1.3 | P-1, P-2, P-3 | Mobile application flow with document capture (OCR), biometric selfie match, and automated sanctions/PEP screening via the Persona verification service; save-and-resume; manual-review fallback routed to CAP-12.2. Target: median ≤ 8 minutes end-to-end (KPI-1.1). | MVP |
| F-102 | Eligibility & Common-Bond Check | CAP-1.4 | P-1, P-2, P-3, P-4 | Automated validation of membership eligibility criteria during onboarding, before share purchase. | MVP |
| F-103 | Initial Membership Share Purchase | CAP-2.1, CAP-2.2 | P-1, P-2, P-3, P-4 | In-flow purchase of the one mandatory membership share ($25 par value, DEC-11) via card or bank transfer; on settlement the member transitions PENDING_PAYMENT → ACTIVE and voting rights activate. | MVP |
| F-104 | Multi-Factor Authentication & Biometrics | CAP-1.5 | All | MFA at enrollment and step-up for sensitive actions; device biometrics; device binding. | MVP |
| F-105 | Member Profile & Consents | CAP-1.6 | All | View/edit contact details (ovog/etsgiin ner/ner + structured address per DEC-6), membership status, join date, consents, and communication preferences. | MVP |
| F-106 | Membership Lifecycle Management | CAP-2.3 | P-5 | Enforcement of the canonical membership status machine (DEC-4) with member-visible status and admin-controlled transitions (suspend, close) under maker-checker. | MVP |
| F-107 | Share Registry & Voting Eligibility | CAP-2.4 | P-4, P-5 | Authoritative registry of shares held per member; drives one-member-one-vote eligibility snapshots per ballot. | MVP |

### Savings & Deposits (CAP-3)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-108 | Primary Savings Account | CAP-3.1, CAP-3.5 | All members | Interest-bearing withdrawable savings opened automatically at activation; daily accrual, monthly posting. | MVP |
| F-109 | Transaction (Checking) Account | CAP-3.2 | P-2, P-3 | Day-to-day spending account backing cards and payments; transaction categorization. | MVP |
| F-110 | Savings Goals | CAP-3.3 | P-2, P-1 | Named personal sub-account pots with targets, progress visuals, and automated recurring transfers. | MVP |
| F-111 | Group Pots | CAP-3.4 | P-4 | Shared multi-member pots with sub-ledgers and configurable collective approval (m-of-n) for outbound transactions; verifiable ledger visible to all pot members. | P2 |

### Payments & Cards (CAP-4, CAP-5)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-112 | Instant Internal P2P Transfer | CAP-4.1 | P-2, P-3 | Instant, free member-to-member transfer addressed by phone number, email, or Member ID (DEC-3); confirmation of recipient display name before send. | MVP |
| F-113 | External Payments (ACH / Wire / Real-Time Rails) | CAP-4.2 | P-3, P-4 | Inbound/outbound external transfers with same-day and real-time options where rails permit. | MVP |
| F-114 | Bill Pay & Scheduled Transfers | CAP-4.3 | P-3, P-4 | Recurring and future-dated payments with failure retry and notifications. | P2 |
| F-115 | Expense Splitting & Payment Requests | CAP-4.4 | P-2 | Split a transaction among members; send payment requests resolved via F-112. | P2 |
| F-116 | Virtual Debit Card | CAP-5.1, CAP-5.4 | P-2, P-3 | Instant virtual card at account opening; wallet tokenization (Apple Pay / Google Pay). | MVP |
| F-117 | Physical Debit Card | CAP-5.2 | P-3, P-4 | Optional physical card with in-app activation and PIN management. | P2 |
| F-118 | Card Controls | CAP-5.3 | P-2 | Instant freeze/unfreeze, spending limits, online/ATM/merchant-category toggles. | MVP |

### Lending (CAP-6)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-119 | Digital Loan Application & Offers | CAP-6.1 | P-3 | In-app application for personal and micro-business loans; product selection, affordability inputs, instant conditional offers. | MVP |
| F-120 | Automated Underwriting Engine | CAP-6.2 | P-3, P-5 | Decisioning that combines open-banking transaction analysis, optional bureau data, and cooperative history (savings, repayment, participation); manual-review queue for edge cases (CAP-12.3). | MVP |
| F-121 | Loan Circles (Peer Guarantees) | CAP-6.3 | P-3, P-4 | Borrower invites 3–5 ACTIVE members to vouch; guarantors pledge a portion of savings or share capital as partial security, reducing the borrower's rate; pledges are locked for the loan term and released pro-rata on repayment (terminology per DEC-7). | P2 |
| F-122 | Pooled Loan Circles (ROSCA) | CAP-6.4 | P-3, P-4 | Rotating pool: circle members contribute a fixed monthly amount and take turns receiving the lump sum; schedule and order agreed at circle creation. | P3 |
| F-123 | E-Signature & Document Vault | CAP-6.5 | P-3 | Legally compliant e-signing of loan agreements; encrypted storage of agreements and collateral documents. | MVP |
| F-124 | Loan Servicing & Flexible Repayment | CAP-6.6 | P-3 | Disbursement to the member's account; repayment schedules including seasonal/income-linked plans; autopay via direct debit; payoff quotes. | MVP |
| F-125 | Arrears Monitoring & Alerts | CAP-6.7 | P-3, P-5 | Early-warning notifications to borrowers and guarantors; hardship rescheduling workflow; collections case queue. | P2 |

### Dividends & Surplus (CAP-7)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-126 | Patronage Calculation Engine | CAP-7.1, CAP-7.2 | P-5 | Computes each member's annual Patronage Dividend from the ratified surplus using weighted patronage factors (savings balances, transaction volume, loan repayment performance, governance participation); factor weights are themselves subject to member vote (FINANCIAL_POLICY proposals). | P2 |
| F-127 | Automated Dividend Payout | CAP-7.3 | All members | Distributes 100% of approved dividends within 5 business days of AGM ratification (KPI-4.3), to the member's savings account or as share-capital reinvestment per member election. | P2 |
| F-128 | Real-Time Dividend Estimator | CAP-7.4 | P-1, P-2, P-3 | Live member dashboard projecting the annual Patronage Dividend and showing which behaviors (saving, repaying, voting) raise it. | MVP |
| F-129 | Dividend & Tax Statements | CAP-7.5 | All members, P-5 | Annual statements for members and jurisdictional tax reporting artifacts. | P2 |

### Governance & Voting (CAP-8)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-130 | Voting Portal | CAP-8.2 | P-1, P-4 | Mobile-native secret ballot on active proposals; one member, one vote; choices FOR / AGAINST / ABSTAIN (DEC-1); eligibility snapshot at ballot open; receipt without revealing vote content. | MVP |
| F-131 | Proposal Builder | CAP-8.1 | P-4, P-1 | Structured workflow to draft a proposal, select its category (COMMUNITY_GRANT / FINANCIAL_POLICY / GOVERNANCE_BYLAW, DEC-2), gather required co-signatures, and submit for admin scheduling; status per DEC-9. | P2 |
| F-132 | Board Elections | CAP-8.3 | All members, P-5 | Candidate profiles, election ballots (choose up to N seats), term tracking, certified results. | P2 |
| F-133 | Proxy Delegation | CAP-8.4 | P-1, P-3 | Delegate one's vote per proposal category to another ACTIVE member; single-level (no transitive chains, DEC-8); instantly revocable; delegation shown in the member's governance dashboard. | P2 |
| F-134 | Proposal Discussion Threads | CAP-8.5 | P-1, P-4 | Threaded discussion attached to each proposal, with community-standards moderation and admin lock at ballot open. | P2 |
| F-135 | Governance Archive & Audit Trail | CAP-8.6 | P-4, P-5 | Immutable record of proposals, ballots, turnout, certified outcomes, and minutes; publicly visible to members. | MVP |

### Community Funding (CAP-9) and Round-Ups (CAP-10)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-136 | Community Project Pitch Board | CAP-9.1 | P-4, P-1 | Members and registered local organizations list projects seeking funding, with goals, budgets, and impact descriptions; admin review before publication. | P2 |
| F-137 | Member Backing & Co-Investment | CAP-9.2 | P-1, P-4 | Back a project directly from savings; contribution history and project updates in-app. | P2 |
| F-138 | Surplus Matching Engine | CAP-9.3 | P-4 | Approved projects receive up to 1:1 matching from the Community Grant pool (10% of annual surplus, KPI-4.2); match release governed by COMMUNITY_GRANT ballots. | P2 |
| F-139 | Project Impact Tracker | CAP-9.4 | P-1 | Per-project fund-allocation and outcome reporting (impact figures labeled as estimates where modeled). | P3 |
| F-140 | Round-Up Savings | CAP-10.1, CAP-10.2 | P-2, P-1 | Round each card transaction to the nearest dollar; route the difference to a Savings Goal or a chosen community project; running impact/savings total. | MVP |

### Notifications (CAP-11), Admin (CAP-12), Compliance & Transparency (CAP-13)

| ID | Feature | Capability | Personas | Description | Priority |
| :--- | :--- | :--- | :--- | :--- | :--- |
| F-141 | Notification Center & Preferences | CAP-11.1–11.3 | All | Push/email/SMS/in-app notifications for payments, governance deadlines, loan milestones, and dividend events; per-channel preferences and quiet hours. | MVP |
| F-142 | Admin Member Console | CAP-12.1, CAP-12.2 | P-5 | 360° member view, KYC/AML review queues, status transitions under maker-checker, case notes. | MVP |
| F-143 | Admin Loan Operations Console | CAP-12.3 | P-5 | Manual underwriting review, restructuring, guarantor-pledge administration, write-off workflow. | P2 |
| F-144 | Governance Administration | CAP-12.4 | P-5 | Schedule ballots and elections, configure quorum and voting windows, certify and publish results. | P2 |
| F-145 | Product & Fee Configuration | CAP-12.5 | P-5 | Administer rates, fees, share par value, and transaction limits with effective-dating and audit. | P2 |
| F-146 | Dividend Run Administration | CAP-12.6 | P-5 | Input ratified surplus, approve the patronage calculation, execute and reconcile the payout run. | P2 |
| F-147 | AML Transaction Monitoring & SAR Workflow | CAP-13.1 | P-5 | Ongoing rules/ML monitoring, alert triage, suspicious-activity report preparation. | MVP |
| F-148 | Regulatory Reporting Suite | CAP-13.2 | P-5 | Scheduled prudential and lending reports (capital adequacy, liquidity, portfolio quality). | P2 |
| F-149 | Immutable Audit Log | CAP-13.3 | P-5 | Append-only log of financial, governance, and administrative actions with tamper evidence. | MVP |
| F-150 | Transparent Capital Ledger | CAP-13.4 | P-1, P-2 | Member-facing visual breakdown of collective fund deployment (local loans, green lending, Community Grants, liquidity reserves) refreshed at least daily. | MVP |
| F-151 | Personal Impact Scorecard | CAP-13.4 | P-1 | Per-member estimated impact attributable to their deposits (clearly labeled as modeled estimates). | P3 |
| F-152 | Data Privacy & Consent Management | CAP-13.5 | P-5, all members | Consent capture and withdrawal per member (Consent Record), data-retention schedule enforcement, and Data Subject Access Request intake, fulfilment, and deadline tracking. | P2 |

---

## 5. Traceability Summary

* Every capability CAP-1 … CAP-13 has at least one feature; every feature maps to exactly one primary capability group and at least one persona.
* KPI anchors: F-101 → KPI-1.1/1.2; F-121/F-125 → KPI-2.5; F-130/F-133 → KPI-3.1/3.2; F-126/F-127 → KPI-4.1/4.3; F-136–F-138 → KPI-4.2/4.4; F-150 → Objective 4 transparency commitments.

---

## 6. Canonical Glossary & Decision Log

**This section is normative.** All downstream documents — user stories, API specifications, data models, UI copy decks, and test plans — MUST use these terms and enum values **verbatim**. Enum values are `UPPER_SNAKE_CASE` machine values; each has one canonical display label. Superseded sprint terms are listed and must not reappear.

### 6.1 Adjudicated Decisions

| Decision ID | Topic | Canonical Decision | Superseded Variants | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **DEC-1** | **Vote choices** | Enum `VoteChoice = FOR \| AGAINST \| ABSTAIN`. Display labels: "For", "Against", "Abstain". | API drafts used `YES/NO/ABSTAIN`; stories used For/Against/Abstain. | For/Against is the standard parliamentary vocabulary for cooperative resolutions and is unambiguous in negatively-phrased motions ("YES" to "Should we NOT raise fees?" is ambiguous). Machine values mirror the display labels 1:1. |
| **DEC-2** | **Proposal categories** | Enum `ProposalCategory = COMMUNITY_GRANT \| FINANCIAL_POLICY \| GOVERNANCE_BYLAW`. Display labels: "Community Grant", "Financial Policy", "Governance Bylaw". Board elections are **not** a proposal category — they are a separate ballot type `BallotType = PROPOSAL \| BOARD_ELECTION`. | "Community Grant/Operating Rules"; "Community Grant/Cooperative Rules/Financial Policy"; `FUNDING_ALLOCATION/POLICY_CHANGE/MEMBER_BYLAW`. | Three-way split cleanly partitions the domain: money to community (COMMUNITY_GRANT ⊇ FUNDING_ALLOCATION), rates/fees/dividend-weight decisions (FINANCIAL_POLICY ⊇ POLICY_CHANGE), and rules of the cooperative itself (GOVERNANCE_BYLAW ⊇ Operating Rules, Cooperative Rules, MEMBER_BYLAW). |
| **DEC-3** | **P2P recipient identifier** | A P2P recipient is addressed by exactly one of: **registered phone number, registered email address, or Member ID**. Enum `RecipientIdentifierType = PHONE \| EMAIL \| MEMBER_ID`. **Usernames/handles are not supported.** | "username or phone number"; "phone/email/member ID". | Phone and email are already KYC-verified attributes; Member ID is system-issued and collision-free. A separate username namespace adds squatting/impersonation risk and another credential to govern, with no capability the other three don't cover. |
| **DEC-4** | **Membership status enum** | `MembershipStatus = PENDING_KYC \| PENDING_PAYMENT \| ACTIVE \| SUSPENDED \| CLOSED`. Transitions: PENDING_KYC → PENDING_PAYMENT (KYC approved) → ACTIVE (initial share settled); ACTIVE ↔ SUSPENDED (admin action, appealable); ACTIVE/SUSPENDED → CLOSED (voluntary exit, share redemption, or expulsion per bylaws). KYC rejection ends the *application*; no member record reaches a "rejected" membership status. Only ACTIVE members may vote, borrow, or guarantee. | `PENDING_TOKEN` (undefined sprint value); implicit/incomplete lifecycles. | Covers the full lifecycle with no dead-end or undefined states. Sprint 2's "membership token generated after share purchase" event maps to the PENDING_PAYMENT → ACTIVE transition; a distinct PENDING_TOKEN state observed nothing a member or admin could act on. |
| **DEC-5** | **KYC vendor** | **Persona** is the canonical identity-verification vendor for document OCR, biometric selfie match, and watchlist screening. All specs, sequence diagrams, and integration stories reference Persona. | Sprint docs alternated between Persona and Jumio. | One vendor must be named for consistent API contracts and test fixtures. Persona is selected for its developer-first API, dynamic-flow configurability suited to a mobile-first onboarding under the 8-minute KPI, and usage-based pricing appropriate to a launch-stage cooperative. (Jumio remains a documented fallback candidate; substituting it later is an integration change, not a requirements change.) |
| **DEC-6** | **Member name & address model** | **Three-part Mongolian name model, stored in Cyrillic as canonical:** `ovog` (clan name, **optional**), `etsgiin_ner` (patronymic — the father's given name in the genitive, ordered **before** the given name), `ner` (**the given name; the person's identity and the sort key** for display, ordering and search). Two supporting fields: `mrz_name_latin` — the Latin name string captured **verbatim** from the document machine-readable zone, never derived or transliterated by the platform, never member-editable; and `registration_number` — the 10-character national registration number (2 Cyrillic letters + 8 digits, structural validation only per the platform ID rule). Normative: (a) `etsgiin_ner` occupies the surname slot in the passport MRZ, so **siblings share a value and a parent and child never do** — any "same surname ⇒ same household / related party / possible duplicate" heuristic is prohibited; (b) a Latin form is only ever `mrz_name_latin` as captured — the platform never transliterates Cyrillic to Latin; (c) `registration_number` is the sole key for **identity matching, duplicate detection, KYC and screening correlation, and record linkage**, and **no name field is ever a matching key**, alone or combined, exact or fuzzy (addressing a P2P payee is a different operation, governed by DEC-3 and unaffected); (d) an applicant-entered `registration_number` is provisional and used only for routing — **the verified value returned by the identity source is authoritative**, a mismatch **blocks the application** rather than overwriting either value, and the uniqueness constraint applies to the verified value. A read-only derived `legal_name` — the composition `ovog` `etsgiin_ner` `ner`, or the document name as captured — may be displayed but is never independently stored/edited. Plus a structured postal address (`address_line_1`, `address_line_2`, `city`, `region`, `postal_code`, `country`). | Single free-text `legal_name` as a stored editable field; a two-field Western given-name/family-name model with an optional middle name (treats the patronymic as a family name — invalid here); models omitting address. | KYC vendors, card issuance/embossing, and regulatory reports all require decomposable name components; a single string cannot be reliably decomposed. That argument stands and produced this decision — what changes is the *shape* of the structure, not the need for one: the correct decomposition for the Mongolian market is clan / patronymic / given name, not given / family. The original rationale's "ACH/wire formats" clause is **retired as market-invalid** — that rail does not exist in Mongolia — not as reasoning-invalid; the remaining rationale is unaffected. Ordering matters (patronymic precedes given name) and the given name — not the patronymic — is the identity, so a Western-shaped model would sort, address and match members wrongly. |
| **DEC-7** | **Peer-guaranteed lending terminology** | Canonical term: **"Loan Circle"** — a group of 3–5 ACTIVE members who **vouch** for a borrower by **pledging** part of their savings or share capital as partial security. Members of a circle are **"guarantors"**; the pledged amount is a **"guarantee pledge"**. The ROSCA variant is a **"Pooled Loan Circle"**. | "Trust Circles" (Sprint 1); "Social Loan Circles" (Sprint 2); "Peer-Supported Lending Circles", "Lending Circles" (Sprint 3). | One name is required across UI, stories, and APIs. "Loan Circle" is the shortest term that says what it does; "trust" and "social" are marketing adjectives, not domain semantics. Group size 3–5 was consistent across sprints and is retained. |
| **DEC-8** | **Vote delegation terminology & semantics** | Canonical term: **"Proxy Delegation"**. Semantics: category-scoped (per `ProposalCategory` and/or BOARD_ELECTION), delegable to exactly one ACTIVE member per scope, **single-level** (a delegate cannot re-delegate a received vote), instantly revocable, and overridable by the delegator voting directly before ballot close. | "Liquid Democracy", "Liquid Democracy Engine", "proxy/liquid delegation", "Proxy Routing", "delegated voting". | "Proxy Delegation" is the regulator-recognizable term for cooperative governance. Single-level delegation avoids the transitive-chain complexity (cycles, hidden vote concentration) of full liquid democracy while preserving the member benefit. |
| **DEC-9** | **Proposal status enum** | `ProposalStatus = DRAFT \| SUBMITTED \| OPEN_FOR_VOTING \| PASSED \| REJECTED \| WITHDRAWN`. (SUBMITTED covers admin review/co-signature verification and ballot scheduling; a proposal failing quorum is REJECTED with reason `QUORUM_NOT_MET`.) | Assorted informal states across sprint narratives. | A single explicit state machine prevents downstream teams inventing incompatible statuses. |
| **DEC-10** | **Dividend vocabulary & cycle** | Canonical term: **"Patronage Dividend"** — the member's share of annual surplus, computed from patronage factors (savings balances, transaction volume, loan repayment performance, governance participation). **Cycle: annual**, ratified at the AGM, paid within 5 business days (KPI-4.3); the member-facing projection is the **"Dividend Estimator"** and updates in real time. | "Activity Dividend", quarterly payout (Sprint 1); "Member Return" (Desjardins-inspired); "pro-rata dividend". | Annual distribution matches cooperative accounting (surplus is only final after year-end audit and AGM ratification) and Sprint 3's payout KPI; Sprint 1's desire for frequency is satisfied by the real-time estimator, not by quarterly payouts. |
| **DEC-11** | **Initial membership share price** | **One mandatory membership share at $25.00 par value**, purchased during onboarding; non-withdrawable while membership is ACTIVE; redeemable at par on CLOSED (subject to bylaws). | $25 (Sprint 2) vs $5 (Sprint 3). | $25 is meaningful enough to fund guarantee pledges and signal commitment while remaining a low entry barrier; it was also the figure tied to the onboarding flow spec. Final par value remains subject to legal/regulatory confirmation, but $25 is the working canonical value for all documents. |
| **DEC-12** | **Round-up terminology** | Canonical term: **"Round-Up"** (noun/adjective: "Round-Up Savings", "Round-Up contribution"). Destination is member-chosen: a Savings Goal or a community project. | "spare-change roundups", "Ethical Round-Ups", "micro-contribution pipeline", "Smart Savings". | One term for one mechanism; the ethical destination is a routing option, not a separate feature name. |
| **DEC-13** | **Group money terminology** | **"Savings Goal"** = personal sub-account pot. **"Group Pot"** = shared multi-member pot with collective (m-of-n) approval. | "savings pots", "Shared Pots", "Group Expense Splitting accounts", "Shared Housing & Group Pots", "goal accounts". | Distinguishes the personal and shared constructs that sprints blurred together. |
| **DEC-14** | **Community funding vocabulary** | **"Community Funding Hub"** = the overall capability (CAP-9). **"Community Project"** = a listed initiative. **"Community Grant"** = money allocated from the cooperative's surplus-funded grant pool (see DEC-2 category). **"Backing"** = a member's direct contribution to a project. **"Surplus Match"** = the cooperative's matching contribution (≤ 1:1). | "Pitch Desk", "Crowdfunding Hub", "Surplus-Matching Portal", "Micro-Community Funding", "Community Impact funding portal", "local bonds". | Collapses five sprint names into one noun set with distinct meanings for pool, project, member money, and matching money. |
| **DEC-15** | **Transparency vocabulary** | **"Transparent Capital Ledger"** = the member-facing fund-deployment view (F-150). **"Impact Scorecard"** = the per-member estimated impact report (F-151). All impact figures derived from models must be labeled "estimated". | "Real-Time Impact Ledger", "Capital Ledger Map", "Allocation Tracker", "ESG Dashboard", "Financial Wellness Compass". | One name per artifact; the estimate-labeling rule enforces the "no invented statistics as fact" policy in member-facing copy. |
| **DEC-16** | **Governance participation KPI name** | Canonical metric name: **"Governance Participation Rate"** — eligible members who cast or delegate a vote in a ballot, ÷ eligible members. Delegated votes count toward the delegator's participation. | "Voter Turnout Rate", "member turnout". | One metric name with an explicit formula prevents inconsistent reporting; counting delegation preserves the incentive DEC-8 creates. |
| **DEC-17** | **Onboarding time definition** | "Onboarding time" is measured from **first app-flow screen** to **MembershipStatus = ACTIVE** (KYC approved and initial share settled). Target: median ≤ 8 min, p90 ≤ 10 min (KPI-1.1). | "< 5 minutes" (Sprints 1–2), "< 8 minutes" (Sprint 3), unmeasured start/end points. | Resolves the sprint contradiction against the persona abandonment ceiling (> 10 min) with a defined measurement window; 5 minutes survives only as a stretch goal. |
| **DEC-18** | **Currency & amount conventions** | All amounts in this program are **USD**; machine representations use minor units (integer cents) with ISO-4217 code `USD`. | Unstated/mixed currency assumptions. | Prevents drift in API/data-model documents. |
| **DEC-19** | **KYC status enum** | `KycStatus = NOT_STARTED \| IN_PROGRESS \| PENDING_REVIEW \| APPROVED \| REJECTED`. PENDING_REVIEW routes to the CAP-12.2 manual queue. | Ad-hoc phrases ("compliance clearance", "verified"). | Downstream onboarding stories and the Persona integration need one status vocabulary. |
| **DEC-20** | **Loan status enum** | `LoanStatus = DRAFT \| SUBMITTED \| UNDER_REVIEW \| APPROVED \| ACTIVE \| DELINQUENT \| PAID_OFF \| DEFAULTED \| WRITTEN_OFF` (ACTIVE begins at disbursement). | None consistent across sprints. | Single lifecycle for origination, servicing, and NPL reporting (KPI-2.5). |

> **Amendment record.** **DEC-6** was **amended in place** (not renumbered, not superseded by a new decision ID) to replace the two-field Western name model with the three-part Mongolian model (`ovog` / `etsgiin_ner` / `ner`), add `mrz_name_latin` and `registration_number`, and redefine the retained derived term `legal_name` as the composition of the three Cyrillic fields. The address portion of DEC-6 is unchanged by this amendment. All other DEC-1…20 entries are unamended.

### 6.2 Canonical Term Table (Quick Reference)

| Canonical Term / Enum | Definition | Do NOT Use |
| :--- | :--- | :--- |
| **Member** | A natural person with a membership record; holds exactly one voting right when ACTIVE. | "customer", "user" (in domain documents; "user" acceptable only in UX artifacts) |
| **Member ID** | System-issued unique member identifier; a P2P recipient identifier type. | "username", "handle", "member number" |
| **Membership Share Account** | Non-withdrawable equity account holding membership share(s); dividend-bearing; par $25. | "Co-op Share Account", "Share Capital Registry" (as account name) |
| **Primary Savings Account / Transaction Account / Savings Goal / Group Pot** | The four deposit constructs per DEC-13. | "pots" (unqualified), "Shared Pots", "checking pot" |
| `MembershipStatus` = `PENDING_KYC`, `PENDING_PAYMENT`, `ACTIVE`, `SUSPENDED`, `CLOSED` | Membership lifecycle per DEC-4. | `PENDING_TOKEN`, "verified member" |
| `KycStatus` = `NOT_STARTED`, `IN_PROGRESS`, `PENDING_REVIEW`, `APPROVED`, `REJECTED` | KYC lifecycle per DEC-19. | "cleared", "compliance passed" |
| **Persona (vendor)** | The identity-verification vendor (DEC-5). | Jumio (except in the fallback note) |
| `ovog` / `etsgiin_ner` / `ner` (+ `mrz_name_latin`, `registration_number`, structured address) | Member name/address model per DEC-6. `ner` is the given name and the sort key; `etsgiin_ner` is a patronymic, not a family name; `legal_name` is the read-only derived composition of the three. | standalone editable `legal_name`; any two-field given/family name model; a platform-generated Latin transliteration; matching members on name |
| `RecipientIdentifierType` = `PHONE`, `EMAIL`, `MEMBER_ID` | P2P addressing per DEC-3. | `USERNAME` |
| **Ballot** / `BallotType` = `PROPOSAL`, `BOARD_ELECTION` | A voting event per DEC-2. | "poll", "resolution vote" (as type names) |
| `VoteChoice` = `FOR`, `AGAINST`, `ABSTAIN` | The only vote choices (DEC-1). | `YES`, `NO`, "approve/deny" |
| `ProposalCategory` = `COMMUNITY_GRANT`, `FINANCIAL_POLICY`, `GOVERNANCE_BYLAW` | Proposal taxonomy (DEC-2). | `FUNDING_ALLOCATION`, `POLICY_CHANGE`, `MEMBER_BYLAW`, "Operating Rules", "Cooperative Rules" |
| `ProposalStatus` = `DRAFT`, `SUBMITTED`, `OPEN_FOR_VOTING`, `PASSED`, `REJECTED`, `WITHDRAWN` | Proposal lifecycle (DEC-9). | "pending", "live", "closed" |
| **Proxy Delegation** | Category-scoped, single-level, revocable vote delegation (DEC-8). | "Liquid Democracy", "Proxy Routing" |
| **Governance Participation Rate** | Voted-or-delegated ÷ eligible, per ballot (DEC-16). | "Voter Turnout Rate" |
| **Loan Circle** / **Pooled Loan Circle** / **guarantor** / **guarantee pledge** | Peer-guaranteed lending constructs (DEC-7). | "Trust Circle", "Social Loan Circle", "voucher", "co-signer pool" |
| `LoanStatus` (per DEC-20) | Loan lifecycle. | ad-hoc statuses |
| **Patronage Dividend** / **Dividend Estimator** | Annual member surplus share and its real-time projection (DEC-10). | "Activity Dividend", "Member Return", "yield bonus" |
| **Community Funding Hub / Community Project / Community Grant / Backing / Surplus Match** | Community funding noun set (DEC-14). | "Pitch Desk", "local bonds", "crowd pool" |
| **Round-Up** | Card-transaction rounding contribution (DEC-12). | "spare change sweep", "Ethical Round-Ups" |
| **Transparent Capital Ledger** / **Impact Scorecard** | Transparency artifacts (DEC-15); modeled figures labeled "estimated". | "Impact Ledger", "ESG Dashboard" |
| **AGM** | Annual General Meeting — ratifies accounts and the dividend run. | "annual vote event" |
| `USD`, integer minor units | Money representation (DEC-18). | floats, unstated currency |

### 6.3 Open Items (Not Resolvable at Requirements Level)

1. **Legal/regulatory confirmation of the $25 share par value and share-redemption terms (DEC-11)** — requires counsel review against the chartering jurisdiction's cooperative/credit-union statute.
2. **Guarantee-pledge enforceability (DEC-7 / F-121)** — whether pledged share capital may legally secure another member's loan varies by jurisdiction; the requirement stands, the legal mechanism is TBD.
3. **Deposit-insurance representation** — depends on the charter obtained (credit union vs bank vs e-money partnership); all member-facing copy must remain accurate to the final structure.
4. **KPI-4.5 (60% impact-aligned lending)** — retained as aspirational; to be re-baselined after Year 1 underwriting data exists.

---

*End of document. This file and 00_market_research.md are the authoritative consolidated requirements baseline; the sprint_1–sprint_3 documents are superseded.*
