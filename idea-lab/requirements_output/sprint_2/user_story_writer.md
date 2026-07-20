# User Stories & Agile Backlog: Digital Coop Bank (Sprint 2)

This document contains the functional user stories for Sprint 2 of the Digital Coop Bank platform. These stories translate high-level features into granular, user-centric deliverables, organized by Epic/Capability. Each story is designed to align with the INVEST criteria (Independent, Negotiable, Valuable, Estimable, Small, Testable) and includes T-shirt sizing for relative complexity.

---

## Epic 1: Member Identity & Onboarding ("Instant-Share" Onboarding)
*Focuses on removing onboarding friction, executing automated KYC, and capturing the initial member share contribution to grant voting rights.*

### Story 1.1: Automated Identity Verification (eKYC)
* **User Story:** As an **Eco-Conscious Evan**, I want to verify my identity digitally using my photo ID and a selfie so that I can open an account securely without visiting a physical branch.
* **Relative Complexity:** L
* **Acceptance Criteria:**
  1. The user can capture or upload a clear photo of a government-issued photo ID (driver's license or passport).
  2. The system performs Optical Character Recognition (OCR) to extract the name, date of birth, ID number, and address.
  3. The system prompts the user to perform a live selfie scan featuring liveness detection (preventing spoofing with photos/videos).
  4. The system compares the selfie with the photo ID and returns an instant pass, fail, or manual review pending state based on a confidence threshold.
  5. The KYC status is recorded on the member's profile.

### Story 1.2: Mandatory Member Share Purchase
* **User Story:** As an **Eco-Conscious Evan**, I want to purchase my initial $25 mandatory member share using standard digital payment methods so that I can validate my common bond eligibility and complete my membership.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. Upon passing KYC, the user is navigated to a payment gateway interface to complete their common bond capital contribution.
  2. The system supports payment through debit/credit cards and integrated digital wallets (Apple Pay and Google Pay).
  3. The $25 transaction is routed specifically to the Member Share Capital Ledger.
  4. The capital is designated as non-withdrawable equity on the ledger.
  5. A receipt is generated and emailed to the member with a copy of the cooperative bylaws.

### Story 1.3: Cooperative Membership Token Generation
* **User Story:** As a **Cooperative Clara**, I want to receive a secure cooperative membership token upon share purchase so that my voting rights are unlocked and my savings account is active.
* **Relative Complexity:** S
* **Acceptance Criteria:**
  1. Upon successful verification and share purchase, the ledger registers the user as an active cooperative member.
  2. The system issues a unique, secure cooperative membership token (membership ID).
  3. The member's status is updated to "Active Member" in the identity service.
  4. The mobile application unlocks access to the Governance and Savings Account portals, which were previously locked during the onboarding flow.

---

## Epic 2: Peer-Supported Lending (Social Loan Circles)
*Focuses on establishing community-vouched lending mechanisms that leverage social trust and cooperative capital over rigid credit scoring.*

### Story 2.1: Social Loan Circle Creation & Invitation
* **User Story:** As a **Cooperative Clara**, I want to create a Social Loan Circle and invite 3 to 5 fellow cooperative members to join so that they can vouch for my loan application.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The borrower can start a new "Social Loan Circle" from the loan application dashboard.
  2. The borrower can search for active cooperative members using their unique member ID, phone number, or email address.
  3. The system sends an in-app and push notification to invited members, detailing the borrower's request.
  4. The circle is marked as "Formed" once a minimum of 3 and a maximum of 5 invited members accept the invitation.

### Story 2.2: Pledging Share Capital as Security
* **User Story:** As a **Community Marcus**, I want to pledge a portion of my share capital as security for a member in my Social Loan Circle so that they can secure a loan.
* **Relative Complexity:** L
* **Acceptance Criteria:**
  1. A circle guarantor can view the borrower's requested loan amount, proposed interest rate, and repayment schedule.
  2. The guarantor can specify an amount of their own savings or share capital to pledge as backing (up to their current available balance).
  3. The pledged amount is immediately placed in a collateral hold state (locked from withdrawal or transfer).
  4. The system presents a legal agreement detailing the risk of default and collateral liquidation, requiring a digital signature to complete the pledge.

### Story 2.3: Community-Guaranteed Underwriting & Dynamic Pricing
* **User Story:** As a **Cooperative Clara**, I want my loan interest rate to decrease based on the amount of community capital pledged so that I can access affordable credit.
* **Relative Complexity:** L
* **Acceptance Criteria:**
  1. The underwriting engine calculates the total value of pledged collateral in the borrower's Social Loan Circle.
  2. The system applies a tiered interest rate discount to the loan rate based on the percentage of the loan covered by the community's collateral pledges.
  3. The system generates the final customized loan offer, highlighting the regular rate versus the community-guaranteed discounted rate.
  4. The borrower can review, accept, and digitally sign the finalized loan agreement.

---

## Epic 3: Democratic Governance (Liquid Democracy & Proxy Routing)
*Enables in-app democratic participation through secure voting and category-specific revocable delegation.*

### Story 3.1: Ballot Management and Direct Voting
* **User Story:** As an **Eco-Conscious Evan**, I want to view active cooperative resolutions and cast my vote directly in the app so that I can participate in democratic decisions.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The user can access a "Governance" tab listing all active ballots, deadlines, resolution texts, and community discussion threads.
  2. The system checks that the member holds an active membership token to authorize voting.
  3. The user can select a voting option (e.g., Yes, No, Abstain) and submit their choice.
  4. The vote is logged securely in the ledger under the "one member, one vote" protocol.
  5. The UI updates to show the ballot status as "Voted" and displays the current aggregate live results (if permitted by the ballot rules).

### Story 3.2: Category-Specific Proxy Delegation
* **User Story:** As a **Cooperative Clara**, I want to delegate my voting power for specific categories to a trusted community expert so that my voice is represented even when I am too busy to vote.
* **Relative Complexity:** L
* **Acceptance Criteria:**
  1. The user can navigate to the "Delegation Settings" and view policy categories (e.g., Green Lending Policy, Treasury Reserve Ratios, Community Grants).
  2. The user can search for a registered proxy or input the member ID of a trusted peer.
  3. The user can choose to delegate their vote specifically for that category.
  4. The system routes the user's vote weight to the designated proxy for any active or future ballots under that category.

### Story 3.3: Proxy Revocation and Direct Overrides
* **User Story:** As a **Cooperative Clara**, I want to revoke my proxy delegation or override a delegated vote on an individual ballot so that I retain final control over my democratic rights.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The user can view a list of active delegations and click a "Revoke Delegation" button to instantly restore direct voting power for that category.
  2. For an active ballot where a proxy has already cast a vote on the member's behalf, the member can open the ballot and cast a direct vote.
  3. The system automatically voids the proxy-cast vote for that specific ballot and registers the member's direct vote.
  4. The aggregate vote counts are updated dynamically.

---

## Epic 4: Cooperative Dividends (Real-Time Patronage Tracker)
*Introduces transparent dividend calculation based on member participation and transactional footprint.*

### Story 4.1: Patronage Footprint Dashboard
* **User Story:** As an **Eco-Conscious Evan**, I want to view a breakdown of my financial contributions to the cooperative so that I understand my patronage value.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The dashboard displays a visual breakdown of the member's financial interactions with the bank for the fiscal year.
  2. The metrics tracked must include: average savings balance, total interest paid on loans, and overall card transaction volume.
  3. The dashboard explains how each financial metric impacts the bank's surplus and the member's individual dividend return.
  4. The data is updated daily based on core ledger entries.

### Story 4.2: Real-Time Dividend Estimator
* **User Story:** As a **Cooperative Clara**, I want to see a real-time estimate of my projected annual dividend payout so that I am motivated to keep my savings and borrowing within the coop.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The system calculates the projected annual dividend using the member's patronage footprint and current cooperative profitability forecasts.
  2. The interface displays a projection model (showing conservative, expected, and high-performance dividend scenarios).
  3. The system displays contextual suggestions on how to increase the dividend (e.g., "Directing $200 more to savings could increase your estimated annual dividend by $12").

---

## Epic 5: Community Crowdfunding & Investments (Community Crowdfunding Hub)
*Provides a marketplace for funding local, high-impact projects through member deposits and grants.*

### Story 5.1: Listing Community Projects (Pitch Desk)
* **User Story:** As a **Community Marcus**, I want to submit a capital-raising project for my local non-profit so that cooperative members can review and invest in it.
* **Relative Complexity:** L
* **Acceptance Criteria:**
  1. A verified organization or community representative can access the "Pitch Desk Creator" tool.
  2. The creator can input project title, description, target funding goal, execution timeline, expected financial/social yield, and upload supporting documents.
  3. The project is submitted to a bank administrator review queue.
  4. Once approved, the project is published live to the in-app Community Crowdfunding Hub.

### Story 5.2: Direct Investment from Savings
* **User Story:** As an **Eco-Conscious Evan**, I want to invest funds directly from my savings account into a community project so that I can earn local impact yields.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The user can select an active project in the Community Crowdfunding Hub and click "Invest".
  2. The user inputs an investment amount, which is validated against their available savings balance.
  3. The system locks the funds from the user's savings and transfers them to the project's escrow account.
  4. The system issues a digital investment certificate detailing the terms, yields, and targeted maturity date.

### Story 5.3: Democratic Community Grant Allocation
* **User Story:** As an **Eco-Conscious Evan**, I want to vote on how the bank's collective community grant funds are allocated among local projects so that I can influence the bank's social impact.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The system shows the total community grant pool reserved from cooperative surplus.
  2. The governance tab displays a list of pre-vetted projects competing for grant allocations.
  3. Each member is allotted a specific voting weight to distribute across projects.
  4. The system aggregates all member allocations at the end of the voting period and triggers automated disbursements to the winning projects.

---

## Epic 6: Micro-Contributions (Ethical Round-Ups)
*Facilitates micro-investments in green and local initiatives via daily transaction micro-contributions.*

### Story 6.1: Round-Up Activation & Configuration
* **User Story:** As an **Eco-Conscious Evan**, I want to enable card transaction round-ups and choose which green project receives the micro-investments so that I can automate my community impact.
* **Relative Complexity:** S
* **Acceptance Criteria:**
  1. The user can toggle the "Ethical Round-Ups" feature on or off in the account settings.
  2. The user is presented with a list of active community projects or green funds to select as the destination.
  3. The user can set a multiplier (e.g., 1x, 2x, or 3x the round-up amount) or configure a maximum monthly cap.
  4. The configuration parameters are updated and saved to the user's account profile.

### Story 6.2: Automated Round-Up Execution
* **User Story:** As an **Eco-Conscious Evan**, I want the system to calculate the round-up amount for each card purchase and accumulate it so that my micro-contributions are processed efficiently.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. For every cleared card transaction (e.g., $3.45), the system calculates the round-up to the nearest dollar ($0.55).
  2. The system tracks these pending micro-contributions in a temporary ledger balance.
  3. When the accumulated round-ups reach a threshold of $5.00, the system initiates a transfer from the user's transaction account to the designated target project's ledger.
  4. The transfer is recorded on the member's statement as an "Ethical Round-Up Transfer".

### Story 6.3: Live Impact Metrics Dashboard
* **User Story:** As an **Eco-Conscious Evan**, I want to see real-time environmental and social impact metrics from my round-ups so that I can visualize the positive changes I am funding.
* **Relative Complexity:** M
* **Acceptance Criteria:**
  1. The app features an impact dashboard that aggregates all round-up contributions made by the member.
  2. The system translates the monetary amount into tangible impact values (e.g., "CO2 offset", "Trees planted", or "Community solar hours funded") using project-provided conversions.
  3. The dashboard updates dynamically when a round-up transfer clears.
  4. The user is able to share their impact metrics directly to social channels.