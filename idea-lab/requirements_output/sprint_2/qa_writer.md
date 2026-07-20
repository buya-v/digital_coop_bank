### Epic 1: Member Identity & Onboarding ("Instant-Share" Onboarding)

#### Story 1.1: Automated Identity Verification (eKYC)
**Business Rules, Data Validation, & Security Assertions:**
- *Age Validation:* The applicant's extracted Date of Birth must indicate they are at least 18 years old.
- *Confidence Threshold:* The facial matching algorithm must return a confidence score of 95% or higher to auto-pass.
- *Liveness Check:* Liveness detection must verify the selfie is a real-time capture (no pre-recorded video or photo-of-a-photo spoofing).
- *Data Integrity:* Government ID text must be successfully parsed via OCR, ensuring required fields (First Name, Last Name, Date of Birth, ID Number) are not empty.
- *PII Protection:* All uploaded photos and OCR data must be encrypted in transit and at rest, complying with GDPR/CCPA guidelines.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Instant Identity Pass*
```gherkin
Given a new user starts the "Instant-Share" onboarding process
And they have provided a valid government-issued photo ID
And they are at least 18 years old according to the ID
When they upload the ID photo and complete the live selfie scan with liveness check
Then the system successfully parses the ID details via OCR
And the system confirms the selfie match confidence is >= 95%
And the system updates the member's profile KYC status to "Passed"
And the user is navigated to the Share Purchase screen
```

*Scenario 2: Negative Path - Liveness Verification Failure*
```gherkin
Given a new user starts the "Instant-Share" onboarding process
And they upload a valid government ID
When they attempt the selfie verification using a printed photo instead of a live capture
Then the liveness detection engine flags the selfie as a spoofing attempt
And the system denies the automatic verification
And the member's profile KYC status is set to "Pending Manual Review"
And the user is presented with a message indicating their application is being reviewed by support
```

*Scenario 3: Edge Case - ID and Selfie Mismatch (Confidence < 95%)*
```gherkin
Given a new user starts the onboarding process
And they upload their passport photo
When they complete the live selfie scan, but the facial recognition confidence is only 82% due to poor lighting
Then the system prevents automatic approval
And the KYC status is marked as "Failed - Review Required"
And the user is prompted to retry the selfie capture under better lighting conditions
```

---

#### Story 1.2: Mandatory Member Share Purchase
**Business Rules, Data Validation, & Security Assertions:**
- *Share Price:* Fixed at exactly $25.00 USD. No other amounts allowed.
- *Ledger Routing:* The $25.00 transaction must be explicitly routed to the Member Share Capital Ledger, not the general savings ledger.
- *Equity Designation:* The purchased share must be flagged as non-withdrawable equity.
- *Pre-requisite:* User must have a KYC status of "Passed" to proceed.
- *Receipt & Bylaws Delivery:* The receipt and cooperative bylaws PDF must be transmitted via secure SMTP to the member's registered email address.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Successful Share Purchase via Credit Card*
```gherkin
Given a user has successfully passed the eKYC verification stage
And their current onboarding state requires the $25 membership share purchase
When they select "Credit Card" as their payment method
And they input valid card details and authorize the $25.00 transaction
Then the payment gateway processes the charge successfully
And the $25.00 is credited to the Member Share Capital Ledger as non-withdrawable equity
And a receipt email containing the transaction details and the cooperative bylaws is sent to the user
And the user is redirected to the membership token generation step
```

*Scenario 2: Negative Path - Declined Payment Transaction*
```gherkin
Given a user has successfully passed the eKYC verification stage
And they are on the payment gateway interface
When they attempt to purchase the $25 share using a card with insufficient funds
Then the payment gateway returns a "Declined" transaction code
And the Member Share Capital Ledger remains unchanged
And the user is shown an error message stating "Payment declined: Insufficient funds. Please try another payment method."
And they are kept on the payment screen to retry
```

*Scenario 3: Security Edge Case - Direct API Bypass Attempt*
```gherkin
Given an unauthenticated or non-KYC-passed client attempts to post a share purchase transaction directly to the API
When the request is processed by the API gateway
Then the system blocks the request with a "403 Forbidden" error
And no entry is made in the Member Share Capital Ledger
And a security alert is logged in the system audit logs
```

---

#### Story 1.3: Cooperative Membership Token Generation
**Business Rules, Data Validation, & Security Assertions:**
- *Token Security:* Membership ID must be a unique, cryptographically secure string (e.g., UUIDv4) that cannot be easily guessed.
- *State Transition:* Membership status must transition to "Active Member" in the central database only after both KYC and payment verify as successful.
- *Access Control:* Access tokens generated for the user session must be updated to include the "Active Member" claim to unlock protected routes (Governance, Savings Accounts).

**Acceptance Criteria:**

*Scenario 1: Happy Path - Automatic Token Generation and UI Unlock*
```gherkin
Given a user has passed eKYC
And the system receives confirmation of the successful $25.00 member share payment
When the system processes the completion of the onboarding flow
Then a unique cooperative membership ID is generated for the user
And the user's status in the identity directory is updated to "Active Member"
And the user's current session claims are refreshed to include the "Active Member" role
And the mobile application dashboard transitions to show the "Governance" and "Savings" tabs as unlocked
```

*Scenario 2: Negative/Edge Case - Access Attempt with Pending Onboarding Status*
```gherkin
Given a user has passed eKYC but has not completed the $25.00 share purchase
When they attempt to navigate directly to the Governance portal via an in-app deep link
Then the system blocks the navigation
And redirects the user back to the "Mandatory Share Purchase" screen
And displays a banner stating "Please complete your membership share purchase to unlock cooperative features."
```

---

### Epic 2: Peer-Supported Lending (Social Loan Circles)

#### Story 2.1: Social Loan Circle Creation & Invitation
**Business Rules, Data Validation, & Security Assertions:**
- *Circle Size:* Minimum of 3 and maximum of 5 distinct active cooperative members (excluding the borrower).
- *Search Restriction:* The member lookup tool must only return members with "Active Member" status.
- *Double Inviting:* A borrower cannot invite the same member multiple times to the same circle.
- *Circle Lifespan:* Circle invitations expire after 7 calendar days if the minimum count (3) is not met.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Circle Formed Successfully*
```gherkin
Given an active member "Clara" starts a new "Social Loan Circle" from her dashboard
When she searches for and invites three active members "Alex", "Blake", and "Charlie" using their unique Member IDs
And all three invited members accept the invitation via their respective push notifications
Then the system registers the invitations as "Accepted"
And the status of Clara's Social Loan Circle transitions to "Formed"
And the loan application is unlocked for submission with community backing
```

*Scenario 2: Negative Path - Member Search with Inactive Status*
```gherkin
Given Clara is creating a Social Loan Circle
When she attempts to search for a user using the email "ex-member@coop.com"
And that user's account status is currently "Suspended"
Then the system does not return the user in the search results
And displays a validation message: "No active cooperative member found with the provided identifier."
```

*Scenario 3: Edge Case - Maximum Limit Exceeded*
```gherkin
Given Clara has successfully invited 5 members who have all accepted the invitations
When she attempts to search for and invite a 6th member to the same Social Loan Circle
Then the system disables the "Invite" action
And displays a validation error: "Social Loan Circles are limited to a maximum of 5 guarantors."
```

---

#### Story 2.2: Pledging Share Capital as Security
**Business Rules, Data Validation, & Security Assertions:**
- *Pledge Cap:* A guarantor cannot pledge an amount exceeding their current "Available Savings Balance" minus any existing holds.
- *Collateral Hold:* Pledged funds must be immediately placed on a database hold status, preventing withdrawal, transfer, or use in other pledges.
- *Legal Signature:* The system must capture an electronic signature (matching legal standards like the ESIGN Act) linked to the specific pledge terms.
- *Self-Pledging:* A borrower cannot pledge their own funds to their own Social Loan Circle.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Successful Collateral Pledge*
```gherkin
Given a guarantor "Marcus" opens a pending loan request for "Clara" in his Social Loan Circle dashboard
And Clara is requesting a $1,000 loan
And Marcus has an available savings balance of $500
When Marcus inputs a pledge amount of $200
And signs the digital guarantor agreement
Then the system verifies the $200 is less than or equal to his available balance
And the system places a $200 "Collateral Hold" on Marcus's savings account ledger
And Marcus's available balance updates to $300 (with total balance remaining $500)
And Clara's Social Loan Circle registry records the signed agreement and the $200 pledge
```

*Scenario 2: Negative Path - Pledge Exceeding Available Balance*
```gherkin
Given Marcus has an available savings balance of $150
When he attempts to pledge $200 to Clara's Social Loan Circle
Then the system blocks the submission
And displays a validation error: "Pledge amount cannot exceed your available savings balance of $150.00."
And no collateral hold is created on the ledger
```

*Scenario 3: Edge Case - Revoking a Pledge Before Loan Disbursal*
```gherkin
Given Marcus has pledged $200 to Clara's pending loan application
And the loan has not yet been disbursed
When Marcus decides to withdraw his pledge from his circle dashboard
Then the system releases the $200 "Collateral Hold" from Marcus's account
And his available balance returns to $500
And Clara's Social Loan Circle total pledged amount is reduced by $200
```

---

#### Story 2.3: Community-Guaranteed Underwriting & Dynamic Pricing
**Business Rules, Data Validation, & Security Assertions:**
- *Base Rate:* The standard baseline interest rate for unsecured loans is 12% APR.
- *Tiered Pricing Logic:*
  - Tier 1: 25% - 49% collateral coverage -> 2% interest rate discount.
  - Tier 2: 50% - 74% collateral coverage -> 4% interest rate discount.
  - Tier 3: 75% - 100%+ collateral coverage -> 6% interest rate discount.
- *Recalculation:* Any change in pledged collateral prior to the loan agreement signing must trigger a recalculation of the interest rate.
- *Security:* The final signed loan agreement PDF must be hashed and stored in the database to prevent tampering.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Dynamic Interest Rate Discount Applied*
```gherkin
Given Clara's loan application for $1,000 has a base interest rate of 12% APR
And her Social Loan Circle has accumulated a total of $600 in pledged collateral (60% coverage)
When she opens her loan offers dashboard
Then the underwriting engine detects Tier 2 coverage (50% - 74%)
And applies a 4% APR discount to the offer
And presents a customized loan offer of 8% APR to Clara
And shows a breakdown of how the community's $600 pledge reduced her rate
```

*Scenario 2: Negative Path - Collateral Drops Below Minimum Tier Before Acceptance*
```gherkin
Given Clara has a customized loan offer of 8% APR based on a $600 (60%) community pledge
And a guarantor withdraws a $200 pledge before Clara signs the contract
When Clara attempts to accept and sign the loan offer
Then the system blocks the transaction
And displays a message: "Your circle's pledged collateral has changed. Re-calculating loan terms."
And the system updates the offer to 10% APR (based on $400 / 40% coverage - Tier 1 discount)
```

---

### Epic 3: Democratic Governance (Liquid Democracy & Proxy Routing)

#### Story 3.1: Ballot Management and Direct Voting
**Business Rules, Data Validation, & Security Assertions:**
- *Voting Power:* One member, one vote. The system must verify that a member has not already cast a vote or had their vote weight allocated on the specific ballot.
- *Authentication & Token:* The voter must possess a valid, active session token with the "Active Member" claim.
- *Ballot Status:* Votes can only be submitted during the active window of the ballot (Current Time >= Start Time and Current Time <= End Time).
- *Anonymity:* Direct vote selections (Yes/No/Abstain) must be decoupled from the user's identity in the voting registry database to maintain ballot secrecy, while maintaining an immutable audit log of who has voted to prevent double-voting.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Successful Direct Vote*
```gherkin
Given an active member "Evan" is authenticated in the system
And there is an active resolution ballot titled "Green Energy Lending Policy"
And Evan has not yet voted on this ballot
When Evan navigates to the Ballot page, selects "Yes", and submits his vote
Then the system verifies his Active Member token
And registers that Evan has voted on the "Green Energy Lending Policy" ballot
And increments the "Yes" count on the ballot ledger by 1
And updates the UI to show the ballot status as "Voted"
```

*Scenario 2: Negative Path - Attempted Double Voting*
```gherkin
Given Evan has already cast his vote on the "Green Energy Lending Policy" ballot
When he attempts to bypass the UI constraints and sends a POST request to submit another vote
Then the system returns a "409 Conflict" error
And the vote totals on the ledger remain unchanged
```

*Scenario 3: Edge Case - Voting After Deadline*
```gherkin
Given a ballot's deadline was 12:00:00 PM today
And the current system time is 12:01:00 PM today
When a member attempts to submit a vote on the ballot
Then the system rejects the request with a validation error: "This ballot is closed and no longer accepting votes."
```

---

#### Story 3.2: Category-Specific Proxy Delegation
**Business Rules, Data Validation, & Security Assertions:**
- *Proxy Status:* The designated proxy must be an active cooperative member.
- *Self-Delegation:* A member cannot delegate voting power to themselves.
- *Circular Delegation Prevention:* The system must traverse the delegation path to ensure that delegating to Member B does not create a loop (e.g., A -> B -> C -> A). If a loop is detected, the transaction must be rejected.
- *Category Isolation:* Delegation is category-specific. A delegation in "Green Lending Policy" does not affect voting weight in "Treasury Reserve Ratios".

**Acceptance Criteria:**

*Scenario 1: Happy Path - Successful Category Delegation*
```gherkin
Given Clara is an active member
And "Marcus" is a registered active member and community expert
When Clara selects the "Green Lending Policy" category in her Delegation Settings
And searches for Marcus's member ID and clicks "Delegate"
Then the system validates that Marcus is active and does not create a circular loop
And saves the delegation record linking Clara's vote weight for "Green Lending Policy" to Marcus
And displays a success message: "Your voting weight for Green Lending Policy has been successfully delegated to Marcus."
```

*Scenario 2: Negative Path - Circular Delegation Loop Detected*
```gherkin
Given member A has delegated their voting power for "Treasury Reserve Ratios" to member B
And member B has delegated their voting power for the same category to member C
When member C attempts to delegate their voting power to member A
Then the system runs a path traversal check and detects a circular reference loop (C -> A -> B -> C)
And blocks the delegation transaction
And displays a validation error: "Invalid delegation: This assignment would create a voting loop."
```

---

#### Story 3.3: Proxy Revocation and Direct Overrides
**Business Rules, Data Validation, & Security Assertions:**
- *Revocation Timeline:* Delegation revocation is instantaneous and applies to all future votes and open ballots that have not closed.
- *Override Priority:* A direct vote by a delegating member always overrides a vote cast by their proxy for that specific ballot.
- *Vote Weight Adjustment:* When an override occurs, the proxy's aggregated vote weight on that ballot must be decremented by 1, and the member's direct vote must be registered under their selected choice.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Direct Override of Proxy Vote*
```gherkin
Given Clara has delegated her voting power to Marcus for the "Community Grants" category
And Marcus has already cast a "Yes" vote on an active ballot in that category
When Clara opens the ballot details and casts a direct vote of "No"
Then the system registers Clara's direct vote of "No"
And reduces the proxy vote weight cast by Marcus by 1
And increases the direct vote count for "No" by 1
And displays a message: "Your direct vote has been recorded and has overridden your proxy's vote for this ballot."
```

*Scenario 2: Happy Path - Instant Revocation of Proxy Delegation*
```gherkin
Given Clara has an active delegation to Marcus for the "Green Lending" category
When she clicks the "Revoke" button on her Delegation Settings dashboard
Then the system deletes the delegation record
And restores Clara's direct voting status for all future ballots in "Green Lending"
```

*Scenario 3: Edge Case - Direct Override Attempt After Ballot Closure*
```gherkin
Given a ballot in the "Community Grants" category has closed
And Clara's proxy Marcus voted on her behalf during the ballot window
When Clara attempts to submit a direct override vote post-closure
Then the system blocks the vote submission
And returns an error message: "This ballot is closed. Votes cannot be modified."
```

---

### Epic 4: Cooperative Dividends (Real-Time Patronage Tracker)

#### Story 4.1: Patronage Footprint Dashboard
**Business Rules, Data Validation, & Security Assertions:**
- *Metrics Accuracy:* The values displayed must pull directly from the verified core ledger.
- *Data Source Constraints:*
  - Average Savings Balance: Calculated as the daily average balance over the elapsed days of the current fiscal year.
  - Loan Interest Paid: Total interest transaction type entries on the member's loan accounts.
  - Transaction Volume: Aggregated dollar amount of settled card purchases.
- *Data Cache:* Dashboard data must be updated at least once every 24 hours (nightly batch process) with the last sync timestamp clearly displayed.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Load Dashboard with Complete Activity*
```gherkin
Given an active member "Evan" logs into his banking app
And has active savings, a car loan, and regular card transactions
When he navigates to the "Patronage Footprint" tab
Then the app loads the dashboard interface
And displays the correct metrics: Average Savings ($5,230.00), Total Interest Paid ($120.00), and Card Volume ($12,450.00)
And displays the last sync timestamp
And provides a textual breakdown explaining how each metric contributes to the bank's surplus
```

*Scenario 2: Negative/Edge Path - Load Dashboard for New Member (No Activity)*
```gherkin
Given a newly onboarded member who has only purchased the $25 share
When they navigate to the "Patronage Footprint" tab
Then the dashboard loads successfully
And displays the default values of "$0.00" for Savings, Interest, and Card Volume
And displays a helper card prompting them to start saving or spending to build their patronage footprint
```

---

#### Story 4.2: Real-Time Dividend Estimator
**Business Rules, Data Validation, & Security Assertions:**
- *Formula Transparency:* The projection formula must utilize the current fiscal year's forecasted cooperative net surplus (provided by the Treasury service) and the user's current patronage metrics.
- *Scenario Bounds:*
  - Conservative: Based on 80% of forecasted surplus.
  - Expected: Based on 100% of forecasted surplus.
  - High-Performance: Based on 120% of forecasted surplus.
- *Suggestion Logic:* Contextual suggestions must be dynamically generated based on gap analysis.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Estimated Projections Displayed*
```gherkin
Given Clara opens her Patronage Dividend Tracker dashboard
And the Treasury system has published the latest cooperative surplus forecast
When the estimator calculates her return
Then the UI displays three distinct projection bars: Conservative ($45.00), Expected ($60.00), and High-Performance ($75.00)
And the dashboard displays a call-to-action suggestion: "Add $150 to your savings account to increase your Expected dividend by an estimated $5.50."
```

*Scenario 2: Negative Path - Treasury Forecast Service Offline*
```gherkin
Given the back-end Treasury forecast service is temporarily unreachable
When Clara navigates to the dividend estimation screen
Then the system fails to retrieve the forecasting coefficients
And the UI displays the member's historical patronage data
And displays a fallback warning: "Dividend estimations are temporarily unavailable. Please check back later."
```

---

### Epic 5: Community Crowdfunding & Investments (Community Crowdfunding Hub)

#### Story 5.1: Listing Community Projects (Pitch Desk)
**Business Rules, Data Validation, & Security Assertions:**
- *Verification Check:* Only users verified as "Organization Representatives" or "Community Organizers" can submit projects.
- *Data Validation Rules:*
  - Title: Required, alphanumeric, 10-100 characters.
  - Target Funding Goal: Required, numeric, must be between $1,000 and $100,000.
  - Timeline: Execution timeline must be between 30 and 365 days.
  - Financial/Social Yield: Must document expected tangible outputs.
  - Supporting Documents: At least one PDF document is required.
- *Admin Workflow:* Submissions must land in a "Pending Review" state, and can only be published to the public hub by a bank administrator.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Successful Project Submission for Admin Review*
```gherkin
Given a verified community organizer "Marcus" is logged into the Pitch Desk
When he fills out the project form with:
  | Field | Value |
  | Title | Community Solar Array Phase 1 |
  | Goal | $50,000 |
  | Timeline | 180 Days |
  | Social Yield | Clean power for 40 local homes |
And uploads a project brief PDF
And submits the project
Then the system validates all fields successfully
And creates the project record with the status "Pending Review"
And displays a message confirming the project is in the review queue
```

*Scenario 2: Negative Path - Validation Error on Incomplete Fields*
```gherkin
Given Marcus is creating a project on the Pitch Desk
When he inputs a funding goal of "$500"
And leaves the supporting document upload blank
And attempts to submit the form
Then the system blocks the submission
And displays inline error messages:
  - "Funding goal must be at least $1,000."
  - "At least one supporting document (PDF) is required."
And the project state remains unsaved
```

*Scenario 3: Security Edge Case - Unauthorized Submission Attempt*
```gherkin
Given an ordinary member "Evan" (who is not a verified organization representative) attempts to submit a project via API request
When the API receives the request
Then the system returns a "403 Unauthorized" response code
And the submission is discarded
```

---

#### Story 5.2: Direct Investment from Savings
**Business Rules, Data Validation, & Security Assertions:**
- *Balance Check:* The investment amount must be less than or equal to the member's available savings balance (excluding member share capital and active collateral holds).
- *Funds Segregation:* Invested funds must be immediately debited from the member's account and placed in a dedicated escrow account associated with the project.
- *Escrow Rules:* Funds remain in escrow until the project funding target is met. If the deadline passes without meeting the target, funds must be refunded to members.
- *Certificate Hashing:* A digital investment certificate containing unique terms and transaction details must be cryptographically signed by the bank and generated as an immutable PDF.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Investment Successfully Executed*
```gherkin
Given Evan has an available savings balance of $1,200
And the "Community Solar Array" project is active with a pending goal
When Evan decides to invest $500 in the solar project
And confirms the investment transaction
Then the system validates he has sufficient funds
And deducts $500 from Evan's savings account ledger
And credits $500 to the "Community Solar Array Escrow Ledger"
And generates a digital investment certificate with terms (maturity, yield)
And displays the certificate in Evan's portfolio tab
```

*Scenario 2: Negative Path - Insufficient Funds for Investment*
```gherkin
Given Evan has an available savings balance of $150
When he attempts to invest $200 in the "Community Solar Array" project
Then the system blocks the investment
And displays a validation error: "Insufficient available savings. Your current available balance is $150.00."
And no ledger transaction is executed
```

*Scenario 3: Edge Case - Project Funding Goal Already Reached*
```gherkin
Given the "Community Solar Array" project has reached 100% of its $50,000 funding goal
When Evan attempts to submit a new investment of $100 to the project
Then the system blocks the transaction
And displays a notice: "This project has reached its funding goal and is closed to new investments."
```

---

#### Story 5.3: Democratic Community Grant Allocation
**Business Rules, Data Validation, & Security Assertions:**
- *Grant Funding Source:* The grant pool must be pre-funded from the cooperative's net surplus ledger.
- *Voting Weight:* Every active member receives an equal, fixed voting weight (e.g., 100 points) to allocate across competing projects.
- *Disbursement Automation:* When the voting window closes:
  - The votes are tallied.
  - The grant pool is divided proportionally among projects.
  - System initiates automated transfers from the Grant Pool Ledger to the projects' organizational accounts.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Allocating Points and Closing the Polls*
```gherkin
Given the bank has announced a $10,000 Community Grant Pool
And two projects "Urban Garden" and "Youth Center" are active on the ballot
And Evan has 100 allocation points available
When Evan allocates 60 points to "Urban Garden" and 40 points to "Youth Center"
And submits his allocation
Then the system registers his points contribution
And updates his remaining allocation points to 0
And displays a confirmation: "Thank you, your community grant votes have been recorded."
```

*Scenario 2: Negative Path - Exceeding Point Allocation Limit*
```gherkin
Given Evan has 100 allocation points
When he attempts to allocate 80 points to "Urban Garden" and 30 points to "Youth Center"
Then the system displays a validation error: "Total allocated points (110) cannot exceed your maximum available points (100)."
And disables the submission button
```

*Scenario 3: System Edge Case - Automated Disbursement at Deadline*
```gherkin
Given the Community Grant voting window closes at 12:00:00 AM
And the total vote distribution is 70% for "Urban Garden" and 30% for "Youth Center"
And the total pool is $10,000
When the scheduled system job runs at 12:00:01 AM
Then the system marks the voting event as "Closed"
And calculates the allocation amounts: $7,000 for Urban Garden, $3,000 for Youth Center
And initiates a ledger transfer of $7,000 to the Urban Garden bank account
And initiates a ledger transfer of $3,000 to the Youth Center bank account
And emails the respective organizers confirming the grant payout
```

---

### Epic 6: Micro-Contributions (Ethical Round-Ups)

#### Story 6.1: Round-Up Activation & Configuration
**Business Rules, Data Validation, & Security Assertions:**
- *Configuration Options:*
  - Destination: Must be a verified active community project or green fund.
  - Multipliers: Supported options are 1x, 2x, or 3x.
  - Monthly Cap: Optional, numeric, must be >= $0.00 (or empty for no cap).
- *State Management:* Changes to the configuration must be saved to the database immediately and take effect on the next cleared transaction.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Enabling Round-Ups with a 2x Multiplier*
```gherkin
Given Evan is on the "Ethical Round-Ups" settings dashboard
When he toggles the feature to "ON"
And selects "Green Reforestation Project" as the target destination
And sets the multiplier to "2x"
And sets a monthly cap of $50.00
And clicks "Save Settings"
Then the system validates the configurations
And updates his profile settings in the database
And displays a confirmation: "Ethical Round-Ups are active. Your spare change will be doubled and sent to Green Reforestation Project."
```

*Scenario 2: Negative Path - Invalid Monthly Cap Input*
```gherkin
Given Evan is configuring his Ethical Round-Ups
When he enters a monthly cap of "-10.00"
Then the system blocks the save action
And displays a validation error: "Monthly cap must be a positive number or zero."
```

---

#### Story 6.2: Automated Round-Up Execution
**Business Rules, Data Validation, & Security Assertions:**
- *Trigger:* Triggers only on card transaction clearance (not authorization).
- *Calculation:*
  - Round-up = Ceil(Transaction Amount) - Transaction Amount.
  - If Transaction Amount is an exact dollar amount (e.g., $10.00), the round-up is $0.00.
- *Threshold:* The transfer from the user's primary transaction account to the project escrow ledger is only initiated once the accumulated pending balance reaches exactly $5.00 or more.
- *Insufficient Funds Protection:* If the user's transaction account balance is less than the accumulated transfer amount ($5.00) when the transfer triggers, the transfer must fail gracefully and retry when funds are available, without overdrafting the account.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Transaction Triggers and Accumulates to Threshold*
```gherkin
Given Evan has "Ethical Round-Ups" active at a 1x multiplier
And his current pending round-up balance is $4.60
And he has $100.00 in his transaction account
When a card transaction of $3.45 clears on his account
Then the system calculates a round-up of $0.55 ($4.00 - $3.45)
And adds $0.55 to his pending round-up balance, totaling $5.15
And detects the pending balance has crossed the $5.00 threshold
And initiates a ledger transfer of $5.15 from Evan's transaction account to the designated project escrow account
And resets the pending round-up balance to $0.00
And lists the transaction on his statement as "Ethical Round-Up Transfer: $5.15"
```

*Scenario 2: Edge Case - Transaction is a Whole Dollar Amount*
```gherkin
Given Evan has "Ethical Round-Ups" active at a 1x multiplier
And his pending round-up balance is $2.00
When a card transaction of $15.00 clears on his account
Then the system calculates the round-up as $0.00
And the pending round-up balance remains $2.00
And no transfer is initiated
```

*Scenario 3: Negative Path - Insufficient Funds for Threshold Transfer*
```gherkin
Given Evan's pending round-up balance is $4.80
And his transaction account balance has dropped to $3.00
When a card transaction of $1.80 clears (creating a $0.20 round-up)
Then the system updates the pending round-up balance to $5.00
And detects the threshold is met
And attempts the $5.00 transfer but detects the account balance ($3.00) is insufficient
And cancels the transfer to prevent overdraft
And retains the pending round-up balance at $5.00
And flags the transfer to retry once the account balance increases
```

---

#### Story 6.3: Live Impact Metrics Dashboard
**Business Rules, Data Validation, & Security Assertions:**
- *Conversion Formulas:* The impact metrics must utilize verified conversion factors provided by the target project (e.g., "$1.00 invested = 0.5 kg CO2 offset").
- *Default Metrics:* If no project-specific metric is available, the system must default to displaying total currency contributed.
- *Security/Privacy:* Social sharing features must only export anonymous impact metrics and must never expose raw account details, transaction history, or account balances.

**Acceptance Criteria:**

*Scenario 1: Happy Path - Load Dynamic Metrics and Share Impact*
```gherkin
Given Evan has contributed a total of $25.00 in round-ups to the "Green Reforestation Project"
And the project's conversion rate is $5.00 per tree planted
When he opens his Live Impact Metrics dashboard
Then the app displays a total contribution of $25.00
And displays the calculated impact as "5 Trees Planted"
And provides a "Share to Social Media" button
And clicking "Share" generates an image card containing: "I just funded 5 trees being planted through my Digital Coop Bank Ethical Round-Ups!"
```

*Scenario 2: Negative/Edge Case - Missing Project Conversion Factor*
```gherkin
Given Evan has contributed $15.00 to a newly listed community project "Local Library Books"
And the project has not uploaded its custom impact conversion rules to the Pitch Desk
When Evan opens his Live Impact Metrics dashboard
Then the app falls back to displaying the raw monetary impact
And displays the metric as: "$15.00 contributed to local initiatives"
And does not display any broken or zero-valued physical translation metrics
```