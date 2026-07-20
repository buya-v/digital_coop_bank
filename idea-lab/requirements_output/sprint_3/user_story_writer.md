# User Stories: Digital Coop Bank (Sprint 3)

As the User Story Writer, I have translated the high-level features from the Business Analyst’s Functional Scope into granular, user-centric user stories. Each user story is organized by Epic/Capability, mapped to our target personas, assigned a relative complexity (T-shirt size), and detailed with concrete Acceptance Criteria to satisfy the INVEST criteria.

---

## Epic 1: Member & Identity Management (MIM)

### Story MIM-1: Automated Identity & Address Verification (eKYC)
*   **User Story:** As a **Frictionless Banking Advocate (Persona B)**, I want to verify my identity and address automatically in under 8 minutes so that I can immediately start using the banking platform.
*   **Persona:** Frictionless Banking Advocate (Persona B)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:** 
    *   *Independent:* Can be built and integrated with KYC providers independently of internal ledger details.
    *   *Valuable:* Directly addresses the neobank devotee's expectation of a rapid, low-friction onboarding experience.
    *   *Testable:* Verified by checking successful API responses and onboarding times.
*   **Acceptance Criteria:**
    1.  The user can scan their government-issued photo ID and perform a live biometric facial scan.
    2.  The system automatically extracts data from the ID and runs real-time verification checks (KYC/AML) via external API integrations.
    3.  Upon success, the user is immediately transitioned to the account-creation stage.
    4.  If verification fails or requires manual review, the user is notified of the specific issue and provided clear instructions on next steps.

### Story MIM-2: Automatic Cooperative Share Allocation
*   **User Story:** As a **Values-Driven Saver (Persona A)**, I want my mandatory cooperative share to be automatically purchased and registered upon onboarding approval so that I am legally recognized as a member-owner of the cooperative.
*   **Persona:** Values-Driven Saver (Persona A)
*   **T-Shirt Size:** Small (S)
*   **INVEST Alignment:**
    *   *Independent:* Relies on onboarding approval but functions as a distinct step in the registration workflow.
    *   *Valuable:* Legally establishes membership, which is a prerequisite for voting and receiving dividends.
    *   *Testable:* Checked by verifying the ledger update and member share certificate generation.
*   **Acceptance Criteria:**
    1.  Immediately upon eKYC approval, the system must reserve one cooperative share ($5 par value) for the member.
    2.  The $5 share purchase is funded via the member's initial deposit.
    3.  The system registers the member in the official cooperative registry with their unique member ID and share ID.
    4.  The user receives a digital share certificate confirming their membership.

---

## Epic 2: Core Accounts & Treasury (CAT)

### Story CAT-1: Group Pot Creation & Multi-Signature Oversight
*   **User Story:** As a **Community Organizer (Persona C)**, I want to create a shared housing savings pot with multi-signature authorization so that group members can collectively pool funds and maintain transparent oversight.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Extra Large (XL)
*   **INVEST Alignment:**
    *   *Independent:* The sub-ledger can be implemented on top of core accounts without altering standard checking accounts.
    *   *Valuable:* Vital for groups, co-housing, and community projects that require shared custody of funds.
    *   *Testable:* Checked by ensuring transfers fail without proper threshold approvals.
*   **Acceptance Criteria:**
    1.  An authorized member can create a "Group Pot" and invite other members using their member IDs.
    2.  The creator can set authorization rules (e.g., "Requires 2 out of 3 signers to approve outbound transfers").
    3.  All group members can view the transaction history and the balance of the pot in real-time.
    4.  The system displays a clear breakdown of each member's individual contribution to the pot.

### Story CAT-2: Joint Transaction Consent Flow
*   **User Story:** As a **Group Pot Member**, I want to receive approval requests for outgoing payments from our shared pot so that I can consent to or reject the transaction before funds leave the account.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* Built as a layer over the group pot, separating the payment trigger from the core transaction engine.
    *   *Valuable:* Prevents unauthorized spending of pooled community funds.
    *   *Testable:* Verified by routing transaction requests through the consent queue.
*   **Acceptance Criteria:**
    1.  When a member initiates an outbound transfer from a Group Pot, the transfer status is set to "Pending Approval."
    2.  All designated signers receive a push notification details of the request (amount, recipient, and purpose).
    3.  Signers can approve or reject the request directly from their mobile app.
    4.  Once the required threshold of approvals is reached, the transaction is executed, and all members are notified.
    5.  If any signer rejects the request and the threshold cannot be met, the transaction is cancelled.

### Story CAT-3: Ethical Yield Allocation
*   **User Story:** As a **Values-Driven Saver (Persona A)**, I want to automatically route a percentage of my interest yield to a designated community project so that my capital supports ethical initiatives.
*   **Persona:** Values-Driven Saver (Persona A)
*   **T-Shirt Size:** Medium (M)
*   **INVEST Alignment:**
    *   *Independent:* Operates during the interest calculation routine without modifying the daily balance calculation.
    *   *Valuable:* Gives ethical consumers direct control over the impact of their savings.
    *   *Testable:* Verified by running an interest payment job and confirming the split distribution.
*   **Acceptance Criteria:**
    1.  The user can access a yield allocator slider in their account settings to choose any percentage between 0% and 100%.
    2.  The user can select a target project from a verified list of active local community initiatives.
    3.  At the end of the interest calculation period, the system calculates the total interest earned.
    4.  The system splits the payment: routing the designated percentage to the community project’s fund and the remainder to the user’s savings account.
    5.  The transaction ledger clearly labels the routed portion as a "Community Yield Donation."

---

## Epic 3: Democratic Governance (DGV)

### Story DGV-1: Policy & Parameter Voting
*   **User Story:** As a **Values-Driven Saver (Persona A)**, I want to cast my vote on proposed credit policy changes and interest rates so that I can influence the cooperative's financial direction.
*   **Persona:** Values-Driven Saver (Persona A)
*   **T-Shirt Size:** Medium (M)
*   **INVEST Alignment:**
    *   *Independent:* Can run on a dedicated voting module that periodically polls active proposals.
    *   *Valuable:* Delivers on the cooperative promise of democratic control over bank operations.
    *   *Testable:* Checked by submitting votes and ensuring tallies update correctly and immutably.
*   **Acceptance Criteria:**
    1.  The user can view a list of active policy proposals (e.g., "Change savings rate to 3.5%" or "Adjust credit risk limits").
    2.  For each proposal, the system displays the current parameter, the proposed change, and the rationale.
    3.  The user can cast one vote ("Yes", "No", or "Abstain").
    4.  The system verifies the user is an active member and records the vote anonymously.
    5.  Once cast, the vote cannot be changed, and the user's status for that proposal changes to "Voted."

### Story DGV-2: Representative Board Elections
*   **User Story:** As a **Community Organizer (Persona C)**, I want to review board candidate profiles and cast my ballot during elections so that I am represented by qualified leaders who share my values.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Medium (M)
*   **INVEST Alignment:**
    *   *Independent:* Can run in parallel with policy voting, sharing the core ballot box engine.
    *   *Valuable:* Empowers members to democratically elect cooperative leadership.
    *   *Testable:* Verified by running a mock election and auditing candidate tallies.
*   **Acceptance Criteria:**
    1.  During an active election window, the user is presented with the ballot containing candidate profiles, photos, and statements.
    2.  The user can select their preferred candidates up to the maximum allowed seats.
    3.  The user submits the ballot securely.
    4.  The system issues a cryptographic confirmation token to the user for ballot verification.
    5.  Once the election closes, the system publishes the aggregated results on the voting portal.

### Story DGV-3: Member Proposal Builder & Signature Gathering
*   **User Story:** As a **Community Organizer (Persona C)**, I want to draft a policy proposal and gather digital signatures from members so that it can be formally submitted to the general membership for voting.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* Proposals exist as drafts in a community workspace before entering the core voting queue.
    *   *Valuable:* Fosters grass-roots initiative creation by letting members dictate the legislative agenda.
    *   *Testable:* Checked by verifying signature aggregation and automatic proposal promotion.
*   **Acceptance Criteria:**
    1.  The user can write a proposal title, summary, detailed body, and select a predefined policy category.
    2.  The proposal is saved as "Draft" and published to a public community board for member review.
    3.  Other verified members can view the draft and digitally sign their support.
    4.  The system tracks the signature count and displays a progress bar toward the target threshold (e.g., 500 signatures).
    5.  Upon reaching the threshold, the proposal is automatically marked as "Submitted" and sent to the board for review and scheduling on the next general ballot.

---

## Epic 4: Peer-Supported Lending (PSL)

### Story PSL-1: Lending Circle Setup & Enrollment
*   **User Story:** As a **Flexible Earner (Persona D)**, I want to join a rotating savings and credit group (ROSCA) with other members so that I can access interest-free loan pools through cooperative savings.
*   **Persona:** Flexible Earner (Persona D)
*   **T-Shirt Size:** Extra Large (XL)
*   **INVEST Alignment:**
    *   *Independent:* The ROSCA ledger sits alongside individual savings accounts and can run on its own schedule.
    *   *Valuable:* Provides access to capital for gig workers and freelancers without standard institutional credit checks.
    *   *Testable:* Verified by simulating a multi-month savings circle and rotation sequence.
*   **Acceptance Criteria:**
    1.  A group of members can establish a lending circle with set parameters: monthly contribution amount, duration, and participant list.
    2.  The system establishes a rotation schedule (either randomized or agreed upon by participants) detailing when each member receives the payout.
    3.  On the designated monthly date, the system automatically pulls the contribution from each participant's account and pools it.
    4.  The system automatically pays the collected lump sum to the scheduled beneficiary of the month.
    5.  If a participant fails to make a payment, the system alerts the circle and initiates risk-matching procedures from secondary collateral.

### Story PSL-2: Peer Guarantee Collateral Locking
*   **User Story:** As a **Flexible Earner (Persona D)**, I want to ask a peer to guarantee my loan using their savings balance as collateral so that I can qualify for a lower interest rate on my borrowing.
*   **Persona:** Flexible Earner (Persona D)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* Collateral locking runs within the loan contract layer, holding savings without moving funds immediately.
    *   *Valuable:* Allows credit-challenged individuals to access fair rates through social relationships.
    *   *Testable:* Verified by creating a loan request, accepting the guarantee, and checking locked funds.
*   **Acceptance Criteria:**
    1.  A loan applicant can input the member ID of a guarantor and the requested guarantee amount.
    2.  The guarantor receives an in-app request detailing the loan terms, interest reduction, and collateral risks.
    3.  Upon guarantor approval, the system freezes the guarantee amount in the guarantor's savings account.
    4.  The borrower's loan interest rate is adjusted down based on the guaranteed portion.
    5.  As the borrower pays down the principal, the system releases the corresponding locked collateral back to the guarantor.

---

## Epic 5: Community & Impact Funding (CIF)

### Story CIF-1: Community Project Crowdfunding
*   **User Story:** As a **Community Organizer (Persona C)**, I want to list a community development project on the portal so that other members can donate directly to fund the initiative.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* Project funding operates as a crowdfunding ledger distinct from daily consumer transactions.
    *   *Valuable:* Directly matches community needs with values-driven member capital.
    *   *Testable:* Verified by posting projects and processing test member contributions.
*   **Acceptance Criteria:**
    1.  The user can submit a project proposal with a title, description, budget goal, deadline, and proof of community impact.
    2.  Once approved by the community review process, the project is published on the portal.
    3.  Members can select a project and authorize a one-time or recurring contribution from their checking or savings account.
    4.  The portal shows the real-time funding progress toward the goal.
    5.  If the project does not reach its goal by the deadline, contributions are refunded to the respective donors.

### Story CIF-2: Surplus Treasury Grant Matching
*   **User Story:** As a **Community Organizer (Persona C)**, I want my community project to receive matching funds from the bank's surplus treasury so that we can reach our funding goals faster.
*   **Persona:** Community Organizer (Persona C)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* The matching engine connects to the surplus ledger and triggers on member donation events.
    *   *Valuable:* Amplifies member donations using the institutional strength of the cooperative bank.
    *   *Testable:* Verified by testing if a $10 donation from a member triggers an automated $10 matching deposit from the surplus account.
*   **Acceptance Criteria:**
    1.  The system determines if a project is eligible for matching grants based on the bank's active matching rules.
    2.  When a member donates to an eligible project, the matching engine calculates a 1:1 match.
    3.  The system transfers the matching amount from the bank's surplus matching treasury to the project fund.
    4.  The system halts matching for a project if the bank's matching cap for that project is met, or if the overall quarterly matching treasury budget is exhausted.

### Story CIF-3: Impact & Investment Ledger Dashboard
*   **User Story:** As a **Values-Driven Saver (Persona A)**, I want to see a live visual dashboard showing the social and environmental metrics of the bank’s investment portfolio so that I know my deposits are doing good.
*   **Persona:** Values-Driven Saver (Persona A)
*   **T-Shirt Size:** Medium (M)
*   **INVEST Alignment:**
    *   *Independent:* Dashboard is a read-only reporting service drawing from aggregated loan and donation databases.
    *   *Valuable:* Provides transparency and validates the ethical status of the bank.
    *   *Testable:* Checked by verifying that data matches database totals for metrics like local housing units or carbon offset.
*   **Acceptance Criteria:**
    1.  The app features a visual "Impact Dashboard" displaying key metrics (e.g., carbon offset, local jobs created, affordable housing units built).
    2.  The metrics are updated dynamically as loans are funded and community projects are completed.
    3.  The dashboard provides a personalized view showing the proportional impact of the user’s own balance.
    4.  The user can drill down to read stories and details about the specific organizations and projects funded.

---

## Epic 6: Dividend Management & Allocation (DMA)

### Story DMA-1: Projected Dividend Dashboard
*   **User Story:** As a **Frictionless Banking Advocate (Persona B)**, I want to view my projected annual dividend dynamically in real-time so that I can see the financial benefit of my active participation in the cooperative.
*   **Persona:** Frictionless Banking Advocate (Persona B)
*   **T-Shirt Size:** Medium (M)
*   **INVEST Alignment:**
    *   *Independent:* Computes values using read-only inputs from member balances, transaction history, and overall bank performance.
    *   *Valuable:* Keeps members engaged with the cooperative model by displaying tangible financial rewards.
    *   *Testable:* Verified by modifying a mock user's deposits and validating the updated dividend projections.
*   **Acceptance Criteria:**
    1.  The dashboard displays the cooperative's total net surplus and growth trends for the current financial year.
    2.  The system calculates the member's dividend estimate based on their average deposit balance, active loans, and voting history.
    3.  The user can view a breakdown showing how their dividend allocation was calculated.
    4.  Projections are recalculated and refreshed at least once daily.

### Story DMA-2: Automated Dividend Disbursal
*   **User Story:** As a **Flexible Earner (Persona D)**, I want my annual dividend payment to be deposited directly into my savings account once approved so that I don't have to manually claim or track it.
*   **Persona:** Flexible Earner (Persona D)
*   **T-Shirt Size:** Large (L)
*   **INVEST Alignment:**
    *   *Independent:* Runs on an automated ledger task triggered by budget approval, executing disbursements in batches.
    *   *Valuable:* Eliminates admin overhead and delivers returns to members without delays.
    *   *Testable:* Verified by executing a test distribution run and checking recipient balances.
*   **Acceptance Criteria:**
    1.  Once the annual budget and dividend distribution percentages are democratically approved by vote, the disbursal job is scheduled.
    2.  The system calculates the final pro-rata dividend amount for every registered member.
    3.  The system posts the dividend transaction directly to the member's primary savings account.
    4.  The member receives a notification detailing the payout amount and a downloadable tax statement.
    5.  The system updates the Cooperative Share Registry to log the payout date and amount for compliance records.

---

## Summary of Story Estimations

The following table summarizes the distribution of story sizes across all Epic domains to support sprint planning:

| Epic | Story Reference | T-Shirt Size | Main Target Persona |
| :--- | :--- | :---: | :--- |
| **MIM** | MIM-1: Automated Identity & Address Verification (eKYC) | **L** | Persona B (Neobank Devotee) |
| **MIM** | MIM-2: Automatic Cooperative Share Allocation | **S** | Persona A (Ethical Consumer) |
| **CAT** | CAT-1: Group Pot Creation & Multi-Signature Oversight | **XL** | Persona C (Community Organizer) |
| **CAT** | CAT-2: Joint Transaction Consent Flow | **L** | Persona C (Community Organizer) |
| **CAT** | CAT-3: Ethical Yield Allocation | **M** | Persona A (Ethical Consumer) |
| **DGV** | DGV-1: Policy & Parameter Voting | **M** | Persona A (Ethical Consumer) |
| **DGV** | DGV-2: Representative Board Elections | **M** | Persona C (Community Organizer) |
| **DGV** | DGV-3: Member Proposal Builder & Signature Gathering | **L** | Persona C (Community Organizer) |
| **PSL** | PSL-1: Lending Circle Setup & Enrollment | **XL** | Persona D (Flexible Earner) |
| **PSL** | PSL-2: Peer Guarantee Collateral Locking | **L** | Persona D (Flexible Earner) |
| **CIF** | CIF-1: Community Project Crowdfunding | **L** | Persona C (Community Organizer) |
| **CIF** | CIF-2: Surplus Treasury Grant Matching | **L** | Persona C (Community Organizer) |
| **CIF** | CIF-3: Impact & Investment Ledger Dashboard | **M** | Persona A (Ethical Consumer) |
| **DMA** | DMA-1: Projected Dividend Dashboard | **M** | Persona B (Neobank Devotee) |
| **DMA** | DMA-2: Automated Dividend Disbursal | **L** | Persona D (Flexible Earner) |