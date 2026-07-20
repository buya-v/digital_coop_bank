# Sprint 1 Acceptance Criteria & QA Specifications: Digital Coop Bank

This document outlines the detailed, testable Gherkin-style acceptance criteria for the Sprint 1 User Stories of the Digital Coop Bank platform. For each user story, functional scenarios (both happy paths and negative/error paths or edge cases) are defined alongside key business rules, data validation constraints, and security assertions.

---

## Capability 1: Member Identity & Access Management (MIAM)

### US-1.1a: Government ID Verification (F-101)

#### Business Rules & Data Validation
* **Supported File Formats:** Only JPEG, PNG, and PDF formats are permitted.
* **Size Constraint:** Maximum file size limit is 10MB.
* **Document Quality Assurance:** Automated client-side and server-side checks verify image contrast, brightness, and text readability (OCR confidence threshold of at least 80%).
* **Security Assertion:** Uploaded ID documents must be encrypted at rest using AES-256 and stored in an isolated, compliant storage bucket.
* **Status Updates:** Upon a successful upload, the system shifts the user's status to `ID Uploaded - Awaiting Verification`.

#### Scenario 1: Successful ID Upload (Happy Path)
* **Given** a new member is completing the digital onboarding flow
* **And** has reached the "Identity Verification" screen
* **When** the user selects the option to take a photo of their government ID
* **Then** the application triggers the device camera overlay with a guidance frame
* **And** the user captures a sharp image of their passport in JPEG format under 10MB
* **And** the system passes the automated legibility check
* **Then** the file is successfully uploaded
* **And** the system updates the member status to `ID Uploaded - Awaiting Verification`
* **And** displays a success message: "ID uploaded successfully. We are verifying your document."

#### Scenario 2: File Rejection due to Excessive Size (Negative Path)
* **Given** a new member is on the ID upload screen
* **When** the user attempts to upload a PDF file containing their ID that is 12MB in size
* **Then** the client-side validator intercepts the upload
* **And** prevents the file from being transmitted to the server
* **And** displays an error message: "File size exceeds the 10MB limit. Please upload a smaller file."

#### Scenario 3: Image Quality check Failure (Negative Path/Edge Case)
* **Given** a new member is using the camera overlay to capture their ID card
* **When** the user captures a blurry photo where details are obscured
* **Then** the local image processor evaluates the photo and determines text legibility is below threshold
* **And** the upload is rejected
* **And** the system displays a retry message: "Document text is too blurry. Please align your ID card and take the photo in a well-lit area."

---

### US-1.1b: Live Facial Scan & Liveness Check (F-101)

#### Business Rules & Data Validation
* **Capture Interface:** Front-facing camera view inside a circular bounding guide.
* **Liveness Proof:** Dynamic prompting requiring random movement combinations (e.g., blink, turn head left/right, smile).
* **ID Match Threshold:** The biometric service must calculate a face-matching confidence score of 95% or higher against the government ID uploaded in US-1.1a.
* **Escalation Rules:** Maximum of 3 automated scanning attempts are permitted before the account is flagged and routed to a manual verification queue.

#### Scenario 1: Successful Liveness Check and ID Match (Happy Path)
* **Given** a member has completed their government ID upload
* **And** has launched the "Live Facial Scan" module
* **When** the user aligns their face with the circular guide
* **And** completes the requested dynamic prompt (blinking and turning head slightly) within the 15-second time window
* **And** the biometric engine calculates a 97% match confidence against the uploaded ID
* **Then** the liveness check is marked as successful
* **And** the member's account status updates to `Verified`

#### Scenario 2: Verification Fail due to Presentation Attack / Low Match Score (Negative Path)
* **Given** the user is conducting the live facial scan
* **When** a static physical photo of the user is placed in front of the camera to bypass verification
* **Then** the liveness engine detects the absence of depth and movement changes
* **And** blocks the verification
* **And** prompts the user: "Liveness verification failed. Please ensure you are in a well-lit environment and perform the requested actions. (Attempt 1 of 3)"

#### Scenario 3: Execution of Manual Queue Escalation (Edge Case)
* **Given** a user has failed the facial scan 2 times
* **When** the user fails the facial scan for the 3rd time due to a matching score of 89% (below the 95% threshold)
* **Then** the automated onboarding interface locks further attempts
* **And** displays: "We could not automatically verify your identity. Your details have been sent to our manual review team."
* **And** the account status transitions to `Pending Manual Verification`

---

### US-1.3a: View Member Profile & Cooperative Standing (F-102)

#### Business Rules & Data Validation
* **Profile Attributes:** Displays Member ID (unique 8-character alphanumeric string), Full Legal Name, Join Date (format: Month, Year), Membership Tier (e.g., `Founding Member`, `Active Shareholder`, `Pending Capitalization`), and Verification Badge.
* **Access Control:** User must possess a valid JSON Web Token (JWT) session to view profile data. Profile data must not be cached by public proxy servers.

#### Scenario 1: View Profile as Verified Active Shareholder (Happy Path)
* **Given** a logged-in member who has completed e-KYC and purchased initial shares
* **When** the member navigates to the profile tab from the main navigation menu
* **Then** the application retrieves the profile details securely
* **And** displays the full name "Elena Rostova"
* **And** shows the unique Member ID "DCB-9821"
* **And** lists the Join Date as "July, 2026"
* **And** displays the tier badge `Active Shareholder`
* **And** displays a green `Verified` badge

#### Scenario 2: Profile View for Unverified Member (Edge Case)
* **Given** a new user who signed up but has not completed their ID verification
* **When** the user accesses the profile section
* **Then** the system displays their name and Member ID
* **And** renders an orange badge stating `Pending Verification`
* **And** shows a persistent dashboard alert banner: "Complete your identity check to unlock full banking access."

---

## Capability 2: Core Accounts & Share Ledger (CASL)

### US-2.1a: Co-op Share Balance & Voting Weight Visibility (F-201)

#### Business Rules & Data Validation
* **Display Format:** Share balance must show the total quantity of shares owned and the equivalent currency valuation (Base calculation: 1 Share = $10.00).
* **Democratic Rule Representation:** Explicit tooltip displaying the democratic cooperative rule: "One Member, One Vote".
* **Minimum Threshold:** Possession of >= 1 share grants exactly 1 voting weight unit. Possession of > 1 share does not scale voting influence.

#### Scenario 1: Shareholder Accesses Dashboard Share Card (Happy Path)
* **Given** a member is logged in and owns 10 cooperative shares
* **When** the dashboard screen loads
* **Then** a distinct account card for "Co-op Share Account" is displayed
* **And** the card details the balance as "10 Shares ($100.00)"
* **And** displays a text label indicating "Voting Weight: 1 Vote"
* **When** the user taps the info icon next to the voting weight
* **Then** a popover modal displays: "Every member of Digital Coop Bank has equal voting rights. Having one or more shares grants you exactly one vote."

#### Scenario 2: Non-Shareholder Views Dashboard (Edge Case)
* **Given** a user who has completed identity check but has not purchased initial shares
* **When** the dashboard screen loads
* **Then** the Co-op Share card indicates a balance of "0 Shares ($0.00)"
* **And** shows the voting weight status as "0 Votes (Inactive)"
* **And** displays a primary call-to-action button: "Purchase shares to activate membership."

---

### US-2.1b: Initial Share Purchase during Onboarding (F-201)

#### Business Rules & Data Validation
* **Purchase Requirements:** Minimum transaction amount is $10.00 (equivalent to 1 initial share).
* **Funding Integration:** Links external payment instruments via Plaid (ACH) or direct debit card gateways.
* **Ledger Atomicity:** The transaction ledger write and share balance update must execute as an atomic transaction block.
* **State Transition:** Upon transaction success, member state changes from `Pending Capitalization` to `Active Shareholder`.

#### Scenario 1: Completion of Initial Share Purchase (Happy Path)
* **Given** a user is on the onboarding step "Purchase Membership Shares" with status `Pending Capitalization`
* **When** the user selects to pay $10.00 using their linked external debit card
* **And** taps "Confirm Share Purchase"
* **Then** the payment processor captures the $10.00 payment successfully
* **And** the share ledger writes a record credit of 1 share to the member's account
* **And** the member's status is updated to `Active Shareholder`
* **And** the user is redirected to a confirmation page welcoming them as a member

#### Scenario 2: Transaction Fails due to Insufficient External Funds (Negative Path)
* **Given** a user is on the initial share purchase screen
* **When** the user attempts to process the transaction, but the linked external bank account returns an "Insufficient Funds" code
* **Then** the payment gateway declines the transfer
* **And** the share ledger does not issue any new shares
* **And** the member's account remains in the `Pending Capitalization` state
* **And** the application displays an error: "Your payment could not be processed. Please check your card balance or try another payment method."

---

### US-2.3a: Toggle Smart Savings Round-Ups (F-202)

#### Business Rules & Data Validation
* **Rounding Threshold Options:** Nearest $1.00, $2.00, or $5.00.
* **Mandatory Parameters:** User must select a valid savings sub-account as the destination bucket.
* **Persistence:** Changes to the settings must update the `member_preferences` table before UI feedback.

#### Scenario 1: Configuring and Enabling Round-Ups (Happy Path)
* **Given** a member is on the "Savings Settings" screen
* **When** the user toggles "Smart Savings Round-Ups" to ON
* **And** selects a threshold of "$1.00"
* **And** designates the target savings goal account "Green Initiative Fund"
* **And** clicks "Save Preferences"
* **Then** the preferences are saved in the system database
* **And** the app displays a success confirmation: "Round-ups activated for your Green Initiative Fund."

#### Scenario 2: Saving Settings without Target Account (Negative Path)
* **Given** the user is on the savings configuration screen
* **When** the user toggles "Smart Savings Round-Ups" to ON
* **And** selects a threshold of "$2.00"
* **And** leaves the destination account field unselected
* **And** attempts to click "Save Preferences"
* **Then** the system blocks the submission
* **And** highlights the destination account field
* **And** displays a validation error: "A destination savings goal account is required to activate round-ups."

---

### US-2.3b: Automated Transfer of Round-Up Amounts (F-202)

#### Business Rules & Data Validation
* **Trigger Event:** Triggered on credit card/debit card authorization match.
* **Rounding Logic:**
  $$\text{Round Up Amount} = \lceil \text{Purchase Amount} \rceil - \text{Purchase Amount}$$
  *(Calculated relative to the selected threshold).*
* **Transactional integrity:** The transaction checking debit and savings goal credit must use a transactional wrapper. If the savings credit fails, the checking debit must roll back.
* **Insufficient Funds Handling:** If the transaction account balance cannot support the round-up transfer, the round-up must be discarded, but the core card purchase must not be declined.

#### Scenario 1: Processing Round-Up on Card Purchase (Happy Path)
* **Given** a member has round-ups enabled at a "$1.00" threshold targeting "Rainy Day Savings"
* **And** the checking account balance is $50.00
* **When** a card transaction of $12.40 is authorized at a merchant
* **Then** the system deducts $12.40 from the checking balance
* **And** calculates a round-up transfer of $0.60
* **And** debits the checking account by $0.60
* **And** credits the "Rainy Day Savings" account by $0.60
* **And** displays two linked entries in the transaction ledger: "$12.40 Purchase" and "$0.60 Round-Up to Rainy Day Savings"
* **And** the final checking balance is updated to $37.00

#### Scenario 2: Card Purchase of Exact Dollar Amount (Edge Case)
* **Given** the member has round-ups active at a "$1.00" threshold
* **When** a card transaction of $15.00 is authorized
* **Then** the system calculates a round-up amount of $0.00
* **And** processes the purchase of $15.00
* **And** does not trigger any corresponding internal savings transfer

#### Scenario 3: Checking Balance Cannot Cover Round-up (Edge Case/Negative Path)
* **Given** a member has round-ups active at a "$1.00" threshold
* **And** their checking account balance is $20.50
* **When** a card purchase of $20.10 is authorized
* **Then** the system processes the $20.10 deduction (leaving a balance of $0.40)
* **And** calculates a round-up amount of $0.90
* **And** checks if the checking balance ($0.40) can cover the $0.90 transfer
* **Then** the system cancels the round-up transfer due to insufficient checking funds
* **And** leaves the checking account balance at $0.40 without executing any transfers to savings
* **And** logs a silent transaction warning in the backend.

---

## Capability 3: Core Transactions & Payments (CTP)

### US-3.1a: Instant Internal Peer-to-Peer Transfer (F-301)

#### Business Rules & Data Validation
* **Recipient Lookup:** Query directory using `@username` or phone numbers normalized to E.164.
* **Privacy Controls:** Do not expose full legal name during recipient confirmation (expose First Name and Last Initial only).
* **Performance SLAs:** Core ledgers must settle the transfer in less than 3 seconds.
* **Pricing Policy:** Internal transfer fees must always be $0.00.
* **Security Assertion:** Transactions must enforce daily transfer limits (default limit: $2,000.00 per day).

#### Scenario 1: Instant P2P Transfer Processed (Happy Path)
* **Given** a logged-in member with a checking balance of $100.00
* **When** the user searches for `@fabian_k` in the P2P send screen
* **Then** the app queries the user directory and displays the avatar and name card "Fabian K."
* **When** the user inputs an amount of $25.00 and taps "Send Now"
* **Then** the database settles the transaction in 1.8 seconds with $0.00 fees
* **And** reduces the sender's checking balance to $75.00
* **And** updates the recipient's balance instantly
* **And** triggers a push notification to both parties confirming the transfer

#### Scenario 2: Search for Non-existent Recipient Handle (Negative Path)
* **Given** the user is typing a recipient handle in the search box
* **When** the user inputs `@unknown_user_123`
* **Then** the system queries the directory database and finds no matching records
* **And** displays an inline message: "No match found for `@unknown_user_123`. Please check the username and try again."
* **And** the "Next" step remains disabled

#### Scenario 3: Transaction Violates Daily Cumulative Limits (Negative Path)
* **Given** a user has already sent $1,900.00 in P2P transfers today
* **When** the user attempts to send another $150.00 to `@elena_r`
* **Then** the system transaction checker evaluates the total daily volume ($2,050.00) against the limit ($2,000.00)
* **And** rejects the transaction before execution
* **And** displays an error message: "Transaction declined. This transfer would exceed your daily sending limit of $2,000.00. (Remaining today: $100.00)"

---

### US-3.1b: Downloadable Transaction Confirmation Receipt (F-301)

#### Business Rules & Data Validation
* **Required Metadata Fields:** Transaction Timestamp, Unique Transaction Reference ID (UUIDv4), Sender Name/ID, Recipient Name/ID, Amount, Fee ($0.00), Status (`COMPLETED`).
* **Document Specifications:** Must generate a PDF document with standard digital signatures for verification.
* **Device Integration:** Must utilize native OS sharing sheets on iOS and Android.

#### Scenario 1: Generating and Exporting a Transaction Receipt (Happy Path)
* **Given** a user is viewing the details page of a past transaction
* **When** the user clicks the "Download PDF Receipt" button
* **Then** the service compiles the transaction metadata into a PDF layout featuring the "Digital Coop Bank Verified" watermark
* **And** initiates the native mobile sharing sheet allowing the user to save, email, or message the document
* **And** logs the download event for security auditing

#### Scenario 2: Error in Receipt Service Availability (Negative Path/Edge Case)
* **Given** a user is viewing a transaction record details page
* **When** the user attempts to download the receipt but the PDF generator microservice returns a 503 Service Unavailable code
* **Then** the application catches the error gracefully
* **And** displays a temporary warning toast: "Receipt download is temporarily unavailable. We are resolving the issue. Please try again in a few moments."
* **And** ensures the main dashboard remains fully interactive

---

### US-3.3a: Generate Instant Virtual Debit Card (F-302)

#### Business Rules & Data Validation
* **Card Details Generation:** Cryptographically secure generation of 16-digit PAN, CVV2, and expiration date (3 years from date of generation).
* **Access Rules:** User must authenticate with biometric credentials (FaceID/TouchID) or account PIN before card data is generated and displayed on-screen.
* **Account Linkage:** The virtual card must query the primary transactional checking account balance for authorization request logic.

#### Scenario 1: Instantly Creating a Virtual Card (Happy Path)
* **Given** a logged-in member on the "Cards" management tab
* **When** the user clicks "Create Virtual Card"
* **Then** the app requests biometric authentication
* **When** the user successfully validates their biometrics
* **Then** the server issues a new card record linked to the user's primary checking account
* **And** renders a card graphic containing the 16-digit card number, expiration date, and CVV code
* **And** provides a button to copy card details directly to the device clipboard

#### Scenario 2: Virtual Card Generation Aborted due to Auth Failure (Negative Path)
* **Given** the user is initiating virtual card creation
* **When** the biometric authentication dialog appears and the user enters an incorrect PIN 3 times
* **Then** the authentication framework rejects the request
* **And** the card creation process is terminated
* **And** the app returns to the card hub displaying: "Authentication failed. Virtual card creation canceled."

---

### US-3.3b: Temporarily Freeze and Unfreeze Virtual Card (F-302)

#### Business Rules & Data Validation
* **State Values:** Active status changes between boolean flags: `Active = true` (Unfrozen) or `Active = false` (Frozen).
* **Authorization Interceptor:** Any card swipe or payment processor inquiry on a frozen card must yield a decline code `Declined - Card Blocked` immediately without checking account funds.
* **Propagation Latency:** Status changes must update globally in less than 500ms.

#### Scenario 1: Freezing an Active Card (Happy Path)
* **Given** a member has an active virtual debit card with status `Active = true`
* **When** the user views the card settings and toggles "Freeze Card"
* **Then** the app sends the status update to the server
* **And** updates the card's flag to `Active = false`
* **And** changes the card's visual design in the UI to a grayed-out "Frozen" state
* **And** any external transaction authorization requests on the card are instantly returned as declined

#### Scenario 2: Authorization Allowed after Unfreezing Card (Happy Path)
* **Given** a member has a frozen virtual debit card with status `Active = false`
* **When** the user toggles "Freeze Card" to OFF
* **Then** the system updates the database flag to `Active = true`
* **And** restores the visual state of the card in the UI
* **And** future transaction authorization requests are processed against checking account funds

#### Scenario 3: Merchant Transaction Declined on Frozen Card (Edge Case)
* **Given** a member's card is currently set to a "Frozen" state
* **When** an online merchant attempts to execute a pre-authorized payment of $15.00 against the card number
* **Then** the core payment gateway interceptor identifies the card status as inactive
* **And** rejects the charge immediately with response code "Card Blocked"
* **And** sends a push notification to the member's device: "A transaction attempt of $15.00 was blocked because your card is frozen."

---

## Capability 4: Embedded Democratic Governance (EDG)

### US-4.2a: Browse Active Cooperative Proposals (F-401)

#### Business Rules & Data Validation
* **Display Fields:** Proposal ID, Title, Short Description, Category badge (e.g., `Community Grant`, `Cooperative Rules`, `Financial Policy`), Closing Date and Time, Voter Turnout Percentage.
* **State Filters:** Users must be able to switch list views between active voting windows, closed/resolved proposals, and proposals where they have already cast a vote.

#### Scenario 1: Browsing Proposals and Applying Filters (Happy Path)
* **Given** a member is on the "Governance Dashboard"
* **When** the proposal list loads
* **Then** the active proposals list displays cards showing the Title, Category, Closing Date/Time, and Turnout percentage
* **When** the user selects the filter "Closed"
* **Then** the active list is replaced by historical proposals showing final voting tallies and resolution status (e.g., `Passed`, `Defeated`)

#### Scenario 2: Accessing Portal when No Proposals are Active (Edge Case)
* **Given** there are no proposals currently open for vote in the cooperative database
* **When** the member navigates to the active voting portal
* **Then** the application does not display blank spaces or crash
* **And** displays an informational layout: "No active proposals for voting at this time. Check back later or view closed proposals."

---

### US-4.2b: Secure Vote Submission (F-401)

#### Business Rules & Data Validation
* **Vote Choices:** Must support three options: `For`, `Against`, or `Abstain`.
* **Re-Authentication:** The user must confirm their identity via biometric authentication or account PIN before the vote is finalized.
* **Double-Voting Prevention:** The database must enforce a unique composite key constraint `(member_id, proposal_id)` on vote records. Any second vote attempt must throw a constraint violation.
* **Audit Integrity:** Individual votes must be recorded in an encrypted, pseudonymous audit log, decoupling the member's identity from their specific selection to preserve voter privacy while maintaining tally verification.

#### Scenario 1: Submitting a Vote on an Active Proposal (Happy Path)
* **Given** an active shareholder who has not yet voted on Proposal #102
* **When** the member views Proposal #102 details
* **And** selects the choice "For"
* **And** clicks "Submit Vote"
* **Then** the app requests biometric confirmation
* **When** the user successfully authenticates
* **Then** the system registers the vote in the audit ledger
* **And** increments the proposal turnout metrics
* **And** updates the user's local state to show they have voted on Proposal #102
* **And** displays a message: "Your vote has been cast securely."

#### Scenario 2: Prevention of Double Voting (Negative Path)
* **Given** a user has already submitted a vote on Proposal #102
* **When** the user attempts to send another vote selection to the server for Proposal #102
* **Then** the API intercepts the request and verifies the existing vote record
* **And** rejects the submission with a validation error
* **And** displays: "You have already voted on this proposal. Multiple votes are not permitted."

#### Scenario 3: Voting on an Expired Proposal (Negative Path/Edge Case)
* **Given** a member is viewing the detail page of Proposal #102
* **When** the deadline timestamp passes while the user is reading the page
* **And** the user attempt to click "Submit Vote"
* **Then** the server validator rejects the request because the current system time exceeds the proposal close time
* **And** displays an error message: "Voting has closed for this proposal. Votes can no longer be accepted."

---

## Capability 5: Community Lending & Trust Networks (CLTN)

### US-5.1a: Apply for Co-op Microloan (F-502)

#### Business Rules & Data Validation
* **Credit Cap Constraint:** Minimum loan application request is $100.00, maximum MVP loan request is $1,000.00.
* **Valid Term Selections:** Repayment term lengths are restricted to 3, 6, or 12 months.
* **Required Input Fields:** Purpose of loan text field (minimum 20 characters, maximum 500 characters).
* **Initial Status:** Newly submitted applications are recorded with the status `Pending Review`.

#### Scenario 1: Submitting a Completed Loan Application (Happy Path)
* **Given** a member is on the "Microloan Application" form
* **When** the user enters a loan amount of $500.00
* **And** selects a repayment term of "6 months"
* **And** inputs the purpose: "Purchasing replacement laptop for graphic design work"
* **And** reviews the dynamically calculated monthly repayment amount
* **And** clicks "Submit Application"
* **Then** the application is successfully stored in the database with status `Pending Review`
* **And** displays a success message: "Application submitted. The cooperative loan committee will review your request shortly."

#### Scenario 2: Submission Fails due to Missing Mandatory Data (Negative Path)
* **Given** the user is filling out the microloan application
* **When** the user inputs an amount of $500.00 and selects a term of "3 months"
* **And** leaves the "Purpose of Loan" text area completely blank
* **And** attempts to tap "Submit Application"
* **Then** the application highlights the missing field in red
* **And** displays an error message: "Purpose of loan is required. Please explain what the funds will be used for."
* **And** blocks transmission of the application data to the server

#### Scenario 3: Requested Amount Exceeds Platform Cap (Negative Path)
* **Given** a member is entering a loan amount
* **When** the user inputs a value of $1,200.00 in the loan amount field
* **Then** the system triggers immediate inline field validation
* **And** displays a message: "The maximum microloan amount during the pilot phase is $1,000.00."
* **And** disables the "Submit Application" button

---

### US-5.1b: Pre-Screening & Automated Interest Estimation (F-502)

#### Business Rules & Data Validation
* **Scoring Inputs:** Checks Account Tenure (months), Co-op Share Balance, average savings balance, and historical vote participation (percentage of eligible votes cast).
* **Pricing Parameters:**
  * **Base Interest Rate:** 8.00% APR.
  * **Tenure Discount:** -1.00% for accounts active > 6 months.
  * **Share Balance Discount:** -1.00% for holding >= 10 shares.
  * **Voting Discount:** -2.00% for participation rate >= 90%.
  * **Floor Rate:** The maximum cumulative discount cannot reduce the rate below 4.00% APR.

#### Scenario 1: Applying Highest Tier Discounts to Interest Calculation (Happy Path)
* **Given** a member has been with the coop for 12 months (qualifies for tenure discount)
* **And** holds 15 shares (qualifies for share discount)
* **And** has voted in 95% of proposals (qualifies for voting discount)
* **When** the member opens the microloan application calculator
* **Then** the calculation engine calculates the total potential discount of 4.00% (1% + 1% + 2%)
* **And** deducts this from the 8.00% base rate
* **And** displays the estimated interest rate as "4.00% APR (Floor Rate Reached)"
* **And** displays a details card explaining: "Your rate includes: -1.00% Tenure, -1.00% Share Ownership, -2.00% Voting Participation."

#### Scenario 2: Calculated Rate for a New Member with No Discounts (Edge Case)
* **Given** a newly registered member with 1 day of tenure, 1 share, and 0% voting history
* **When** the user views the loan calculator
* **Then** the system calculates a discount of 0.00%
* **And** displays the interest rate as "8.00% APR"
* **And** displays the message: "You are receiving the standard base rate. You can unlock interest discounts by participating in voting and growing your savings."

---

## Capability 6: Dynamic Dividend Engine (DDE)

### US-6.3a: View Cumulative Savings Yield (F-602)

#### Business Rules & Data Validation
* **Data Visualizations:** Chart displaying monthly interest payouts.
* **Dashboard Summary Metrics:** Display cumulative YTD interest earned and the interest earned during the last calendar month.
* **Layout Requirements:** Responsive layout compatible with standard mobile viewport widths (320px to 480px).

#### Scenario 1: Render Interest Yield Chart (Happy Path)
* **Given** a member has been earning savings interest over the last 6 months
* **When** the member navigates to the "Yield Tracker" section
* **Then** the system displays a line chart mapping interest payouts month-by-month
* **And** renders a summary showing the exact dollar value for "Total Interest Year-to-Date" and "Last Month's Payout" matching the ledger databases
* **When** the user taps on a specific data point on the chart
* **Then** a tooltip overlay displays showing the exact month and payout value (e.g., "June 2026: $8.45")

#### Scenario 2: New Account with No Yield History (Edge Case)
* **Given** a user opened their account in the current month and has not yet completed a statement cycle
* **When** the user accesses the "Yield Tracker" page
* **Then** the app renders an empty chart state with a flat horizontal line at $0.00
* **And** displays the metrics as "$0.00"
* **And** displays helper text: "Your interest payouts will start appearing here once your first monthly cycle completes."

---

### US-6.3b: Estimated Cooperative Dividends Projection (F-602)

#### Business Rules & Data Validation
* **Projection Variables:** The current cooperative revenue surplus pool size, the member's proportion of total outstanding shares, and their voting activity multiplier.
* **Legal Compliance:** A disclaimer must accompany projections to prevent guarantee compliance issues.

#### Scenario 1: Displaying a Dividend Projection (Happy Path)
* **Given** a member with 20 shares and a 100% voting participation rate
* **When** the user opens the "Dividend Tracker" screen
* **Then** the engine retrieves the current quarter's cooperative surplus pool estimate ($50,000.00)
* **And** calculates the user's projected share weight
* **And** displays: "Estimated Upcoming Dividend: $42.50"
* **And** displays the disclaimer: "Projections are based on current cooperative earnings and may fluctuate based on quarterly performance."

#### Scenario 2: Dividend Projection when Coop Surplus is Zero (Edge Case)
* **Given** the cooperative has generated no surplus revenue in the current tracking quarter
* **When** the user views the Dividend Tracker screen
* **Then** the app displays: "Estimated Upcoming Dividend: $0.00"
* **And** shows an informational message: "Cooperative surplus is currently zero. Projections will update as quarterly revenue increases."

---

## Capability 7: Transparent Capital Ledger (TCL)

### US-7.1a: Interactive Capital Ledger Chart (F-701)

#### Business Rules & Data Validation
* **Categorization:** Allocation data must resolve to four specific categories: `Green Bonds`, `Local Business Loans`, `Community Infrastructure`, and `Cash Liquidity Reserves`.
* **Mathematical Validation:** The sum of percentages for all categories on the chart must equal exactly 100%.
* **Cache Lifecycle:** Capital allocations data must be cached and updated weekly. The interface must display the date of the last update.

#### Scenario 1: Successful Donut Chart Load (Happy Path)
* **Given** the user is viewing the "Capital Ledger" dashboard
* **When** the page is loaded
* **Then** the system displays a donut chart showing the distribution of total assets under management
* **And** the data categories are labeled: `Green Bonds`, `Local Business Loans`, `Community Infrastructure`, and `Cash Liquidity Reserves`
* **And** the sum of the category percentages displayed equals exactly 100%
* **And** shows a timestamp indicating: "Data updated on [Date of last Sunday]"

#### Scenario 2: Offline/Network Failure Loading Chart Data (Negative Path)
* **Given** a user opens the Capital Ledger tab, but the device has no internet connection
* **When** the API call to fetch ledger data fails
* **Then** the chart displays a placeholder loading state
* **And** displays a message: "Cannot load ledger data. Please check your network connection."
* **And** displays the last successfully cached local data with a prominent warning: "Displaying cached offline data from [Date]."

---

### US-7.1b: Capital Project Spotlights & Details (F-701)

#### Business Rules & Data Validation
* **Granular Drill-Down:** Tapping on a ledger chart category must dynamically filter and display the underlying project cards.
* **Card Attributes:** Project Name (or compliance-approved anonymized code), Short Impact Description, Location, and Total Funded Amount.
* **Detail Modal:** Tapping on a card opens a modal overlay displaying rich text narratives and external verification links if applicable.

#### Scenario 1: Drilling Down into Local Loans Category (Happy Path)
* **Given** a member is on the Capital Ledger dashboard
* **When** the user taps the "Local Business Loans" segment on the donut chart
* **Then** the segment is highlighted
* **And** the list below refreshes to display cards representing projects in that category (e.g., "Organic Farm Expansion", "Cooperative Bakery")
* **When** the user taps the card for "Organic Farm Expansion"
* **Then** the app opens a modal showing: Project Name, Location, Description of environmental benefits, Total Funding ($45,000.00), and a button to visit their web presence.

#### Scenario 2: Selecting Category with No Projects (Edge Case)
* **Given** the user is on the Capital Ledger dashboard
* **When** the user taps the "Cash Liquidity Reserves" segment on the chart
* **Then** the segment is highlighted
* **And** the list below displays: "Liquidity reserves are held in secure, high-quality central cooperative accounts to ensure member withdrawal availability. They do not fund individual community projects directly."
* **And** no individual project cards are shown.