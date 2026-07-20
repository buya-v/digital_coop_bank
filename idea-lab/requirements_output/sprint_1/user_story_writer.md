# Sprint 1 User Stories: Digital Coop Bank

This document contains the functional user stories for the **Digital Coop Bank** Sprint 1 MVP scope, prepared by the **User Story Writer**. These stories translate the Business Analyst's Functional Scope into granular, testable, and user-centric units of work aligned with target personas, using the standard template and adhering strictly to the INVEST criteria.

---

## 1. Target User Personas Reference

To maintain a member-first design methodology, the stories are written from the perspectives of our four core personas:
*   **Eco-Conscious Elena** (The Values-Aligned Consumer)
*   **Freelance Fabian** (The Gig Economy Worker)
*   **Community Organizer Chloe** (The Co-op Leader)
*   **Digital Native Daniel** (The Gen Z Tech Enthusiast)

---

## 2. Sprint 1 User Stories by Capability

### Capability 1: Member Identity & Access Management (MIAM)

#### Epic: Frictionless & Secure Digital Onboarding

##### **US-1.1a: Government ID Verification (F-101)**
*   **Story Statement:** As a new member (Elena, Fabian, or Daniel), I want to take a photo of my government-issued ID and upload it through the mobile application so that the bank can verify my identity securely.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   The app triggers the mobile device camera overlay to guide the user in alignment with the document boundaries.
    *   The system accepts JPEG, PNG, and PDF file formats, with a maximum file size limit of 10MB.
    *   The system performs an automated quality check to ensure the text is legible (not blurry) and the photo page is visible, showing a retry prompt if legibility checks fail.
    *   Once uploaded, the status transitions to "ID Uploaded - Awaiting Verification."
*   **INVEST Alignment:** 
    *   *Independent:* Can be developed and tested with stubbed backend validation before the liveness check is complete.
    *   *Testable:* Verified by uploading valid, blurry, and oversized image files to check system responses.

##### **US-1.1b: Live Facial Scan & Liveness Check (F-101)**
*   **Story Statement:** As a new member (Daniel), I want to perform a live facial scan during sign-up so that the bank can prove I am physically present and prevent identity fraud.
*   **Relative Complexity:** **L**
*   **Acceptance Criteria:**
    *   The app launches a front-camera interface displaying a circular guide for the user's face.
    *   The user must follow a dynamic prompt (e.g., blink, turn head slightly, or smile) to verify liveness.
    *   The system matches the facial structure of the live scan against the photo on the uploaded government ID with a confidence score threshold of 95% or higher.
    *   If matching fails, the user is given up to 3 attempts before being routed to a manual verification queue.
*   **INVEST Alignment:**
    *   *Small:* Confined specifically to the liveness check module, distinct from document extraction.
    *   *Testable:* Tested by attempting scans under poor lighting, using static photos, and matching non-owners to detect rejection rates.

##### **US-1.3a: View Member Profile & Cooperative Standing (F-102)**
*   **Story Statement:** As a cooperative member (Chloe), I want to view my profile details, join date, and membership tier in one dashboard so that I can monitor my status within the cooperative.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   A profile tab is accessible from the main navigation menu.
    *   Displays full legal name, unique Member ID number, join date (Month, Year), and current tier (e.g., "Founding Member," "Active Shareholder").
    *   Displays a status badge showing if the account is "Verified" (e-KYC complete) or "Pending Verification."
*   **INVEST Alignment:**
    *   *Valuable:* Provides transparency to members about their legal cooperative status.
    *   *Testable:* Verify that a newly registered user displays correct join dates and membership status on login.

---

### Capability 2: Core Accounts & Share Ledger (CASL)

#### Epic: Member Ownership and Micro-Savings Accounts

##### **US-2.1a: Co-op Share Balance & Voting Weight Visibility (F-201)**
*   **Story Statement:** As a member shareholder (Chloe or Fabian), I want to view my Co-op Share Account balance and my corresponding voting weight so that I know my level of equity ownership and democratic influence.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   The dashboard features a distinct card dedicated to "Co-op Shares" alongside regular transactional checking accounts.
    *   Displays total shares owned (denominated in both shares and domestic currency valuation, e.g., "10 Shares ($100.00)").
    *   Includes a tool-tip or information icon explaining the "One Member, One Vote" governance rule (confirming that holding 1 or more shares qualifies for exactly 1 vote).
*   **INVEST Alignment:**
    *   *Negotiable:* The layout, charts, or text representation can be iterated on based on user feedback.
    *   *Testable:* Assert that the UI renders the correct share balance and voting weight status based on database ledger records.

##### **US-2.1b: Initial Share Purchase during Onboarding (F-201)**
*   **Story Statement:** As a newly verified member (Elena), I want to purchase my initial cooperative membership shares so that my account is fully activated and I obtain voting rights.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   During the final stage of onboarding, the user is prompted to buy the mandatory baseline share (e.g., $10 minimum share value).
    *   The interface allows linking an external debit card or bank account via instant transfer.
    *   Upon successful payment processing, the Co-op Share Ledger updates in real-time, assigning the user 1 share.
    *   The membership status updates from "Pending Capitalization" to "Active Shareholder" with immediate activation of voting permissions.
*   **INVEST Alignment:**
    *   *Valuable:* Ensures the cooperative receives its base equity capital while granting the user immediate membership rights.
    *   *Testable:* Complete a transaction using mock card inputs and verify that the share ledger registers the new share entry.

##### **US-2.3a: Toggle Smart Savings Round-Ups (F-202)**
*   **Story Statement:** As a cardholder (Daniel), I want to enable and configure automated transaction round-ups in my savings settings so that I can accumulate micro-savings effortlessly.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   A simple toggle is provided in the Savings Goal settings page to "Enable Smart Savings Round-Ups."
    *   The user can select the round-up threshold (e.g., round to the nearest $1.00, $2.00, or $5.00).
    *   The user can designate a specific "Smart Savings Goal Account" (e.g., "Rainy Day Pool" or "Elena's Green Initiative") to receive the accumulated round-up amounts.
*   **INVEST Alignment:**
    *   *Independent:* The UI toggle and configuration parameters can be built and tested independently of the transaction engine.
    *   *Testable:* Toggle the switch and modify parameters, checking that the new config values are updated in the user preferences database.

##### **US-2.3b: Automated Transfer of Round-Up Amounts (F-202)**
*   **Story Statement:** As a member with round-ups enabled (Elena), I want the system to automatically round up my card purchases and transfer the differences to my savings goal so that my savings grow incrementally with my spending.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   Upon authorization of a card purchase, the engine calculates the difference between the purchase amount and the next configured threshold increment. (e.g., a purchase of $4.35 is rounded up to $5.00, calculating a $0.65 difference).
    *   The system executes an internal debit transfer of the difference ($0.65) from the checking account to the designated Smart Savings Goal Account.
    *   Both the purchase and the matching round-up transfer are displayed clearly in the ledger transaction history (e.g., "$4.35 Purchase at Local Grocery" followed by a linked transaction showing "$0.65 Smart Round-Up").
*   **INVEST Alignment:**
    *   *Small:* Focuses purely on calculation and database balance manipulation post-authorization.
    *   *Testable:* Trigger simulated purchase events (e.g., $10.15, $5.00) and verify that the correct round-up transfer is made ($0.85 and $0.00 respectively).

---

### Capability 3: Core Transactions & Payments (CTP)

#### Epic: Instant Payments and Card Management

##### **US-3.1a: Instant Internal Peer-to-Peer Transfer (F-301)**
*   **Story Statement:** As a member (Daniel or Fabian), I want to send money instantly to another bank member using only their username or registered phone number so that I can transfer funds without exchanging sensitive account numbers.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   The P2P search bar allows typing a username (e.g., `@fabian`) or a phone number.
    *   The system queries the internal directory and displays the matching user's profile avatar and partial name (e.g., "Fabian K.") for verification.
    *   The user inputs the amount and taps "Send." The transfer executes instantly (in under 3 seconds) with $0.00 transaction fees.
    *   Both sender and recipient receive immediate in-app notifications and updated account balances.
*   **INVEST Alignment:**
    *   *Valuable:* Solves the need for fast, zero-cost, and non-sensitive transfers.
    *   *Testable:* Search for a real username, verify matching profile card, send a transfer, and check that balances adjust instantly on both accounts.

##### **US-3.1b: Downloadable Transaction Confirmation Receipt (F-301)**
*   **Story Statement:** As a transaction sender (Fabian), I want to access a digital confirmation receipt for any completed transaction so that I can share proof of payment with external parties.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   Every transaction detail screen contains a button to "Share Receipt" or "Download PDF Receipt."
    *   The receipt displays: Transaction Date/Time, Reference ID, Sender Name/ID, Recipient Name/ID, Amount, Fee ($0.00), and a "Digital Coop Bank Verified" watermark.
    *   The generated PDF is optimized for mobile sharing (compatible with iOS/Android native share sheets).
*   **INVEST Alignment:**
    *   *Negotiable:* Formatting and layout of the PDF document can change depending on branding requirements.
    *   *Testable:* Generate receipt for a transfer and verify PDF outputs matching layout specs and containing accurate transaction metadata.

##### **US-3.3a: Generate Instant Virtual Debit Card (F-302)**
*   **Story Statement:** As an online shopper (Fabian or Daniel), I want to instantly generate a virtual debit card linked to my checking account so that I can make online purchases securely.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   From the "Cards" tab, the user can select "Create Virtual Card."
    *   The system prompts the user to enter their account PIN or authenticate using biometrics.
    *   The screen displays a mock card with a unique 16-digit card number, expiration date, and CVV code.
    *   The virtual card is linked to the primary checking account balance for authorization queries.
*   **INVEST Alignment:**
    *   *Independent:* Can be developed using mock authorization engines before integration with global card networks (e.g., Visa/Mastercard sandbox APIs).
    *   *Testable:* Create card, check that details display correctly, and copy credentials to clipboard.

##### **US-3.3b: Temporarily Freeze and Unfreeze Virtual Card (F-302)**
*   **Story Statement:** As a cardholder (Daniel), I want to freeze and unfreeze my virtual debit card instantly via the app so that I can prevent unauthorized transactions when the card is not in use.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   The virtual card dashboard shows a prominent "Freeze Card" toggle switch.
    *   When the card status is set to "Frozen," any incoming authorization request is automatically declined with a "Card Blocked" transaction response.
    *   Toggling the switch back to "Unfrozen" instantly restores the card's active state for online purchases.
*   **INVEST Alignment:**
    *   *Small:* Focuses on editing a single boolean flag (`is_frozen`) on the card database record and validating it during authorization.
    *   *Testable:* Attempt to process a mock transaction when frozen (should fail) and when unfrozen (should succeed).

---

### Capability 4: Embedded Democratic Governance (EDG)

#### Epic: Mobile-First In-App Democratic Voting

##### **US-4.2a: Browse Active Cooperative Proposals (F-401)**
*   **Story Statement:** As a cooperative member (Chloe or Elena), I want to browse a list of open proposals and review their details so that I can make informed voting decisions.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   A "Governance" or "Voting Portal" is accessible from the main dashboard navigation.
    *   The portal displays a list of active proposals showing: Title, Short Description, Category (e.g., "Community Grant," "Operating Rules"), Closing Date/Time, and Current Turnout percentage.
    *   Filters are available to show "Active," "Voted On," and "Closed" proposals.
*   **INVEST Alignment:**
    *   *Independent:* Can be completed using read-only proposal databases, independent of the transaction-secured voting engine.
    *   *Testable:* Assert that the UI filters proposals accurately by status and displays all metadata fields.

##### **US-4.2b: Secure Vote Submission (F-401)**
*   **Story Statement:** As a shareholder member (Elena), I want to securely submit my vote on an active proposal so that my voice is represented in the cooperative's decisions.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   On a proposal detail screen, the user is presented with three options: "For," "Against," and "Abstain."
    *   Tapping "Submit Vote" requests biometric or PIN re-authentication to prevent unauthorized device actions.
    *   Upon authentication, the system records the vote, increments the global proposal tally, and marks the user as "Voted" on this specific proposal ID to prevent double voting.
    *   The screen updates to show a "Thank You for Voting" confirmation and displays the live aggregate results (if configured to show).
*   **INVEST Alignment:**
    *   *Valuable:* Preserves democratic integrity through double-voting prevention and authentication.
    *   *Testable:* Attempt to vote twice on the same proposal using the same member credentials and verify that the system blocks the duplicate.

---

### Capability 5: Community Lending & Trust Networks (CLTN)

#### Epic: Accessible Community-Led Capital

##### **US-5.1a: Apply for Co-op Microloan (F-502)**
*   **Story Statement:** As a self-employed member (Fabian), I want to apply for a small, short-term microloan through the app so that I can quickly finance my business activities.
*   **Relative Complexity:** **L**
*   **Acceptance Criteria:**
    *   The user accesses the "Loans" hub and selects "Apply for Microloan."
    *   The interface allows inputting the requested loan amount (up to the MVP cap of $1,000) and selecting repayment terms (e.g., 3, 6, or 12 months).
    *   The UI dynamic calculator displays the estimated monthly payment and interest rate.
    *   The application process prompts the user to input a brief description of the loan purpose (e.g., "Camera Equipment" or "Office Space Rent").
    *   Upon submission, the request enters the cooperative underwriting queue.
*   **INVEST Alignment:**
    *   *Valuable:* Connects members to quick, non-exploitative capital.
    *   *Testable:* Complete a loan application with valid inputs and confirm that the request is successfully saved in the backend loans database with a "Pending Review" status.

##### **US-5.1b: Pre-Screening & Automated Interest Estimation (F-502)**
*   **Story Statement:** As a loan applicant (Fabian), I want to see an automated estimate of my interest rate based on my cooperative engagement metrics so that I can see the financial reward of my active participation.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   Before submitting a loan application, the system evaluates the user's cooperative metrics: Account tenure, Co-op Share Account balance, Average savings balance, and historical Governance voting participation.
    *   The algorithm assigns a cooperative health score and calculates a corresponding interest rate discount (e.g., base interest of 8% reduced down to a minimum of 4% based on high engagement).
    *   The screen displays a breakdown explaining the discount (e.g., "-1% for voting in all recent proposals," "-1% for maintaining active savings").
*   **INVEST Alignment:**
    *   *Negotiable:* The scoring weight parameters (savings vs. voting) can be tuned without rewriting the user interface.
    *   *Testable:* Simulate different member histories (e.g., new member vs. long-term voter) and verify that the dynamic calculator output matches the interest scoring rules.

---

### Capability 6: Dynamic Dividend Engine (DDE)

#### Epic: Real-Time Yield Tracking

##### **US-6.3a: View Cumulative Savings Yield (F-602)**
*   **Story Statement:** As a saving member (Daniel), I want to view my accrued savings interest in an interactive graph so that I can see my capital growth over time.
*   **Relative Complexity:** **S**
*   **Acceptance Criteria:**
    *   The Yield Tracker screen features a clean line or bar chart showing interest payouts over time (monthly and year-to-date views).
    *   Displays a numerical value for "Total Interest Earned Year-to-Date" and "Last Month's Payout."
    *   The UI must render correctly on multiple mobile screen sizes, featuring tooltips when points on the graph are tapped.
*   **INVEST Alignment:**
    *   *Negotiable:* Front-end visualization design can use different charting library options.
    *   *Testable:* Assert that interest payout arrays from the API are mapped and rendered accurately on the coordinate system of the graph.

##### **US-6.3b: Estimated Cooperative Dividends Projection (F-602)**
*   **Story Statement:** As a shareholder member (Elena), I want to view a projection of my upcoming quarterly dividend payout based on my current cooperative contribution metrics so that I can see the direct benefits of membership.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   The dividend dashboard displays an "Estimated Upcoming Dividend" value.
    *   The estimation engine pulls current data from the Cooperative Revenue Pool and calculates the member's share based on current shares owned and voting activity score.
    *   Includes a disclaimer stating: "Projections are based on current cooperative earnings and may fluctuate based on quarterly performance."
*   **INVEST Alignment:**
    *   *Independent:* Projections are calculations and do not affect the official ledger balances until the payout date.
    *   *Testable:* Calculate the mock projection manually and compare it with the displayed UI projection value to ensure mathematical parity.

---

### Capability 7: Transparent Capital Ledger (TCL)

#### Epic: Ethical Capital Transparency

##### **US-7.1a: Interactive Capital Ledger Chart (F-701)**
*   **Story Statement:** As an ethical depositor (Elena), I want to view an interactive chart showing the exact allocation of the bank's total capital reserves so that I can verify my deposits are used for ethical and community-centric purposes.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   The ledger screen displays an interactive donut or pie chart representing the total assets under management.
    *   Data is categorized into four segments: Green Bonds, Local Business Loans, Community Infrastructure, and Cash Liquidity Reserves.
    *   Displays percentage values and raw dollar amounts on each segment (e.g., "Green Bonds: 35% ($8.75M)").
    *   The chart pulls live summary data from the ledger, cached and updated weekly.
*   **INVEST Alignment:**
    *   *Independent:* Visual rendering is independent of granular underlying sub-ledgers.
    *   *Testable:* Verify that the sum of the percentages displayed on the chart equals exactly 100% and totals the cooperative assets under management.

##### **US-7.1b: Capital Project Spotlights & Details (F-701)**
*   **Story Statement:** As a member (Elena), I want to drill down into a capital allocation category to view profiles of the specific projects funded by the cooperative so that I can see the real-world impact of my money.
*   **Relative Complexity:** **M**
*   **Acceptance Criteria:**
    *   Tapping on a segment of the Capital Ledger Chart (e.g., "Local Business Loans") highlights the segment and displays a list of funded project cards below.
    *   Each card contains: Project Name (or anonymized identifier, e.g., "Organic Farm Expansion"), Short Impact Description, Location, and Total Funded Amount.
    *   Tapping on a card opens a modal containing a rich-text story detail and a link to the project's web presence if applicable.
*   **INVEST Alignment:**
    *   *Valuable:* Provides validation of ethical claims, which is key for Values-Aligned consumers.
    *   *Testable:* Tap on different ledger segments to confirm correct project cards filter and display relevant details in the modal.

---

## 3. Sprint 1 MVP User Stories Complexity & Persona Matrix

Below is a summary mapping of the user stories, their targeted personas, and relative complexities.

| Story ID | Capability / Feature | Story Title | Primary Persona | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **US-1.1a** | 1.1 Onboarding / F-101 | Government ID Verification | Elena, Fabian, Daniel | **M** |
| **US-1.1b** | 1.1 Onboarding / F-101 | Live Facial Scan & Liveness Check | Daniel | **L** |
| **US-1.3a** | 1.3 Profile / F-102 | View Member Profile | Chloe | **S** |
| **US-2.1a** | 2.1 Shares / F-201 | Co-op Share & Vote Weight View | Chloe, Fabian | **S** |
| **US-2.1b** | 2.1 Shares / F-201 | Initial Share Purchase | Elena | **M** |
| **US-2.3a** | 2.3 Micro-Savings / F-202| Toggle Smart Savings Round-Ups | Daniel | **S** |
| **US-2.3b** | 2.3 Micro-Savings / F-202| Automated Transfer of Round-Up | Elena | **M** |
| **US-3.1a** | 3.1 P2P Transfers / F-301 | Instant P2P Transfer | Daniel, Fabian | **M** |
| **US-3.1b** | 3.1 P2P Transfers / F-301 | PDF Transaction Receipt | Fabian | **S** |
| **US-3.3a** | 3.3 Card Mgmt / F-302 | Generate Virtual Card | Fabian, Daniel | **M** |
| **US-3.3b** | 3.3 Card Mgmt / F-302 | Freeze/Unfreeze Virtual Card | Daniel | **S** |
| **US-4.2a** | 4.2 Voting Engine / F-401 | Browse Active Proposals | Chloe, Elena | **S** |
| **US-4.2b** | 4.2 Voting Engine / F-401 | Secure Vote Submission | Elena | **M** |
| **US-5.1a** | 5.1 Microloans / F-502 | Apply for Co-op Microloan | Fabian | **L** |
| **US-5.1b** | 5.1 Microloans / F-502 | Automated Interest Estimate | Fabian | **M** |
| **US-6.3a** | 6.3 Yield Tracker / F-602 | View Cumulative Savings Yield | Daniel | **S** |
| **US-6.3b** | 6.3 Yield Tracker / F-602 | Projected Dividend View | Elena | **M** |
| **US-7.1a** | 7.1 Capital Ledger / F-701| Interactive Capital Chart | Elena | **M** |
| **US-7.1b** | 7.1 Capital Ledger / F-701| Capital Project Spotlights | Elena | **M** |

---

### Sprint 1 Total Story Point Allocation Estimate:
*   **Small (S):** 7 Stories
*   **Medium (M):** 10 Stories
*   **Large (L):** 2 Stories
*   **Extra Large (XL):** 0 Stories (all XL epics broken down to satisfy INVEST)

This completes the User Story mapping for the Sprint 1 MVP scope. All functional requirements from the Business Requirements Document have been converted into granular, developer-ready user stories that ensure visual, ethical, and interactive success metrics.