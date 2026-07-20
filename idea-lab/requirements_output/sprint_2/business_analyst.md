# Digital Coop Bank - Business Requirements Document & Functional Scope (Sprint 2)

This document defines the functional scope, target personas, business goals, domain capability map, and feature list for the proposed purely digital cooperative banking platform.

---

## 1. Target User Personas

To align the platform's product development with market demands, we define three primary target personas representing the core segments of the Digital Coop Bank.

### Persona 1: "Eco-Conscious Evan" (The Ethical Consumer)
*   **Demographics:**
    *   **Age:** 24–32
    *   **Occupation:** Software Developer / Creative Professional
    *   **Income:** $65,000–$90,000/year
    *   **Location:** Urban center
*   **Needs & Goals:**
    *   Demands 100% transparency on where deposits are directed (e.g., green energy, local social housing, fair-trade businesses).
    *   Desires a premium, high-quality mobile application experience comparable to leading fintech neobanks.
    *   Wants to avoid traditional banks that invest in fossil fuels or engage in predatory lending practices.
*   **Behaviors:**
    *   Actively researches corporate ethics and ESG ratings before choosing services.
    *   Prefers digital-first payment methods, contactless transactions, and interactive financial dashboards.
    *   Engages heavily in social media communities centered on sustainability and social justice.
*   **Pain Points:**
    *   Traditional ethical banks (e.g., credit unions) have outdated, clunky user interfaces and require branch visits.
    *   Existing neobanks lack a collective ownership structure, passing profits to venture capital rather than back to depositors or local communities.

### Persona 2: "Cooperative Clara" (The Gig Worker & Small Entrepreneur)
*   **Demographics:**
    *   **Age:** 30–45
    *   **Occupation:** Independent Organic Farmer / Freelance Gig Economy Worker
    *   **Income:** Variable, $35,000–$60,000/year
    *   **Location:** Suburban or Rural-fringe
*   **Needs & Goals:**
    *   Requires flexible, low-cost financial services that accommodate fluctuating monthly incomes.
    *   Needs access to business credit and small equipment loans without rigid corporate underwriting.
    *   Wants to participate in banking decisions and earn dividends that represent a return on her financial contribution (patronage).
*   **Behaviors:**
    *   Manages business and personal finance through mobile apps.
    *   Collaborates with local regional networks, cooperatives, and farmer-to-consumer platforms.
    *   Maintains a strong regional presence and relies on community reputation.
*   **Pain Points:**
    *   Standard algorithmic credit scoring rejects her due to irregular gig/farming income, overlooking local trust networks.
    *   Attending physical Credit Union Annual General Meetings (AGMs) is impossible due to time constraints and remote operations.

### Persona 3: "Community Marcus" (The Grassroots Organizer)
*   **Demographics:**
    *   **Age:** 40–55
    *   **Occupation:** Director of a Neighborhood Non-Profit / Community Housing Advocate
    *   **Income:** $50,000/year
    *   **Location:** Urban/Suburban community
*   **Needs & Goals:**
    *   Needs a transparent vehicle to raise community capital for local development projects (e.g., urban gardens, community centers).
    *   Wants credit solutions that leverage peer responsibility (social loan circles) rather than heavy assets.
    *   Seeks to empower low-income community members through democratic financial access.
*   **Behaviors:**
    *   Coordinates community initiatives using group chats, online boards, and local town halls.
    *   Maintains organizational funds with local financial institutions.
    *   Acts as a trusted liaison between community members and external partners.
*   **Pain Points:**
    *   Commercial banks demand substantial collateral and complex covenants for minor community development loans.
    *   Friction in traditional banking tools makes crowdfunding or co-investing slow and administratively heavy for small non-profits.

---

## 2. Business Objectives & Key Performance Indicators (KPIs)

To drive and measure the success of the platform, the business operates under four strategic pillars:

### Objective 1: Member Acquisition & Seamless Onboarding
*   **Goal:** Rapidly scale the cooperative membership base by removing friction while maintaining high compliance standards.
*   **KPIs:**
    *   **Cost Per Acquisition (CPA):** Keep customer acquisition cost under $25 through referral loops built on social lending and community circles.
    *   **Onboarding Completion Rate:** Achieve > 85% completion rate for sign-ups.
    *   **Time-to-Onboard:** Reduce the average time for complete digital identity verification (KYC/AML) and initial member share purchase to under 5 minutes.

### Objective 2: High Democratic Engagement
*   **Goal:** Redefine member control by converting governance into a low-friction, digital-first experience.
*   **KPIs:**
    *   **Governance Participation Rate:** Achieve > 45% member turnout in quarterly policy voting and annual board elections (compared to traditional credit union averages of < 5%).
    *   **Delegated Voting Adoption:** Maintain a > 20% active rate of proxy/liquid delegation where members route their votes to verified domain experts.

### Objective 3: Financial Sustainability & Loan Portfolio Quality
*   **Goal:** Build a robust, profitable portfolio of community loans and deposit products with minimal risk.
*   **KPIs:**
    *   **Non-Performing Loan (NPL) Rate:** Maintain a loan default rate under 1.8%, leveraging peer-vouching networks.
    *   **Deposit-to-Loan Ratio:** Keep the ratio between 75% and 85% to maintain liquidity while maximizing member deposits for community credit.
    *   **Capital Adequacy Ratio:** Maintain a capital reserve ratio > 10% to ensure regulatory resilience.

### Objective 4: Community Wealth Generation & Impact
*   **Goal:** Maximize wealth distribution to members and direct capital towards high-impact community initiatives.
*   **KPIs:**
    *   **Surplus Redistribution Rate:** Distribute > 60% of yearly net earnings back to members via patronage dividends.
    *   **Community Capital Raised:** Facilitate $1,500,000 in peer-vouched crowdfunding and green community loans during the first year.

---

## 3. Domain Capability Map

The Digital Coop Bank functional architecture is organized into six core capability domains:

*   **1. Member Identity & Trust Services**
    *   1.1. Digital KYC/AML (Automated verification, photo ID OCR, selfie match)
    *   1.2. Common Bond Verification (Checking membership criteria eligibility)
    *   1.3. Profile Management (Account limits, security keys, notification preferences)
*   **2. Core Banking Ledger & Treasury**
    *   2.1. Member Share Capital Registry (Tracking non-withdrawable equity and membership status)
    *   2.2. Savings & Transactional Accounts (Withdrawable deposits, interest accretion engines)
    *   2.3. Settlement Gateway (Integration with FedNow, ACH, SEPA, and card networks)
*   **3. Peer-Supported Lending Suite**
    *   3.1. Underwriting Engine (Open banking transaction analysis and scoring)
    *   3.2. Social Loan Circle Registry (Configuring peer-to-peer trust networks, co-signer logic, and collateral locks)
    *   3.3. Document Vault & E-Sign (Secure execution of legal loan agreements)
    *   3.4. Loan Servicing (Repayment scheduling, automated direct debits)
*   **4. Democratic Governance Portal**
    *   4.1. Ballot & Voting Manager (Creating secure polls, resolutions, and board elections)
    *   4.2. Liquid Democracy Engine (Routing proxy delegations, managing revocable trust lines)
    *   4.3. Discussion Forum & Proposals (Collaborative space for drafting local initiatives)
*   **5. Cooperative Dividend Engine**
    *   5.1. Patronage Calculator (Computing returns based on member savings, transactions, and loans)
    *   5.2. Payout Processor (Direct distributions to member savings accounts or share capital reinvestment)
*   **6. Community Impact & Crowdfunding Hub**
    *   6.1. Pitch Desk (Listing community projects seeking funds, grants, or investments)
    *   6.2. Allocation Tracker (Showing project investment performance and real-world impact metrics)
    *   6.3. Micro-Contribution Pipeline (Spare-change roundups and recurring fee donations)

---

## 4. Feature List

The following list outlines key platform features, mapping each to its respective domain capability and target personas.

### Feature A: "Instant-Share" Digital Onboarding
*   **Capability Map:** 1.1 Digital KYC/AML, 2.1 Member Share Capital Registry
*   **Target Personas:** Eco-Conscious Evan, Cooperative Clara
*   **Description:** An onboarding experience that conducts automated identity validation (using facial scans and document OCR). Immediately upon compliance clearance, the interface guides the user to buy their initial mandatory member share ($25 common bond contribution) using standard digital wallets. Once purchased, the system generates their cooperative membership token, instantly unlocking savings and voting rights.

### Feature B: Social Loan Circles (Community-Guaranteed Credit)
*   **Capability Map:** 3.2 Social Loan Circle Registry, 3.4 Loan Servicing
*   **Target Personas:** Cooperative Clara, Community Marcus
*   **Description:** An alternative lending flow where borrowers with non-traditional income can invite 3 to 5 fellow coop members to vouch for their loan application. The system allows vouching members to pledge a portion of their share capital as partial security. This lowers the borrower’s interest rate and expands credit access based on community trust instead of credit scores.

### Feature C: Liquid Democracy / Proxy Routing
*   **Capability Map:** 4.2 Liquid Democracy Engine, 4.1 Ballot & Voting Manager
*   **Target Personas:** Eco-Conscious Evan, Cooperative Clara
*   **Description:** An in-app voting module. Members who do not have time to read detailed policy resolutions can delegate their vote to a trusted member or verified community expert (e.g., delegating green lending decisions to an environmental advocate). The delegation is fully granular, category-specific, and instantly revocable at any time.

### Feature D: Real-Time Patronage Dividend Tracker
*   **Capability Map:** 5.1 Patronage Calculator
*   **Target Personas:** Eco-Conscious Evan, Cooperative Clara
*   **Description:** A dashboard showing the member's financial footprint within the cooperative (total deposits, credit utilized, and transaction volume). It provides a real-time estimate of the member’s projected annual dividend payout, demonstrating how supporting the coop yields individual and collective financial returns.

### Feature E: Community Crowdfunding Hub & Local Bonds
*   **Capability Map:** 6.1 Pitch Desk, 6.2 Allocation Tracker
*   **Target Personas:** Community Marcus, Eco-Conscious Evan
*   **Description:** A crowdfunding platform integrated into the banking app. Registered local organizations can list capital-raising projects (e.g., local solar installations). Members can invest directly from their savings accounts, track the social and financial yields, and vote to allocate a percentage of the bank's collective community grant funds to specific projects.

### Feature F: Ethical Round-Ups for Community Reinvestment
*   **Capability Map:** 6.3 Micro-Contribution Pipeline
*   **Target Personas:** Eco-Conscious Evan
*   **Description:** A transaction-monitoring feature that rounds up every card purchase to the nearest dollar. The difference is accumulated and automatically channeled as micro-investments into member-selected green projects or local development initiatives, displaying live environmental impact metrics inside the app.