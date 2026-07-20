# Digital Coop Bank: Product Requirements Document (PRD) & Sprint 1 Orchestration

---

## 1. Product Requirements Document (PRD) Synthesis

### 1.1 Executive Summary & Vision
Digital Coop Bank (DCB) is a digital cooperative banking platform designed to combine modern digital banking convenience with the community-centric, democratic ownership model of credit unions. DCB addresses the market gap left by traditional financial institutions that lack transparency in capital deployment and operate under centralized, shareholder-first governance models. 

By utilizing modern mobile technology, DCB targets values-aligned consumers, independent gig workers, and community cooperative leaders. The platform stands on four core pillars:
1. **Embedded Democratic Governance:** Translating the "one member, one vote" philosophy into an in-app proposal and voting portal.
2. **Transparent Capital Ledger:** Providing real-time, interactive visibility into where member deposits are deployed (e.g., green bonds, local business loans, liquidity reserves).
3. **Community-Led Micro-Lending:** Replacing traditional, rigid credit scoring with cooperative trust networks and peer-backed microloans.
4. **Dynamic Dividend Engine:** Distributing quarterly profits back to members based on active participation, savings balances, and voting history rather than flat deposit volumes alone.

---

### 1.2 Target User Personas
To ensure that all features directly address user needs, the product requirements are mapped to four primary personas:

*   **Eco-Conscious Elena (The Values-Aligned Consumer):** Elena requires absolute transparency regarding capital deployment. She refuses to allow her deposits to fund fossil fuels or unethical industries. She uses the Transparent Capital Ledger to verify the environmental and local impact of her funds.
*   **Freelance Fabian (The Gig Economy Worker):** Fabian experiences fluctuating monthly income and struggles to secure credit from traditional banks. He seeks flexible banking features, peer-supported credit access (Trust Circles), and automated tools to manage micro-savings.
*   **Community Organizer Chloe (The Co-op Leader):** Chloe manages group treasuries and coordinates local initiatives. She relies on the Embedded Democratic Governance portal to run community votes and requires automated dividend distribution to reduce administrative overhead.
*   **Digital Native Daniel (The Gen Z Tech Enthusiast):** Daniel expects a premium mobile UI/UX, instant digital onboarding, and gamified financial incentives. He is motivated by micro-interactions, dark-mode styling, and transparent social impact tracking.

---

### 1.3 Scope of Domain Capabilities & KPIs
The functional scope of the platform is divided into seven core domains:

1. **Member Identity & Access Management (MIAM):** Fulfills identity verification (e-KYC) and membership status monitoring.
2. **Core Accounts & Share Ledger (CASL):** Manages regular liquid accounts alongside equity share accounts that establish cooperative membership and voting eligibility.
3. **Core Transactions & Payments (CTP):** Powers instant peer-to-peer transfers, virtual debit cards, and external transfers.
4. **Embedded Democratic Governance (EDG):** Drives the active proposal catalog and secure voting mechanisms.
5. **Community Lending & Trust Networks (CLTN):** Handles cooperative underwriting, microloan applications, and trust circle mechanics.
6. **Dynamic Dividend Engine (DDE):** Runs calculations for cooperative profit sharing based on savings deposits and platform engagement.
7. **Transparent Capital Ledger (TCL):** Aggregates assets under management and maps them to active sustainable projects.

#### Key Performance Indicators (KPIs)
To measure product success, the platform will track:
*   **Active Membership:** Target of 50,000 active members in Year 1 (performing at least 3 transactions monthly).
*   **Assets Under Management (AUM):** Target of $25,000,000 in total deposits.
*   **Voter Turnout Rate:** Target of >45% participation per governance proposal.
*   **Social Impact Deployment:** Target of 60% of the loan portfolio directed into ESG-verified initiatives.
*   **Onboarding Efficiency:** Average customer onboarding time under 5 minutes.

---

### 1.4 Technical Architecture & Integration Specifications
The technical foundation relies on a relational database design, secure REST APIs, and third-party integrations.

#### Abstract Data Model
The database manages 12 core entities:
*   **Member:** Stores personal details, KYC status, and membership tier.
*   **KYCSubmission:** Logs documentation metadata and biometric match scores.
*   **Account:** Tracks checking, savings, and share account ledger balances.
*   **Card:** Represents virtual debit cards linked to checking accounts.
*   **Transaction:** The double-entry ledger tracking all debits and credits.
*   **ShareLedger:** Records capital contributions and active voting weights.
*   **Proposal:** Represents active democratic proposals and cached tallies.
*   **Vote:** Stores anonymous individual voting selections.
*   **VoterParticipation:** Prevents double-voting using hashed identifiers.
*   **LoanApplication:** Manages principal, interest rates, and loan statuses.
*   **CapitalProject:** Tracks specific cooperative investments.
*   **SavingsSetting:** Saves user preferences for automated round-ups.

#### Integration Architecture
*   **Identity Verification (Persona API):** Onboarding initiates an inquiry session. The client runs the native photo capture and liveness checks. Persona posts webhook events back to the backend. The backend updates the member status to `Verified` upon successful completion.
*   **Open Banking (Plaid & Unit Core):** Links external bank accounts and pulls the initial membership share payment ($10). Upon clearing, the backend executes double-entry credits to the Share Ledger.
*   **Card Issuing (Lithic API):** Generates virtual card parameters. Lithic leverages active authorization webhooks to validate transactions against checking account balances in real-time, enforcing a 200ms response SLA.

---

## 2. Backlog Scoping (Sprint Allocation)

The features and user stories are organized into a logical execution plan across three distinct development phases.

### Sprint 1: Identity, Equity, & Core Ledger (Foundational MVP)
*   **MIAM - Government ID Upload (US-1.1a):** Enable document upload, format checking, and basic validation.
*   **MIAM - Liveness Check (US-1.1b):** Implement facial scanning and liveness verification matching.
*   **MIAM - Profile Dashboard (US-1.3a):** Render member profile card, unique Member ID, and verification status.
*   **CASL - Co-op Share Visibility (US-2.1a):** Display share accounts, share values, and voting weight rules.
*   **CASL - Share Purchase (US-2.1b):** Link external bank accounts and process the mandatory $10 share payment.
*   **CTP - Instant P2P Send (US-3.1a):** Implement peer transfers using usernames/phone numbers with search functionality.
*   **EDG - Proposal Browser (US-4.2a):** Construct the active proposal listing page with status filters.
*   **EDG - Secure Vote Submission (US-4.2b):** Establish vote casting with biometric verification and double-voting blocks.
*   **TCL - Interactive Capital Ledger (US-7.1a):** Render the capital reserve asset allocation chart (Green Bonds, Loans, Liquidity).

### Sprint 2: Account Automation, Virtual Cards, & Yield Tracking (Utility MVP)
*   **CASL - Smart Savings Toggle (US-2.3a):** Build UI settings for transaction round-ups and goal selection.
*   **CASL - Round-Up Automation (US-2.3b):** Automate secondary internal transfers from checking to savings post-authorization.
*   **CTP - PDF Receipts (US-3.1b):** Enable PDF generation and download of signed transaction receipts.
*   **CTP - Virtual Card Generation (US-3.3a):** Request biometric verification and generate instant virtual cards.
*   **CTP - Freeze/Unfreeze Card (US-3.3b):** Provide instant card blocking toggle to intercept unauthorized merchant requests.
*   **DDE - Yield Graph (US-6.3a):** Develop interactive charts showing cumulative savings interest history.
*   **DDE - Dividend Projection (US-6.3b):** Calculate upcoming quarterly dividends dynamically.
*   **TCL - Project Spotlights (US-7.1b):** Link allocation categories to details showing funded local businesses.

### Sprint 3: Advanced Governance, Lending, & Community Integrations (Phase 2 Launch)
*   **EDG - Proposal Creator (F-402):** Allow members meeting specific share thresholds to draft and submit proposals.
*   **CLTN - Microloan Form (US-5.1a):** Build microloan applications for amounts up to $1,000 with term selections.
*   **CLTN - Interest Pre-Screening (US-5.1b):** Implement the interest discount algorithm based on voting and savings metrics.
*   **CLTN - Trust Circles (F-501):** Introduce social-collateral networks to co-sign and back group member loans.
*   **DDE - Automated Dividend Payouts (F-601):** Run quarterly distribution logic crediting member accounts from the coop surplus pool.
*   **TCL - Personal Impact Score (F-702):** Calculate individual impact scores based on personal deposit volumes and project distribution.

---

## 3. Sprint 1 Prioritization (MoSCoW Mapping)

For Sprint 1, the scope is prioritized to deliver a working end-to-end framework of cooperative membership: joining, securing identity, buying equity, transferring basic funds, and exercising voting rights.

### Must Have
*   **Government ID Verification (US-1.1a):** Required for regulatory compliance and identity check initiating.
*   **Initial Share Purchase (US-2.1b):** Mandatory to legally capitalize the cooperative and activate member voting weight.
*   **Instant P2P Transfer (US-3.1a):** The core utility path proving ledger capability.
*   **Secure Vote Submission (US-4.2b):** Enforces democratic participation and checks double-voting constraints.
*   **Interactive Capital Ledger Chart (US-7.1a):** Establishes the transparent value proposition from day one.

### Should Have
*   **Liveness Check (US-1.1b):** Crucial to prevent presentation attacks and reduce manual verification backlogs.
*   **View Member Profile (US-1.3a):** Displays membership status and cooperative standing to the user.
*   **Browse Active Proposals (US-4.2a):** Provides the entry point for the governance portal.

### Could Have
*   **Co-op Share Visibility (US-2.1a):** While important, this dashboard card can initially show simple text values before the full dynamic component is finalized.
*   **Automated Interest Estimate (US-5.1b):** Can run on static calculations in Sprint 1 before linking to the underwriting engine.

### Won't Have (Deferred to Sprint 2 / Sprint 3)
*   **Smart Savings Settings & Automation (US-2.3a, US-2.3b):** Scheduled for Sprint 2 to allow the core transaction engine to stabilize.
*   **Virtual Card Management (US-3.3a, US-3.3b):** Deferred to Sprint 2 to isolate active authorization webhook performance testing.
*   **Microloan Application (US-5.1a):** Scheduled for Sprint 3.
*   **Dividend Projections (US-6.3b):** Requires baseline transactions and historical database histories to show useful data.
*   **Capital Project Spotlights (US-7.1b):** Expanded detail modals are secondary to the primary allocation donut chart.

---

## 4. Product Release Roadmap

```
[Release Phase Roadmap]
├── MVP (Phase 1)
│   ├── Foundational Onboarding & KYC
│   ├── Basic P2P Internal Payments
│   ├── Interactive Capital Ledger
│   └── Base Proposal Voting
├── Phase 2 (Growth & Lending)
│   ├── Virtual Debit Cards (Lithic Integration)
│   ├── Automated Micro-Savings (Round-Ups)
│   ├── Yield Tracker & Dividend Projections
│   └── Community Microloan Pilot (Up to $1000)
└── Phase 3 (Decentralized Ecosystem)
    ├── Peer Trust Circles & Collateral Pooling
    ├── Member-Generated Proposal Portal
    ├── Dynamic Dividend Distribution Engine
    └── Real-time ESG Impact Scorecards
```

### Phase 1: Foundational MVP (Sprint 1 & Sprint 2)
The objective of Phase 1 is to deploy a regulatory-compliant digital banking shell that establishes cooperative membership.
*   **Key Capabilities:** Instant KYC via Persona, external funding links via Plaid, checking accounts, P2P payments, virtual debit cards, interactive capital allocation charts, and "One Member, One Vote" governance.
*   **Target User Benefit:** Ethical consumers can join, verify that their funds are allocated to sustainable categories, and vote on basic bylaws.

### Phase 2: Growth & Lending (Sprint 3 & Sprint 4)
Phase 2 shifts focus to financial utility and credit access, launching the core cooperative differentiators.
*   **Key Capabilities:** Automated savings round-ups, community-vetted microloans up to $1,000, interest discounts tied to cooperative engagement metrics, and graphic yield tracking.
*   **Target User Benefit:** Gig workers and values-aligned savers can borrow small amounts at discounted rates by proving positive contribution and voting engagement.

### Phase 3: Decentralized Cooperative Ecosystem (Sprint 5+)
Phase 3 expands democratic control and introduces community-led risk sharing.
*   **Key Capabilities:** Trust Circles (enabling members to co-sign and pool collateral for peer loans), member-created proposals, the fully automated Dynamic Dividend Engine distributing quarterly pool shares, and personalized ESG impact scores showing the exact reduction in carbon emissions linked to member deposits.
*   **Target User Benefit:** Community organizers can utilize the platform to pool community funds, create localized funding proposals, and distribute profits automatically back to local project participants.