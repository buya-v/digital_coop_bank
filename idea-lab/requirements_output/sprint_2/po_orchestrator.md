# Product Requirements & Sprint Orchestration Document: Digital Coop Bank

This document represents the unified product requirements, sprint backlog scoping, sprint-specific MoSCoW prioritization, and the multi-phase release roadmap for **Digital Coop Bank**, a purely digital cooperative banking platform.

---

## 1. Product Requirements Document (PRD) Synthesis

### Vision & Strategy
Digital Coop Bank combines the premium, mobile-first user experience of modern retail neobanks with the ethical, democratic, and wealth-distributing principles of traditional cooperative financial institutions. By digitalizing the "one member, one vote" governance model and introducing community-vouched credit mechanics, the bank addresses the market gap between impersonal corporate neobanks and technologically outdated local credit unions.

### Target Personas
*   **Eco-Conscious Evan (The Ethical Consumer):** Demands complete transparency on deposit allocations, seeks high-quality digital interfaces, and actively reinvests personal funds into local, green projects.
*   **Cooperative Clara (The Gig Worker & Small Entrepreneur):** Has irregular income patterns that fail traditional algorithmic credit scoring; requires flexible, community-guaranteed credit options and remote democratic participation.
*   **Community Marcus (The Grassroots Organizer):** Directs neighborhood non-profits, seeks collateral-free community development loans using group trust, and organizes local crowdfunding initiatives.

### Core Capability Domains
1.  **Member Identity & Trust Services:** Automated eKYC validation (photo ID OCR, biometric liveness check), common bond verification, and membership token lifecycle management.
2.  **Core Banking Ledger & Treasury:** Strict double-entry ledger architecture containing withdrawable savings, transactional balances, non-withdrawable share capital accounts, and real-time payment network settlements (e.g., FedNow, ACH, SEPA).
3.  **Peer-Supported Lending Suite:** Alternative underwriting engines mapping transactional history, managing group invitation frameworks, automating collateral holds on guarantor savings, and administering dynamic interest pricing.
4.  **Democratic Governance Portal:** Secure voting matrices maintaining ballot listings, implementing category-specific proxy delegation paths, and enabling direct vote overrides.
5.  **Cooperative Dividend Engine:** Calculated patronage distributions derived from members' annual transactional footprint (deposit averages, card spending volume, and active credit interests).
6.  **Community Impact & Crowdfunding Hub:** Platform desks enabling local non-profits to pitch capital projects, facilitating direct member investments into local bonds, and processing micro-contribution card round-ups.

### Security, Compliance, & Non-Functional Requirements (NFRs)
*   **Ledger Consistency:** Relational database systems operating under Strict Serializability isolation levels. Eventual consistency is strictly prohibited for financial transactional accounts.
*   **Data Privacy & Encryption:** AES-256 GCM encryption at rest for PII data, with TLS 1.3 enforced for all network transactions.
*   **Democratic Secret Ballot Protocol:** Separation of audit trails from voting choices. The system records who has voted to prevent duplicate submissions but registers choice data anonymously without foreign key relations to the voter's identity.
*   **Operational SLOs:** Write-heavy transactional API operations must clear within 200 milliseconds (p95); read-heavy queries must resolve within 50 milliseconds using optimized Redis caching.

---

## 2. Backlog Scoping & Sprint Allocation

The agile backlog is structured across four distinct sprints to progress from foundational setup to advanced engagement and ecosystem features.

### Sprint 1: Identity & Foundational Ledger (Completed)
*   **Focus:** Establish core database schemas, setup the Double-Entry Ledger System, and implement standard transaction API logic.
*   **Included Deliverables:** 
    *   Setup relational database entities for Members and Accounts.
    *   Configure transactional API gateways for deposits and withdrawals.
    *   Deploy basic user profile creation and initial API security configurations.

### Sprint 2: Core Cooperative Mechanics (Current Sprint)
*   **Focus:** Deliver automated onboarding compliance, enable peer-supported credit circles, and establish the baseline direct voting governance framework.
*   **Included Deliverables:**
    *   *Story 1.1:* Automated Identity Verification (eKYC with liveness verification).
    *   *Story 1.2:* Mandatory Member Share Purchase ($25 common bond validation).
    *   *Story 1.3:* Cooperative Membership Token Generation (system UI unlocking).
    *   *Story 2.1:* Social Loan Circle Creation & Invitation.
    *   *Story 2.2:* Pledging Share Capital as Security (guarantor account ledger holds).
    *   *Story 2.3:* Community-Guaranteed Underwriting & Dynamic Pricing.
    *   *Story 3.1:* Ballot Management and Direct Voting (one member, one vote).
    *   *Story 3.2:* Category-Specific Proxy Delegation.
    *   *Story 3.3:* Proxy Revocation and Direct Overrides.

### Sprint 3: Community Wealth & Reinvestment (Next Sprint)
*   **Focus:** Deploy transparent patronage dividend tracking and launch the community investment marketplace.
*   **Included Deliverables:**
    *   *Story 4.1:* Patronage Footprint Dashboard (displaying savings and transaction volumes).
    *   *Story 4.2:* Real-Time Dividend Estimator (scenarios and recommendations).
    *   *Story 5.1:* Listing Community Projects (Pitch Desk).
    *   *Story 5.2:* Direct Investment from Savings (escrow transfer and certificate hashing).
    *   *Story 5.3:* Democratic Community Grant Allocation (surplus distribution pool voting).

### Sprint 4: Micro-Engagement & Scalability (Future Sprint)
*   **Focus:** Automate micro-contributions, implement advanced scaling strategies, and perform load testing.
*   **Included Deliverables:**
    *   *Story 6.1:* Round-Up Activation & Configuration (multipliers and monthly caps).
    *   *Story 6.2:* Automated Round-Up Execution (cleared card transactions threshold sweep).
    *   *Story 6.3:* Live Impact Metrics Dashboard (visualizations of CO2 offset / local solar hours).
    *   *System Tuning:* Database partitioning on voting tables by ballot ID and async background processing for daily interest and balance updates.

---

## 3. MoSCoW Prioritization (Sprint 2)

To ensure a successful and compliant release of the Sprint 2 scope, the user stories from Epics 1, 2, and 3 are mapped below according to their criticality.

### Must Have
*   **Story 1.1: Automated Identity Verification (eKYC)**
    *   *Rationale:* Non-negotiable regulatory entry point. The system cannot onboard users or open financial accounts without complying with identity, age, and fraud-detection frameworks.
*   **Story 1.2: Mandatory Member Share Purchase**
    *   *Rationale:* Cooperative regulations require depositors to hold a member share to be legally recognized as member-owners of the cooperative.
*   **Story 1.3: Cooperative Membership Token Generation**
    *   *Rationale:* The structural foundation of session authorization. A cryptographically secure membership identifier is required to unlock protected governance and savings features.
*   **Story 3.1: Ballot Management and Direct Voting**
    *   *Rationale:* The fundamental democratic feature. Cooperative governance requires members to be able to vote directly on cooperative policies and resolutions.

### Should Have
*   **Story 2.1: Social Loan Circle Creation & Invitation**
    *   *Rationale:* Essential core of the peer-supported lending model. Without invitations, members cannot form trust networks to access credit.
*   **Story 2.2: Pledging Share Capital as Security**
    *   *Rationale:* Provides the database and ledger lock mechanism needed to secure alternative lending. Ensures guarantor capital is held securely during active loans.
*   **Story 3.3: Proxy Revocation and Direct Overrides**
    *   *Rationale:* Necessary for individual democratic sovereignty. Members must be able to override a proxy's vote to ensure they maintain final control over their democratic rights.

### Could Have
*   **Story 2.3: Community-Guaranteed Underwriting & Dynamic Pricing**
    *   *Rationale:* While dynamic discounting is a key differentiator, the early release could launch with flat, manually configured interest offsets for peer-backed loans, migrating to automated tier calculations later.
*   **Story 3.2: Category-Specific Proxy Delegation**
    *   *Rationale:* Highly innovative liquid democracy mechanism, but could be deferred in favor of direct voting if timeline constraints require a simplified initial release.

### Won't Have (Deferred to Sprints 3 & 4)
*   **Epic 4: Cooperative Dividends** (Deferred to Sprint 3)
*   **Epic 5: Community Crowdfunding & Investments** (Deferred to Sprint 3)
*   **Epic 6: Micro-Contributions** (Deferred to Sprint 4)
*   *Discussion Forum & Proposal Drafting:* Deferred to post-Sprint 4 features.

---

## 4. Release Roadmap

```
+------------------------------------+------------------------------------+------------------------------------+
|            PHASE 1 (MVP)           |              PHASE 2               |              PHASE 3               |
|      "Legal & Democratic Core"     |     "Community Wealth & Credit"    |     "Liquid Governance & Impact"   |
+------------------------------------+------------------------------------+------------------------------------+
|  * Automated Digital Onboarding    |  * Social Loan Circles             |  * Liquid Democracy & Proxies      |
|    (eKYC & Identity Verification)  |    (Group trust invitations)       |    (Category-specific delegation)  |
|  * Mandatory Member Share Setup    |  * Collateral hold engines         |  * Community Grant Allocations     |
|  * Core Double-Entry Ledger        |    (Guarantor savings locks)       |    (Surplus pool distribution)     |
|  * Ballot Management & Direct Vote |  * Patronage Dividend Tracker      |  * Card Transaction Round-ups     |
|    (One member, one vote)          |    (Daily footprint tracking)      |  * Live Impact Metrics Portal      |
|  * Basic Savings/Transactional     |  * Crowdfunding Pitch Desk         |  * Open Banking API Integrations   |
|    Deposit accounts                |    (Local bond investments)        |  * Ballot-ID DB Partitioning       |
+------------------------------------+------------------------------------+------------------------------------+
```

### Phase 1: Minimum Viable Product (MVP) - "Legal & Democratic Core"
*   **Target:** Establish a legally compliant, operational digital cooperative banking core.
*   **Capabilities Delivered:** Instant onboarding, secure double-entry account ledgers, share purchase mechanisms, and direct voting on active cooperative ballots.
*   **Success Metrics:** Onboarding completion rate > 85%, average time-to-onboard < 5 minutes, direct ballot submission functionality.

### Phase 2: Community Wealth & Credit
*   **Target:** Introduce the primary financial differentiators of the platform.
*   **Capabilities Delivered:** Peer-supported lending circles, collateral hold triggers, risk-adjusted interest rates, real-time dividend estimations, and community project investment capabilities.
*   **Success Metrics:** Active deposit-to-loan ratios between 75% and 85%, initial peer-guaranteed loans disbursed, first local project funding rounds initiated.

### Phase 3: Liquid Governance & Impact
*   **Target:** Scale democratic participation and introduce continuous community reinvestment.
*   **Capabilities Delivered:** Category-specific proxy voting routing, automatic community grant allocation payouts, card transaction round-up sweeps, and dynamic social impact translation metric cards.
*   **Success Metrics:** Member governance turnout > 45%, delegated voting proxy adoption > 20%, micro-contribution transaction processing, and database latency below 50ms at scale.