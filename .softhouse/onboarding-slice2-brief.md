# Build brief — Onboarding vertical slice 2 (EP-1: eligibility + ХУР KYC + promotion)

Builds on slice 1 (the onboarding_application draft + repo/service/router foundation).
Adds: the common-bond eligibility check, ХУР/XYP KYC (behind a provider port + mock),
and the draft→Member promotion on KYC approval. STILL stops before share purchase
(which needs the ledger). No money, no ledger.

## Standing facts (CLAUDE.md + PO direction, provisional)
- Common bond = **defined-bond SCC path**; eligibility is **config-driven**
  (`eligibility.common_bond_rules`). The specific bond (employer/association/aimag)
  is NOT chosen — so build a config-driven ENGINE with a sensible DEFAULT rule set,
  not a hard-coded bond.
- eKYC = **ХУР/XYP state-register lookup**, NOT biometric face-match. The provider is
  procurement-TBD → integrate behind a PORT (interface) with a MOCK; no real API call.
- **DEC-4: no member record ever reaches a rejected status.** A Member is created ONLY
  on KYC approval. A rejected/abandoned application leaves NO Member row.
- Three-part names (ovog/etsgiin_ner/ner, never first/last); registration_number
  10-char STRUCTURAL only (no invented check-digit); no float; two time zones no DST.

## The KYC-before-Member reconciliation (important — resolve against 04 + contract)
`KycSubmission` (app/models/identity.py) has a NOT-NULL `member_id` FK — but KYC runs
during the PRE-AUTH onboarding application, before any Member exists (DEC-4). Therefore:
- In-flight KYC state (kyc_inquiry_id, kyc_status) lives on the **onboarding_application
  draft**, NOT in a KycSubmission row. Add the needed columns to the draft (model +
  migration, gate-coupled) OR store on its `onboarding_state` JSON — prefer real columns
  for `kyc_inquiry_id` (unique) and `kyc_status` since the contract returns them; justify
  your choice.
- The member-linked `KycSubmission` row is created at **promotion** (approval), when a
  Member finally exists, carrying the evidence/result.
- Confirm this against 04 §2/§3.1 and the contract; if 04 models it differently, follow
  04 and flag.

## Scope of THIS slice — implement to the EXISTING contract (ep1-identity.yaml)
1. **checkOnboardingEligibility** (POST /onboarding/applications/eligibility, 200):
   evaluate `EligibilityCheckRequest.answers` against config-driven common_bond_rules;
   return `EligibilityCheckResponse` (eligible/ineligible + reasons). A small config
   source (a default rule set; optionally readable from ConfigurationParameter later —
   do NOT build the US-12.5 admin CRUD now). Records the outcome on the draft.
2. **createKycSession** (POST …/kyc/sessions, 201): start a KYC session via the eKYC
   PORT (mock ХУР/XYP state-register lookup); store kyc_inquiry_id + set kyc_status
   IN_PROGRESS on the draft; return `KycSessionResponse`.
3. **getKycStatus** (GET …/kyc/status, 200): return `KycStatusResponse` (re-read /
   re-poll the port as the contract implies). The MOCK drives NOT_STARTED → IN_PROGRESS
   → APPROVED / PENDING_REVIEW / REJECTED deterministically (e.g. by a field in the
   request or a config toggle) so tests can exercise every branch.
4. **Promotion** (on KYC APPROVED): create a `Member` from the draft (copy DEC-6 name +
   registration_number), membership_status **PENDING_KYC → PENDING_PAYMENT**; create the
   member-linked `KycSubmission` with the result/evidence. NEVER create a Member for a
   REJECTED result (DEC-4). STOP at PENDING_PAYMENT — do NOT do share purchase (ledger).
5. Clean up slice-1 leftovers: implement the 409 REGISTRATION_NUMBER_MISMATCH code where
   the contract declares it (at the SUBMITTED transition), and add the missing tests
   (PATCH non-resolving-token → 401; create CHANNEL_UNVERIFIED → 422).

## Foundation reuse (do NOT re-invent slice-1 patterns)
- Reuse BaseRepository / the onboarding repo / OnboardingService / the router / the
  Error envelope / the bootstrap-token dependency. Add an `app/adapters/ekyc/` port +
  mock. Keep logic in services, not routers. Repos never commit; routers commit on
  mutation (slice-1 convention).

## OUT OF SCOPE
Share purchase / MembershipShare issuance (ledger); MFA/step-up; devices; profile;
consents CRUD (record consent minimally only if the KYC flow requires it); any money;
the ConfigurationParameter admin CRUD (US-12.5).

## Gates (from backend/, ALL must PASS; paste outputs in handoff)
`python3 -m app.db.check_models`, `python3 -m app.db.check_migration` (if you extend the
draft schema, model+migration in lockstep), `python3 openapi/validate.py`,
`python3 -m pytest -q` (add tests: eligibility eligible/ineligible; KYC session→status
through every mock outcome; promotion creates a PENDING_PAYMENT Member + KycSubmission on
APPROVED and creates NO Member on REJECTED; + the 2 slice-1 gap tests). ruff + mypy
strict clean on new files.

## Handoff
The KYC-before-Member design decision (+ 04/contract reconciliation); every new file +
role; each endpoint's contract-conformance; the eKYC port/mock design + how tests drive
outcomes; the promotion logic + the DEC-4 guarantee (no Member on reject); all gate
outputs verbatim.
