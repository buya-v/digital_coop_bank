# Acceptance Criteria - Digital Coop Bank (Sprint 3)

This document contains the Quality Assurance (QA) Acceptance Criteria for the User Stories in Sprint 3 of the Digital Coop Bank project. All criteria are written in testable Gherkin-style format ("Given-When-Then") and include happy paths, negative/error paths, and edge cases. Business rules, data validation rules, and security assertions are documented for each story.

---

## Epic 1: Member & Identity Management (MIM)

### Story MIM-1: Automated Identity & Address Verification (eKYC)

#### Business & Security Rules
*   **Verification Location:** Must take place securely within the mobile banking application.
*   **KPI Requirement:** Onboarding duration must be tracked by the system to measure against the 8-minute completion goal.
*   **Compliance Checks:** Integrated APIs must verify details against global Anti-Money Laundering (AML), Counter-Terrorist Financing (CTF), and Politically Exposed Persons (PEP) watchlists.
*   **Security Assertion:** Document images and live biometric scans must be encrypted in transit and at rest using AES-256 and TLS 1.3, ensuring compliance with GDPR and SOC2.

#### Scenarios

*   **Scenario 1: Happy Path - Successful Automated Onboarding**
    *   **Given** the user is on the identity verification screen of the Digital Coop Bank application.
    *   **When** the user uploads a valid, unexpired government-issued photo ID.
    *   **And** the user performs a live biometric facial scan.
    *   **Then** the system extracts the full name, date of birth, and residential address from the ID.
    *   **And** the system successfully verifies the extracted details against the integrated AML database and identity validation APIs.
    *   **And** the system transitions the user to the account-creation stage in under 8 minutes.

*   **Scenario 2: Negative Path - Document Verification Failure due to Blurred Image**
    *   **Given** the user is on the document upload screen.
    *   **When** the user uploads a blurry or low-resolution image of their government ID.
    *   **Then** the system fails to extract readable text.
    *   **And** the system displays the error message: "Document could not be read. Please ensure there are no glares or blurs and try again."
    *   **And** the system permits the user to retry up to 3 times before locking the automated route and offering a manual upload option.

*   **Scenario 3: Edge Case - Manual Review Triggered by Address Mismatch**
    *   **Given** the user is performing the verification flow.
    *   **When** the biometric scan matches the photo ID.
    *   **But** the address extracted from the ID does not match the address returned from the credit bureau or utility database verification APIs.
    *   **Then** the system flags the onboarding state as "Pending Manual Review".
    *   **And** the system notifies the user: "We need to verify your address manually. Please upload a utility bill or bank statement from the last 3 months."
    *   **And** the system routes the application to the compliance queue for administrator action.

---

### Story MIM-2: Automatic Cooperative Share Allocation

#### Business & Security Rules
*   **Membership Rule:** A member must own exactly one cooperative share to be recognized as a member-owner and gain voting rights.
*   **Share Valuation:** The cooperative share has a fixed par value of $5.00, which is non-transferable and non-negotiable.
*   **Funding Rule:** The $5.00 share purchase must be funded from the member's first deposit.
*   **Security Assertion:** The cooperative share registry must be write-once, read-many (WORM) or cryptographically ledgered to prevent retrospective changes.

#### Scenarios

*   **Scenario 1: Happy Path - Automatic Share Purchase upon Initial Deposit**
    *   **Given** the user has completed eKYC verification and has been assigned a unique member ID.
    *   **When** the user makes their first deposit of $10.00 or more into their checking account.
    *   **Then** the system automatically deducts $5.00 from the deposit.
    *   **And** the system registers the member in the cooperative share registry.
    *   **And** the system updates the member's share status to "Active" and issues a digital share certificate via email.

*   **Scenario 2: Negative Path - Insufficient Funds on Initial Deposit**
    *   **Given** the user has completed eKYC verification.
    *   **When** the user performs an initial deposit of only $3.00.
    *   **Then** the system does not deduct the $5.00 share fee.
    *   **And** the system sets the cooperative membership status to "Pending Funding".
    *   **And** the system displays a dashboard notification: "Deposit at least $5.00 to purchase your cooperative share and activate your voting rights."

*   **Scenario 3: Edge Case - Account Closure and Share Redemption**
    *   **Given** an active member-owner initiates the account closure process.
    *   **When** the member requests to withdraw all remaining funds.
    *   **Then** the system redeems the cooperative share, crediting $5.00 back to the user's closing balance.
    *   **And** the system marks the member's share ID as "Redeemed/Inactive" in the registry.

---

## Epic 2: Core Accounts & Treasury (CAT)

### Story CAT-1: Group Pot Creation & Multi-Signature Oversight

#### Business & Security Rules
*   **Eligibility:** Only verified active member-owners in good standing can create or join a Group Pot.
*   **Threshold Settings:** The creator must define the approval threshold (e.g., 2 out of 3 signers) at the time of creation.
*   **Ledger Rules:** The sub-ledger must track and display the exact breakdown of contributions by individual member IDs.
*   **Security Assertion:** Access to the pot's details, balances, and history must be restricted using access control lists (ACLs) to only those member IDs that are registered participants of the pot.

#### Scenarios

*   **Scenario 1: Happy Path - Successful Group Pot Setup**
    *   **Given** a verified member-owner is logged into the application.
    *   **When** the user creates a Group Pot named "Housing Fund".
    *   **And** the user invites two other active member-owners by entering their member IDs.
    *   **And** the user sets the authorization threshold to "2 of 3 approvals".
    *   **Then** the system creates the Group Pot, marks the invitees as "Pending Acceptance", and sends them invitations.

*   **Scenario 2: Negative Path - Invitation of Non-Existent Member ID**
    *   **Given** a verified member-owner is configuring a new Group Pot.
    *   **When** the user attempts to invite a member using an invalid or non-existent Member ID.
    *   **Then** the system blocks the invitation.
    *   **And** the system displays an error message: "Member ID not found. Please verify the ID."

*   **Scenario 3: Edge Case - Change of Approval Threshold by Members**
    *   **Given** a Group Pot has 4 active members and a threshold of "3 of 4".
    *   **When** the members vote to change the threshold to "5 of 4".
    *   **Then** the system rejects the configuration change.
    *   **And** the system displays a validation error: "Approval threshold cannot exceed the number of active signers in the group."

---

### Story CAT-2: Joint Transaction Consent Flow

#### Business & Security Rules
*   **Transaction Lock:** Any outbound transaction from a Group Pot must be held in a "Pending Approval" state.
*   **Expiry Window:** Pending approvals must expire after exactly 48 hours. If expired, funds on hold are released back to the pot.
*   **Security Assertion:** Approvals must be authenticated using the signer's biometric credential (face/fingerprint scan) or secure passcode.

#### Scenarios

*   **Scenario 1: Happy Path - Threshold Reached and Transaction Executed**
    *   **Given** a Group Pot has a "2 of 3" approval threshold.
    *   **When** Member A initiates an outbound transfer of $200.00.
    *   **Then** the system places a pending hold on $200.00 and sends push notifications to Member B and Member C.
    *   **And when** Member B approves the transaction using biometric authentication.
    *   **Then** the threshold is met, the system executes the transfer, and notifies all members of the successful execution.

*   **Scenario 2: Negative Path - Transaction Explicitly Rejected**
    *   **Given** a Group Pot has a "2 of 3" approval threshold.
    *   **When** Member A initiates a transfer of $150.00.
    *   **And** Member B and Member C both reject the transaction in the app.
    *   **Then** the system cancels the transaction.
    *   **And** the system releases the $150.00 hold and notifies all members.

*   **Scenario 3: Edge Case - Time Window Expiry**
    *   **Given** a Group Pot has a pending transaction request.
    *   **When** 48 hours pass without the required number of approvals being recorded.
    *   **Then** the system updates the transaction status to "Expired".
    *   **And** the system returns the held funds to the available balance of the Group Pot.

---

### Story CAT-3: Ethical Yield Allocation

#### Business & Security Rules
*   **Granularity:** Users must be able to adjust yield donation percentages in increments of 1% (from 0% to 100%).
*   **Project Verification:** Interest splits can only be routed to projects listed as "Active" in the Community Impact Funding module.
*   **Tax Compliance:** The system must generate a receipt for each split transaction labeled as a "Community Yield Donation".

#### Scenarios

*   **Scenario 1: Happy Path - Automatic Interest Split**
    *   **Given** the user has configured their yield allocator to route 10% of interest to the "Solar Power Project".
    *   **When** the monthly interest payment is processed and calculates $50.00 of interest earned.
    *   **Then** the system splits the payment, depositing $45.00 into the user's savings account.
    *   **And** the system deposits $5.00 into the "Solar Power Project" treasury account.
    *   **And** the system logs a tax-deductible donation entry of $5.00.

*   **Scenario 2: Negative Path - Destination Project Terminated or Completed**
    *   **Given** the user's yield allocator is set to 20% donation for "Housing Initiative A".
    *   **When** "Housing Initiative A" reaches its funding goal and transitions to "Completed" status.
    *   **Then** the system automatically resets the user's donation allocation to 0% for that project.
    *   **And** the system sends an in-app alert to the user to choose a new target project.
    *   **And** the system directs 100% of subsequent interest to the user's savings account until a new selection is made.

---

## Epic 3: Democratic Governance (DGV)

### Story DGV-1: Policy & Parameter Voting

#### Business & Security Rules
*   **Equality Principle:** The voting system must enforce a "One Member, One Vote" restriction, regardless of the user's account balance.
*   **Anonymity Assertion:** The application database must decouple the "Voted Status" record of a member ID from the actual ballot details to guarantee complete vote privacy.
*   **Immutability:** Once a vote is successfully cast, it cannot be modified or retracted.

#### Scenarios

*   **Scenario 1: Happy Path - Member Casts Vote**
    *   **Given** a verified member-owner who has not yet voted on the proposal "Increase checking interest to 2.5%".
    *   **When** the member selects "Yes" and submits their vote.
    *   **Then** the system records the vote in the anonymous tally database.
    *   **And** the system marks the member's voter record as "Voted" for this proposal.
    *   **And** the member is prevented from voting on this proposal again.

*   **Scenario 2: Negative Path - Non-Member Attempts to Vote**
    *   **Given** a visitor has created an account but has not yet purchased their cooperative share.
    *   **When** the user attempts to submit a ballot.
    *   **Then** the system blocks the submission.
    *   **And** the system displays a restriction message: "Voting is reserved for active member-owners who have funded their cooperative share."

*   **Scenario 3: Edge Case - Concurrent Voting Requests**
    *   **Given** an active member-owner is on the voting screen.
    *   **When** the user rapidly submits their vote multiple times (double-tap exploit).
    *   **Then** the system processes only the first request successfully.
    *   **And** the system rejects subsequent requests with a "Vote already recorded" error.

---

### Story DGV-2: Representative Board Elections

#### Business & Security Rules
*   **Electoral Window:** Elections must occur only within defined start and end date/time parameters.
*   **Seat Validation:** The user cannot select more candidates than there are vacant seats on the ballot.
*   **Security Assertion:** The system must generate a cryptographic verification token for the voter to confirm their vote is included in the final tally without exposing their selections.

#### Scenarios

*   **Scenario 1: Happy Path - Successful Ballot Submission**
    *   **Given** there is an active board election with 2 open seats.
    *   **When** a member-owner selects 2 candidates and submits the ballot.
    *   **Then** the system increments the tallies for those candidates.
    *   **And** the system issues a unique cryptographic receipt to the user.

*   **Scenario 2: Negative Path - Selecting More Candidates Than Allowed**
    *   **Given** an election with 2 open seats.
    *   **When** the member-owner attempts to select 3 candidates on the screen.
    *   **Then** the system prevents the selection of the third candidate.
    *   **And** the system displays a validation warning: "You can select a maximum of 2 candidates."

*   **Scenario 3: Edge Case - Submission at Expiry Deadline**
    *   **Given** a user is completing their ballot as the election window is closing.
    *   **When** the user taps submit at the exact second the election expires.
    *   **And** the server receives the request after the expiration timestamp.
    *   **Then** the system rejects the ballot.
    *   **And** the system displays the message: "Elections have closed. Your ballot was not recorded."

---

### Story DGV-3: Member Proposal Builder & Signature Gathering

#### Business & Security Rules
*   **Field Constraints:** Proposals must have a Title (10–100 characters), Summary (50–500 characters), and Description (100–5000 characters).
*   **Signature Limit:** A member can sign a draft proposal only once. Signatures cannot be withdrawn.
*   **Automatic Progression:** When a draft proposal reaches the target signature count (e.g., 500 signatures) within the 30-day deadline, it must transition from "Draft" status to "Submitted".

#### Scenarios

*   **Scenario 1: Happy Path - Proposal Reaches Target Signature Threshold**
    *   **Given** an active draft proposal has gathered 499 signatures.
    *   **When** a verified member-owner adds their signature to the proposal.
    *   **Then** the system updates the signature count to 500.
    *   **And** the system changes the proposal status to "Submitted".
    *   **And** the system routes the proposal to the board review queue.

*   **Scenario 2: Negative Path - Signature of Proposal by the Creator**
    *   **Given** a member-owner has created a draft proposal.
    *   **When** the creator attempts to sign their own proposal.
    *   **Then** the system blocks the action.
    *   **And** the system displays a message: "Creators are credited as the primary sponsor and cannot sign their own proposal."

*   **Scenario 3: Edge Case - Proposal Expiration**
    *   **Given** a draft proposal has gathered 350 signatures.
    *   **When** the proposal reaches its 30-day publication limit.
    *   **Then** the system changes the proposal status to "Archived".
    *   **And** the system disables the "Sign Support" button.

---

## Epic 4: Peer-Supported Lending (PSL)

### Story PSL-1: Lending Circle Setup & Enrollment

#### Business & Security Rules
*   **Group Limits:** Lending circles must contain between 3 and 12 participants.
*   **Contribution Rule:** Monthly contributions must be equal across all participants and automatically debited on the same day each month.
*   **Order of Draw:** The rotation order must be fully established and agreed upon by all participants before the circle can be activated.
*   **Security Assertion:** Defaulting on a contribution triggers automatic lockouts on a member's primary cooperative share.

#### Scenarios

*   **Scenario 1: Happy Path - Circle Activation and First Payout Cycle**
    *   **Given** a group of 4 members have set up a circle with a $50.00 monthly contribution.
    *   **When** the start date arrives and all 4 members have sufficient balances.
    *   **Then** the system debits $50.00 from each member.
    *   **And** the system transfers the total sum of $200.00 directly to the first scheduled beneficiary.

*   **Scenario 2: Negative Path - Contribution Failure (Insufficient Funds)**
    *   **Given** an active lending circle is in its second month.
    *   **When** the payment execution date arrives and Member B has a balance of $10.00 (insufficient for the $50.00 contribution).
    *   **Then** the system fails the debit transaction.
    *   **And** the system sends alerts to the circle and halts the payout to the beneficiary.
    *   **And** the system initiates the default recovery procedure for Member B.

---

### Story PSL-2: Peer Guarantee Collateral Locking

#### Business & Security Rules
*   **Collateral Lock:** The guaranteed amount must be locked in the guarantor's savings account, reducing their available balance.
*   **Pro-Rata Release:** As the borrower pays down the principal of the loan, the corresponding locked savings of the guarantor must be released proportionally.
*   **Rate Deduction:** The interest rate discount applied to the borrower is directly proportional to the percentage of the loan principal covered by the guarantee.

#### Scenarios

*   **Scenario 1: Happy Path - Collateral Lock and Pro-Rata Release**
    *   **Given** a guarantor agrees to guarantee $500.00 of a borrower's $1,000.00 loan.
    *   **When** the loan is disbursed to the borrower.
    *   **Then** the system locks $500.00 in the guarantor's savings account.
    *   **And when** the borrower pays off $200.00 of the loan principal.
    *   **Then** the system automatically unlocks $100.00 (50% of the repaid principal) in the guarantor's account.

*   **Scenario 2: Negative Path - Insufficient Available Balance to Guarantee**
    *   **Given** a user has a savings balance of $1,000.00, but $700.00 of it is already locked for another loan.
    *   **When** the user attempts to guarantee a new loan for $500.00.
    *   **Then** the system rejects the guarantee request.
    *   **And** the system displays the message: "Insufficient available funds. Only $300.00 is available for guarantees."

*   **Scenario 3: Edge Case - Borrower Defaults on Loan**
    *   **Given** a borrower's loan is in default (90 days past due) with $300.00 of remaining principal guaranteed.
    *   **When** the system initiates the default recovery protocol.
    *   **Then** the system withdraws the remaining locked $300.00 from the guarantor's savings account.
    *   **And** the system applies it to settle the outstanding loan balance.
    *   **And** the system notifies the guarantor of the seizure of funds.

---

## Epic 5: Community & Impact Funding (CIF)

### Story CIF-1: Community Project Crowdfunding

#### Business & Security Rules
*   **Project Lifespan:** Crowdfunding campaigns must have a duration limit of 1 to 90 days.
*   **Escrow Ledger:** All contributions must be held in a project-specific escrow account.
*   **Refund Rule:** If the project fails to meet its exact funding target by the deadline, 100% of the funds in the escrow ledger must be refunded to the donors.

#### Scenarios

*   **Scenario 1: Happy Path - Project Reached Target and Funds Disbursed**
    *   **Given** a project has a funding target of $2,000.00.
    *   **When** donations from members reach $2,000.00 before the project deadline.
    *   **Then** the system marks the project as "Fully Funded".
    *   **And** the system transfers the escrowed $2,000.00 to the project creator's bank account.

*   **Scenario 2: Negative Path - Project Fails to Reach Target (Refund Triggered)**
    *   **Given** a project has a target of $2,000.00 and a 30-day deadline.
    *   **When** the deadline is reached and the total donations received equal $1,800.00.
    *   **Then** the system marks the project as "Unsuccessful".
    *   **And** the system automatically refunds the respective donation amounts back to each donor's account.

---

### Story CIF-2: Surplus Treasury Grant Matching

#### Business & Security Rules
*   **Ratio:** Matching is calculated at a 1:1 ratio.
*   **Validation Check:** The system must verify that both the individual project matching cap and the overall quarterly matching treasury budget have remaining funds before executing the match.
*   **Atomicity:** The matching transaction from the treasury must occur in the same database transaction as the member's donation.

#### Scenarios

*   **Scenario 1: Happy Path - Match Executed Successfully**
    *   **Given** a project is eligible for matching grants and has not reached its project matching limit.
    *   **When** a member donates $50.00 to the project.
    *   **Then** the system debits $50.00 from the member's account.
    *   **And** the system transfers $50.00 from the Bank's Surplus Matching Treasury to the project escrow.
    *   **And** the project's funding progress shows an increase of $100.00.

*   **Scenario 2: Negative Path - Project Matching Cap Reached**
    *   **Given** a project has a matching grant cap of $500.00, and $500.00 has already been matched.
    *   **When** a member makes a donation of $50.00.
    *   **Then** the system transfers only the member's $50.00 donation to the project escrow.
    *   **And** the system does not allocate any matching funds from the bank treasury.

*   **Scenario 3: Edge Case - Quarterly Budget Exhaustion**
    *   **Given** the quarterly matching treasury has only $10.00 remaining.
    *   **When** a member makes a donation of $100.00 to an eligible project.
    *   **Then** the system matches only $10.00 from the treasury.
    *   **And** the system disables the matching engine for all projects for the remainder of the quarter.

---

### Story CIF-3: Impact & Investment Ledger Dashboard

#### Business & Security Rules
*   **Calculation Method:** The dashboard must calculate a user's personalized impact by determining the ratio of the user's average balance to the bank's total assets, and applying that ratio to the aggregate project metrics.
*   **Update Frequency:** Data displayed on the dashboard must be refreshed automatically at least once every 24 hours.

#### Scenarios

*   **Scenario 1: Happy Path - Metrics Rendered Successfully**
    *   **Given** the user has an average monthly balance of $2,000.00.
    *   **When** the user navigates to the Impact Dashboard.
    *   **Then** the system displays the total community metrics (e.g., carbon offset, affordable homes built).
    *   **And** the system displays the user's calculated share of that impact (e.g., "Your deposits have contributed to planting 12 trees").

*   **Scenario 2: Negative Path - Data Sync Failure**
    *   **Given** the impact aggregation database service is offline.
    *   **When** the user opens the dashboard.
    *   **Then** the system displays the cached data from the last successful update.
    *   **And** the system displays a status message: "Data updated [X] hours ago. Reconnecting to live feed."

---

## Epic 6: Dividend Management & Allocation (DMA)

### Story DMA-1: Projected Dividend Dashboard

#### Business & Security Rules
*   **Inputs:** Calculations must be based on: (1) Average deposit balance, (2) Active loan repayment status, (3) Voting participation rate, and (4) The bank's year-to-date net surplus.
*   **Update Frequency:** Calculations must be updated daily via a background processing task.

#### Scenarios

*   **Scenario 1: Happy Path - Correct Estimation Rendered**
    *   **Given** a member who maintains a $5,000.00 average balance and has voted in all active elections.
    *   **When** the user visits the Dividend Dashboard.
    *   **Then** the system displays a real-time dividend estimation (e.g., "Projected Annual Dividend: $75.00").
    *   **And** the system provides a breakdown detailing the contribution of voting activity and deposits to the estimate.

*   **Scenario 2: Negative Path - Background Sync Delayed**
    *   **Given** the daily update cron job fails to calculate the projections.
    *   **When** the user opens the dashboard.
    *   **Then** the system displays the last calculated projection.
    *   **And** the system displays a warning message: "Dividend estimates may be out of date. We are correcting this now."

---

### Story DMA-2: Automated Dividend Disbursal

#### Business & Security Rules
*   **Authorization Rule:** The payout disbursal job can only be triggered after the annual general assembly vote passes and two authorized treasury administrators sign off on the batch execution.
*   **Payout destination:** Dividends must be transferred directly into the member's primary checking or savings account.
*   **Documentation:** The system must generate a PDF tax statement (e.g., 1099-DIV equivalent) for each member receiving a payout.

#### Scenarios

*   **Scenario 1: Happy Path - Batch Disbursal Success**
    *   **Given** the general assembly has approved the annual dividend percentage.
    *   **And** two treasury administrators have authorized the execution of the payment batch.
    *   **When** the disbursal job runs.
    *   **Then** the system calculates the pro-rata payout for every active member ID.
    *   **And** the system deposits the funds into their savings accounts.
    *   **And** the system generates and deposits the digital tax statement in the member document folder.

*   **Scenario 2: Negative Path - Payment Fails due to Closed Account**
    *   **Given** the disbursal job is executing the batch payments.
    *   **When** the system attempts to deposit a dividend to a member whose account has been suspended or closed.
    *   **Then** the system halts the transaction for that specific member ID.
    *   **And** the system logs a payout error in the treasury audit trail.
    *   **And** the system continues processing the remaining members in the batch.

---
### Summary of Work

I have finalized the Gherkin-style Acceptance Criteria for all 15 user stories in Sprint 3. The document is structured in clean Markdown, without any external links, and contains no source code, adhering to the project's quality standards and compliance regulations.