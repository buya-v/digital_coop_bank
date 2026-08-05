# EP-2 Share Purchase (US-2.1) — Build Readiness

- **Document ID:** ep2-share-purchase-readiness
- **Status:** DRAFT — planning/design document, no implementation
- **Author:** Softhouse analyst agent, run `20260805-ep2-readiness`, task T1
- **Date:** 2026-08-05
- **Upstream sources of truth:** `backend/openapi/paths/ep2-shares.yaml`, `backend/openapi/schemas/ep2-shares.yaml`, `backend/app/models/ledger.py`, `backend/app/models/membership.py`, `idea-lab/final_requirements/03_acceptance_criteria.md` (EP-2), `idea-lab/final_requirements/06_ledger_addendum.md` §4.1/§7.3, `idea-lab/final_requirements/01_business_analysis.md` §6 (DEC-4, DEC-11), `CLAUDE.md`
- **Purpose:** inventory what already exists for EP-2/US-2.1 (`PENDING_PAYMENT → ACTIVE`), map it against the `03` acceptance criteria, and split the remaining work into what can be built **now** versus what is blocked on **U1** (controller ratification of `06_ledger_addendum.md`). This document implements nothing; it authors no code and edits no contract/model/requirements file.

**Honesty convention used throughout:** every material claim is tagged `[VERIFIED: file:line]` (I opened the file and read the cited line(s)) or `[UNVERIFIED]` (asserted in a document but not independently confirmed, or a reasonable inference I could not confirm by reading source). Where I looked for something and did not find it, I say "not found" rather than describing it.

---

## 1. Inventory — what exists today

### 1.1 OpenAPI contract — `EP-2` tag (`backend/openapi/paths/ep2-shares.yaml`)

The contract defines **10** EP-2 operations, not 4 — the four money/read ops named in the task plus six more (membership summary, closure, admin registry, admin governance ops). All ten are listed for completeness; the task's four are marked **★**.

| Operation | Method/path | Security | Idempotency-Key | Declared responses | Evidence |
|---|---|---|---|---|---|
| ★ `purchaseMembershipShare` | `POST /api/v1/onboarding/share-purchase` | memberOAuth2 (document default) | **required** (header, UUID, explicit param) | 200, 401, 402 `PAYMENT_FAILED`, 403, 409 `WRONG_MEMBERSHIP_STATE`/`IDEMPOTENCY_CONFLICT`, 422 `AMOUNT_MISMATCH`, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:9-66]` |
| ★ `getSharePurchaseStatus` | `GET /api/v1/onboarding/share-purchase/{transaction_id}` | memberOAuth2 | n/a (read) | 200, 401, 404, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:68-93]` |
| `getMyMembership` | `GET /api/v1/members/me/membership` | memberOAuth2 | n/a | 200, 401, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:95-111]` |
| ★ `listMyShares` | `GET /api/v1/members/me/shares` | memberOAuth2 | n/a | 200, 401, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:113-131]` |
| `getClosurePreconditions` | `GET /api/v1/members/me/closure-preconditions` | memberOAuth2 | n/a | 200, 401, 403, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:133-151]` |
| `createClosureRequest` | `POST /api/v1/members/me/closure-requests` | memberOAuth2 **+ stepUpAssertion** | **required** (marked INFERRED — §3.2 row doesn't list it, but §3.0 mandates it for money-movement POSTs) | 200, 401, 403, 409 `PRECONDITIONS_NOT_MET`, 422, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:153-202]` |
| ★ `getShareRegistry` | `GET /api/v1/admin/shares/registry` | staffSSO | n/a | 200, 401, 403, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:204-227]` |
| `createEligibilitySnapshot` | `POST /api/v1/admin/ballots/{ballot_id}/eligibility-snapshot` | staffSSO | n/a | 201, 401, 403, 409, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:229-267]` |
| `createMemberStatusTransition` | `POST /api/v1/admin/members/{id}/status-transitions` | staffSSO | n/a | 200, 401, 403, 409 `PENDING_TRANSITION_EXISTS`, 422 `ILLEGAL_TRANSITION`, 429 | `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:269-317]` |
| `paymentsWebhook` (not EP-2-tagged, but drives US-2.1 activation) | `POST /api/v1/webhooks/payments` | none (provider-authenticated) | ack is idempotent | 200, 401 `SIGNATURE_INVALID`, 409, 422 `AMOUNT_MISMATCH` | `[VERIFIED: backend/openapi/paths/webhooks.yaml:80-125]` |

Key schema facts (`backend/openapi/schemas/ep2-shares.yaml`):
- `amount`/`par_value` are `int64` MNT minor units; the contract explicitly does **not** pin a default — "US-12.5 configuration (DEC-11), never a hard-coded contract constant" `[VERIFIED: backend/openapi/schemas/ep2-shares.yaml:58-65,102-108]`.
- `SharePurchaseResponse.membership_status` is `allOf`-pinned to the literal `"ACTIVE"` on settlement `[VERIFIED: backend/openapi/schemas/ep2-shares.yaml:135-138]`.
- `MembershipRights{vote,borrow,guarantee}` booleans back `getMyMembership` `[VERIFIED: backend/openapi/schemas/ep2-shares.yaml:162-174]`.
- `ClosurePreconditions.blockers[]` enum: `ACTIVE_OR_DELINQUENT_LOAN | LOCKED_GUARANTEE_PLEDGE | GROUP_POT_MEMBERSHIP | NONZERO_BALANCES` `[VERIFIED: backend/openapi/schemas/ep2-shares.yaml:220-227]`.
- `MemberStatusTransitionRequest.target_status` explicitly says "Illegal transitions rejected" — this is the DEC-4 guard surface for the admin maker-checker path `[VERIFIED: backend/openapi/schemas/ep2-shares.yaml:354-357]`.

### 1.2 Models

`backend/app/models/membership.py`:
- `MembershipStatus` enum: `PENDING_KYC, PENDING_PAYMENT, ACTIVE, SUSPENDED, CLOSED` — names equal values `[VERIFIED: backend/app/models/membership.py:23-30]`.
- `ShareClass` enum: `MEMBERSHIP, REINVESTED_PATRONAGE` — names equal values `[VERIFIED: backend/app/models/membership.py:33-37]`.
- `ShareStatus` enum: `MEMBER = "ISSUED"`, `REDEEMED = "REDEEMED"` — **name/value mismatch on the first member** (Python name `MEMBER` maps to wire value `"ISSUED"`) `[VERIFIED: backend/app/models/membership.py:40-42]`. See Gap G-6.
- `Member` (E-1): `membership_status` column present; **no `kyc_status` column** on `Member` `[VERIFIED: backend/app/models/membership.py:45-103 — full file read, no kyc_status field]`. `kyc_status` instead lives on the pre-auth `OnboardingApplication` draft `[VERIFIED: backend/app/models/identity.py:239-240]`. This is consistent with DEC-4 (a Member is created only on KYC approval, so by construction an existing Member's KYC is APPROVED) — not a defect, just worth knowing when building the `purchaseMembershipShare` precondition check.
- `MembershipShare` (E-5): `id, member_id, certificate_number, par_value(MoneyMinor), share_class, status, issued_at, redeemed_at` `[VERIFIED: backend/app/models/membership.py:105-121]`. **No `subscription_transaction_id` / `redemption_transaction_id` FK columns** — see Gap G-1.
- No `MembershipShare` repository exists anywhere in `backend/app` `[VERIFIED: grep -rl "MembershipShare" app --include=*.py returned only models/membership.py and a comment in services/kyc.py:18]`.

`backend/app/models/ledger.py`:
- `Account` (E-6): `owner_member_id, account_number, account_type, balance, available_balance, status, opened_at, closed_at` `[VERIFIED: backend/app/models/ledger.py:55-71]`. `balance`/`available_balance` are explicitly documented as materialized-but-unwritten placeholders — "Nothing may write them directly; ... lives in that service, not here" `[VERIFIED: backend/app/models/ledger.py:10-14]`. **No `system_account_code` column** — see Gap G-2.
- `AccountType` enum: `MEMBERSHIP_SHARE, PRIMARY_SAVINGS, TRANSACTION, GROUP_POT, SYSTEM` `[VERIFIED: backend/app/models/ledger.py:38-47]` — `SYSTEM` is a single placeholder value; the chart-of-accounts breakdown (1010, 1000, 5400, 3000, …) does not exist as distinct rows/types yet, by design (`06`'s chart of accounts is not implemented).
- `Transaction` (E-8): `idempotency_key, type(DeferredEnum/String), status, amount, external_ref, settled_at`, plus `created_at/updated_at` via the `Timestamps` mixin `[VERIFIED: backend/app/models/ledger.py:74-86, db/base.py:39-45]`. `type` is deliberately a `String`, not an enum — the value set (incl. `SHARE_SUBSCRIPTION`) is held pending the corrected design `[VERIFIED: backend/app/models/ledger.py:18-19,81]`.
- `LedgerEntry` (E-7): `transaction_id, account_id, direction(DEBIT/CREDIT), amount, entry_type(DeferredEnum/String), sequence, posted_at` `[VERIFIED: backend/app/models/ledger.py:88-108]`. No `posting_class` (FINANCIAL/MEMO_HOLD/ATTRIBUTION) column — that's a `06` §8.2 amendment not yet applied to the model, consistent with "structure only."
- No posting logic, no double-entry enforcement, no balance derivation anywhere in `backend/app` — confirmed by the module docstring itself and by grep (`SHARE_SUBSCRIPTION`, `purchaseMembershipShare`, `share`, `ledger` all absent from `app/api/routers/` and `app/services/` except comments noting the boundary) `[VERIFIED: grep -rni "share|ledger|purchaseMembership|SHARE_SUBSCRIPTION" backend/app/api/routers backend/app/services — only doc-comment hits, no code]`.

### 1.3 EP-1 patterns to reuse

These are real, running patterns in `backend/app` today; the EP-2 build should mirror them rather than invent new shapes.

| Pattern | Where it lives now | What it does |
|---|---|---|
| repositories → services → routers, router owns the commit | `app/repositories/{base,membership,onboarding,identity}.py`, `app/services/{onboarding,eligibility,kyc}.py`, `app/api/routers/onboarding.py` | `BaseRepository.get/add/flush` never commits; the router commits on success `[VERIFIED: backend/app/repositories/base.py:1-45]`. `onboarding.py` router shows the full shape end-to-end `[VERIFIED: backend/app/api/routers/onboarding.py:190-393]`. |
| External integration behind a **PORT + deterministic MOCK**, swapped via `app.dependency_overrides` | `app/adapters/ekyc/{port,mock}.py`, `app/adapters/sms/{port,mock}.py` | Abstract provider class + dataclass request/response objects + a construction-time-scripted mock; the router injects the provider via a `Depends(get_ekyc_provider)`-style seam `[VERIFIED: backend/app/adapters/ekyc/port.py:1-94; backend/app/api/routers/onboarding.py:176-184]`. This is the template for a future payments port. |
| Uniform-401/403, no status leakage | `require_active_member` in `app/auth/deps.py:132-157` | **Already exists and is already exactly the mechanism the "suspended member blocked, no status leakage" AC needs**: it composes `get_current_member` (uniform 401 for unknown/CLOSED subject) then requires `membership_status == ACTIVE`, else uniform `403 MEMBER_NOT_ACTIVE` for SUSPENDED, PENDING_PAYMENT, or PENDING_KYC alike `[VERIFIED: backend/app/auth/deps.py:132-157]`. Its own docstring says it is built but **not yet wired into any router** — "AVAILABLE for future money/ledger routes; apply it ONLY where clearly correct" `[VERIFIED: backend/app/auth/deps.py:145]`. Confirmed unused: no router currently imports it `[VERIFIED: grep -rn "require_active_member" backend/app/api/routers — no hits outside auth/deps.py itself]`.
| Row-lock + re-read idempotency guard for a concurrent state promotion | `OnboardingApplicationRepository` (name inferred from usage) `.get_...locked` in `app/repositories/onboarding.py:55-81` | `SELECT ... FOR UPDATE` + `populate_existing=True` to serialize a concurrent read-modify-write across two requests racing the same promotion (`04`'s "two concurrent getKycStatus polls" case) `[VERIFIED: backend/app/repositories/onboarding.py:55-81]`. Directly reusable for `PENDING_PAYMENT → ACTIVE` promotion (settlement webhook vs. synchronous purchase-response racing, or two settlement redeliveries — US-2.1 Scenario 3). |
| Config-driven, never-hard-coded policy value | `app/config.py:get_common_bond_rules()` | A module-level default constant + a `get_*()` accessor documented as "the single seam a later ConfigurationParameter-backed loader (US-12.5) would replace" `[VERIFIED: backend/app/config.py:90-97]`. Directly reusable shape for a future `get_share_par_value()`. |
| `ApiError` uniform error envelope | `app/api/errors.py` (used throughout `onboarding.py`) | `ApiError(status, code, message, details=...)` raised from the router, matching the contract's `Error` schema `[VERIFIED: backend/app/api/routers/onboarding.py:167-172,207-212,264-296 — repeated ApiError(...) call sites]`. |

---

## 2. US-2.1 (and full EP-2) acceptance map

`03_acceptance_criteria.md` §EP-2 has exactly **16** scenarios across 4 stories (US-2.1–US-2.4) `[VERIFIED: idea-lab/final_requirements/03_acceptance_criteria.md:195-306 — 4 scenarios per story × 4 stories]`, matching the "~16" the task cited.

| Scenario | Component that must satisfy it | Status |
|---|---|---|
| **US-2.1 S1** — card payment settles → 10,000₮ posts to Membership Share Account, status → `ACTIVE`, Member ID + confirmation pack issued, rights activate `[VERIFIED: 03:199-205]` | `purchaseMembershipShare` handler + `SHARE_SUBSCRIPTION` posting + promotion | **TO-BUILD, ledger-gated** (the posting and the resulting `ACTIVE` transition both depend on `06` §4.1) |
| **US-2.1 S2** — payment declined → no ledger entry, status stays `PENDING_PAYMENT`, retry allowed `[VERIFIED: 03:207-212]` | `purchaseMembershipShare` 402 path / `paymentsWebhook` failure path | **Split**: the "stay `PENDING_PAYMENT`, retry" behavior is a status no-op (buildable now); "no entry posts" is trivially true only once the ledger call exists, so end-to-end proof is ledger-gated |
| **US-2.1 S3** — duplicate settlement webhook → idempotent, exactly one share/one credit `[VERIFIED: 03:214-218]` | Idempotency-Key / webhook idempotent-ack handling + `SHARE_SUBSCRIPTION` (must not double-post) | **Ledger-gated** (the "exactly one credit" assertion is a ledger-correctness claim) — the Idempotency-Key *plumbing* itself (header validation, replay detection, `409 IDEMPOTENCY_CONFLICT` on mismatched replay) is buildable now |
| **US-2.1 S4** — API bypass pre-KYC-approval → `403`, no payment initiated, no ledger entry, audit log `[VERIFIED: 03:220-225]` | Status-transition guard on `purchaseMembershipShare` | **Buildable now** (see Gap G-4 for a real ambiguity in this scenario's premise) |
| **US-2.2 S1** — `ACTIVE` member: vote/borrow/guarantee all permitted, server-side `[VERIFIED: 03:229-233]` | `require_active_member`-style guard on the vote/loan/guarantee endpoints (not EP-2's own routes, but consumes EP-2's status) | **Buildable now** — mechanism (`require_active_member`) already exists `[VERIFIED: backend/app/auth/deps.py:132-157]`; the vote/loan/guarantee endpoints themselves are other epics, out of this doc's scope |
| **US-2.2 S2** — `SUSPENDED` blocks vote/borrow/guarantee with `403` + reason, record still viewable `[VERIFIED: 03:235-240]` | Same `require_active_member` guard | **Buildable now** |
| **US-2.2 S3** — illegal transition (`CLOSED→ACTIVE`, `PENDING_KYC→ACTIVE`) rejected everywhere with `409` naming from/to states `[VERIFIED: 03:242-246]` | DEC-4 transition-guard (both the admin `createMemberStatusTransition` maker step, `422 ILLEGAL_TRANSITION`, and any internal caller) | **Buildable now** — pure status-machine logic, no ledger dependency. Note the AC's error code (`409`) does not match the contract's declared code for the analogous admin op (`422 ILLEGAL_TRANSITION`) — see Gap G-5. |
| **US-2.2 S4** — reinstatement (`SUSPENDED→ACTIVE`) via maker-checker restores rights immediately `[VERIFIED: 03:248-252]` | `createMemberStatusTransition` (maker) + a checker-approval step (not in this contract file — likely EP-12 admin) | **Buildable now** for the status flip itself; the maker-checker approval workflow/entity (`MakerCheckerApproval`, E-53) is outside `ep2-shares.yaml` — not inventoried here |
| **US-2.3 S1** — eligibility snapshot at ballot open captures exactly the `ACTIVE` set `[VERIFIED: 03:256-260]` | `createEligibilitySnapshot` | **Buildable now** — reads `Member.membership_status`, no ledger dependency |
| **US-2.3 S2** — registry/ledger reconciliation mismatch flagged `[VERIFIED: 03:262-266]` | `getShareRegistry.equity_ledger_reconciliation` vs L-4 | **Ledger-gated** — by definition requires `balance(3000)` |
| **US-2.3 S3** — member activated after snapshot excluded, `403` reason "not in the eligibility snapshot" `[VERIFIED: 03:268-272]` | Snapshot membership check | **Buildable now** |
| **US-2.3 S4** — one vote regardless of additional holdings `[VERIFIED: 03:274-278]` | Voting-weight logic (binary, ignores share count) | **Buildable now** in principle; moot until voluntary/reinvested shares exist (also ledger-adjacent) |
| **US-2.4 S1** — clean closure: balances swept, share redeemed at par, status → `CLOSED` `[VERIFIED: 03:282-287]` | `createClosureRequest` + `SHARE_REDEMPTION` posting | **Ledger-gated** |
| **US-2.4 S2** — closure blocked by active loan `[VERIFIED: 03:289-294]` | `getClosurePreconditions` `ACTIVE_OR_DELINQUENT_LOAN` blocker | **Buildable now** if loan status is itself a non-ledger status field (EP-6 is deferred per CLAUDE.md anyway, so this is moot for now) |
| **US-2.4 S3** — closure blocked by locked guarantee pledge `[VERIFIED: 03:296-300]` | `LOCKED_GUARANTEE_PLEDGE` blocker | **Ledger-gated** (a "locked pledge" is a `MEMO_HOLD` posting under `06` §3, which doesn't exist yet) |
| **US-2.4 S4** — closure blocked by unresolved Group Pot `[VERIFIED: 03:302-306]` | `GROUP_POT_MEMBERSHIP` blocker | **Buildable now** if Group Pot membership is a non-balance status field; **ledger-gated** for the `NONZERO_BALANCES` blocker specifically, since that reads `Account.balance` |

---

## 3. The `06` posting rule (ratification-gated) — reproduced, not implemented

> **DO NOT IMPLEMENT until U1 (controller ratification).** The following is reproduced verbatim in substance from `idea-lab/final_requirements/06_ledger_addendum.md` for planning reference only. `06` remains do-not-implement per `CLAUDE.md` and `.softhouse/patterns.md` ("Do not implement from `final_requirements/06_ledger_addendum.md`"). No code in this repository may encode this rule until a controller/core-banking engineer signs off the design (U1, see `CLAUDE.md` "Known defects in the baseline").

**`SHARE_SUBSCRIPTION` posting rule** `[VERIFIED: idea-lab/final_requirements/06_ledger_addendum.md:179-192]`:

| Type | Stage | Dr | Cr |
|---|---|---|---|
| `SHARE_SUBSCRIPTION` | collection (US-2.1) | `1010` Payment-Processor Clearing | Member `SHARE` (`3000` Member Share Capital control) |
| `SHARE_SUBSCRIPTION` | processor remittance | `1000` FBO Cash **and** `5400` Payment Processing Fees | `1010` Payment-Processor Clearing |
| `SHARE_REDEMPTION` | closure at par (DEC-11) | Member `SHARE` | Member `SAV` (`PRIMARY_SAVINGS`) |
| `SHARE_SUBSCRIPTION_REFUND` | aborted application | Member `SHARE` | `1010` Payment-Processor Clearing |

The remittance leg is **split, net of fees**: because the payment processor remits net of its fee, `1010` clears via two legs (`1000` cash + `5400` fee expense) against the original `1010` collection, not a single par-for-par leg — "posting par against par would leave 1010 permanently uncleared" `[VERIFIED: 06:188]`.

**Invariant L-4**: `count(ISSUED shares) × par_value = balance(3000)`, checked by US-2.3 `[VERIFIED: 06:192]`. Also enforced as a nightly integrity check `[VERIFIED: 06:543]`.

Account definitions referenced above `[VERIFIED: 06:67-71,98]`:
- `1010` Payment-Processor Clearing — "Share-subscription collections in flight (US-2.1)."
- `1000` FBO Cash at Sponsor Bank — "the reconciliation anchor."
- `5400` Payment Processing Fees — "Payment-processor fees withheld from remittance (§4.1)."
- `3000` Member Share Capital — "Control for `MEMBERSHIP_SHARE`, at DEC-11 par ... par is a US-12.5 config seed, never hard-coded."

None of `1010`, `1000`, `5400`, `3000` (nor the `system_account_code`/`account_category`/`normal_balance` columns needed to represent them) exist in `backend/app/models/ledger.py` today `[VERIFIED: backend/app/models/ledger.py:38-71 — AccountType has only one SYSTEM placeholder, no chart-of-accounts fields]`. This box exists so that when U1 lands, the account numbers and the net-of-fees split are already pinned and don't need re-deriving from `06` again.

---

## 4. THE SPLIT

### 4.1 Ratification-independent (buildable now)

| Item | AC scenario(s) | File it would live in |
|---|---|---|
| `amount == configured par` validation → `422 AMOUNT_MISMATCH` | US-2.1 (contract row; not a literal `03` scenario — see Gap G-3) | `app/services/shares.py` (new) — validate against `app.config.get_share_par_value()` (new, mirroring `get_common_bond_rules()` `[VERIFIED: backend/app/config.py:90-97]`) |
| `Idempotency-Key` header handling: required-header check, replay-with-same-payload → original response, replay-with-different-payload → `409 IDEMPOTENCY_CONFLICT` | US-2.1 S3 (the plumbing half) | `app/api/routers/shares.py` (new router) for the header contract; a lightweight idempotency-record store (could reuse the existing `Transaction.idempotency_key` unique column structurally — see note below — or a dedicated table) in `app/repositories/` |
| DEC-4 status-transition guard: `PENDING_PAYMENT`-only precondition on `purchaseMembershipShare` (`409 WRONG_MEMBERSHIP_STATE` otherwise), and the general "illegal transition rejected" rule for `createMemberStatusTransition` (`422 ILLEGAL_TRANSITION`) | US-2.1 S4, US-2.2 S3 | A new `app/services/membership_transitions.py` (or extend `services/membership.py`) encoding the DEC-4 adjacency list (`PENDING_KYC→PENDING_PAYMENT→ACTIVE`; `ACTIVE↔SUSPENDED`; `ACTIVE/SUSPENDED→CLOSED`) `[VERIFIED: idea-lab/final_requirements/01_business_analysis.md:360]` |
| Suspended/non-active member blocked with uniform `403`, no status leakage | US-2.2 S2 | **Already built**, just needs wiring: `require_active_member` in `app/auth/deps.py:132-157` — apply it to whichever future vote/loan/guarantee routes need it (not an EP-2 route itself) |
| Payment initiation behind a PORT + MOCK (eKYC-style) | US-2.1 S1/S2 (the initiation half, not settlement) | `app/adapters/payments/port.py` + `app/adapters/payments/mock.py` (new), mirroring `app/adapters/ekyc/port.py:1-94` — an abstract `PaymentProvider` with `initiate(...)`/`get_status(...)`, a deterministic mock the tests script |
| `getSharePurchaseStatus` polling (status of a `Transaction` row: `PENDING/SETTLED/FAILED`) | US-2.1 (all, as a read) | `app/api/routers/shares.py` — reads the `Transaction` row created at purchase-initiation time; does not require the ledger posting to exist, only the `Transaction` row's `status` field, which the model already carries `[VERIFIED: backend/app/models/ledger.py:74-86]` |
| `getMyMembership` (status + rights + practical-meaning copy) | US-2.2 S1/S2 | `app/api/routers/shares.py` — pure `Member.membership_status` read, `rights{vote,borrow,guarantee}` derived by the same status→boolean mapping the transition guard uses; no ledger read |
| `listMyShares` read path (mechanism only — returns whatever `MembershipShare` rows exist, which will be empty until ledger-gated issuance runs) | US-2.1 (read side), US-2.3 S4 | `app/repositories/shares.py` (new `MembershipShareRepository`) + `app/api/routers/shares.py` — queries the existing structure-only `MembershipShare` table `[VERIFIED: backend/app/models/membership.py:105-121]`; `total_equity` sums `par_value` across the member's own rows (not an `Account.balance` read) |
| `createEligibilitySnapshot` | US-2.3 S1/S3 | `app/services/governance.py` or similar (new) — snapshots `Member.membership_status == ACTIVE`, no ledger read |
| `getClosurePreconditions` blockers other than `NONZERO_BALANCES` (`ACTIVE_OR_DELINQUENT_LOAN`, `LOCKED_GUARANTEE_PLEDGE`, `GROUP_POT_MEMBERSHIP`) — **to the extent** those other epics expose non-ledger status fields; EP-6 (lending) is itself deferred per `CLAUDE.md`, so this is largely moot pre-EP-6 | US-2.4 S2/S3/S4 | out of EP-2's own files; noted for completeness |

**Note on Idempotency-Key storage**: the natural persistent home for an idempotency key is `Transaction.idempotency_key` (already a unique column, structure-only, no posting logic attached) `[VERIFIED: backend/app/models/ledger.py:80]`. Creating a `Transaction` row with `status=PENDING` to record "we saw this key" does **not** require any `LedgerEntry` — `LedgerEntry` is the double-entry posting; `Transaction` is just the business-level record. This is a **design proposal for the eventual build**, not a verified existing capability — flagged as such rather than presented as fact.

### 4.2 Ledger-gated (needs U1)

| Item | AC scenario(s) | Why it's gated |
|---|---|---|
| `SHARE_SUBSCRIPTION` double-entry posting (collection + net-of-fees remittance legs) | US-2.1 S1 | Directly `06` §4.1 — the exact thing U1 must ratify |
| `PENDING_PAYMENT → ACTIVE` activation **on settlement** (as opposed to the status-machine mechanics, which are gate-independent) | US-2.1 S1 | The activation is defined as happening "on settlement," and "settlement" is a ledger posting event (`06` §4.1 "processor remittance" stage / `paymentsWebhook`'s `payment_intent.succeeded` handler `[VERIFIED: backend/openapi/paths/webhooks.yaml:87-91]`) |
| `SHARE_SUBSCRIPTION_REFUND` (aborted-application refund) | 04 §4.4 (referenced, not a `03` EP-2 scenario) | Same posting-rule dependency |
| `SHARE_REDEMPTION` (closure payout at par) | US-2.4 S1 | `06` §4.1 posting rule |
| L-4 enforcement (`count(ISSUED) × par = balance(3000)`) | US-2.3 S2 | Needs `balance(3000)`, a materialized/derived ledger quantity that doesn't exist until the ledger service is built |
| `getShareRegistry.equity_ledger_reconciliation` | US-2.3 S2 | Same — reads ledger balances by definition |
| `NONZERO_BALANCES` closure blocker | US-2.4 (implicit in S1's "no balance") | Reads `Account.balance`, materialized-but-unwritten today |
| `LOCKED_GUARANTEE_PLEDGE` closure blocker | US-2.4 S3 | A "lock" is a `MEMO_HOLD` posting under `06` §3 — doesn't exist without the hold-posting machinery |
| Exactly-once idempotent posting proof (US-2.1 S3's "exactly one 10,000₮ credit") | US-2.1 S3 | The plumbing (header/replay handling) is gate-independent, but proving "exactly one credit posted" is inherently a ledger-correctness claim |

---

## 5. Gaps / risks found

Each finding below is something I actually located by reading the cited files — not a generic risk list.

**G-1 — `MembershipShare` model is missing the FKs `04` requires for ledger reconciliation.**
`04_technical_architecture.md` §2.2 E-5 specifies `subscription_transaction_id FK→Transaction` and `redemption_transaction_id? FK→Transaction` "reconciles the registry to the equity ledger (US-2.3)" `[VERIFIED: idea-lab/final_requirements/04_technical_architecture.md:182]`. `backend/app/models/membership.py`'s `MembershipShare` class has no such columns `[VERIFIED: backend/app/models/membership.py:105-121, full class read]`. Without these FKs, `getShareRegistry`'s `equity_ledger_reconciliation` and US-2.3 S2's mismatch-detection have no join key back to the `Transaction` that created/redeemed the share. This needs a migration when the ledger build starts — flag for the eventual builder, not fixable in this doc (it would be an edit to `membership.py`, out of scope here).

**G-2 — `Account` model is missing the `system_account_code` (and related chart-of-accounts) columns `06` requires.**
`06` §2/§8.1 requires a `system_account_code` String (nullable, "required when `account_type = SYSTEM`"), plus `account_category`, `normal_balance`, `gl_control_code` `[VERIFIED: idea-lab/final_requirements/06_ledger_addendum.md:61,581]`. `backend/app/models/ledger.py`'s `Account` has none of these `[VERIFIED: backend/app/models/ledger.py:55-71]`. This is expected — `06` is do-not-implement — but it means the `1010`/`1000`/`5400`/`3000` account numbers referenced in §3's posting box have **no representable row** in the current schema at all; the schema amendment itself is part of what U1 must also bless.

**G-3 — the `03` acceptance criteria never literally test `422 AMOUNT_MISMATCH` for US-2.1, despite `05`'s summary claiming they do.**
`05_prd_and_roadmap.md` line 53 asserts "AC themes (03 EP-2, 16 scenarios): amount must equal configured par (`422 AMOUNT_MISMATCH`)..." `[VERIFIED: idea-lab/final_requirements/05_prd_and_roadmap.md:53]`. But I read all four US-2.1 scenarios verbatim `[VERIFIED: idea-lab/final_requirements/03_acceptance_criteria.md:199-225]` and none of them is a "wrong amount" Given/When/Then — the closest is the *preamble* prose above Scenario 1 ("client-supplied amounts are ignored/rejected") which names no HTTP status or error code `[VERIFIED: 03:197]`. `AMOUNT_MISMATCH` as a string appears nowhere in `03_acceptance_criteria.md` (`grep -c` over the whole file = 0) `[VERIFIED: grep -n AMOUNT_MISMATCH idea-lab/final_requirements/03_acceptance_criteria.md returned no lines]`. The error code is real (declared in `04` and the contract), but `05`'s "16 scenarios" summary overstates what's literally in `03`. A future test-writer building this AC would need to author a 5th US-2.1 scenario rather than find one ready-made.

**G-4 — `03` US-2.1 Scenario 4's premise is hard to reach given how `DEC-4`/`kyc.py` actually behave.**
Scenario 4 posits "a client authenticated to an application with `KycStatus=PENDING_REVIEW` (so `MembershipStatus=PENDING_KYC`)" POSTing to share-purchase and getting `403` `[VERIFIED: idea-lab/final_requirements/03_acceptance_criteria.md:220-225]`. But: (a) `purchaseMembershipShare` is secured by `memberOAuth2` (the document default; no override in its op) `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:1-3,9-16 — no security: override on this op]`, which per `app/auth/deps.py:get_current_member` requires an existing `Member` row reachable by JWT subject; (b) `Member.membership_status = PENDING_KYC` is, by the existing `_promote` code, only ever a **transient, uncommitted** intermediate value — the same function that creates a Member at `PENDING_KYC` immediately reassigns it to `PENDING_PAYMENT` before commit, with the comment "the transient state never persists" `[VERIFIED: backend/app/services/kyc.py:246-270]`; (c) a Member is never created at all before KYC approval (DEC-4). So there is no code path today that produces a genuine, authenticatable Member sitting durably at `PENDING_KYC`. The scenario is plausibly describing the *pre-auth applicant* (bootstrap `resume_token`, not a memberOAuth2 JWT) attempting the same endpoint — but that would fail authentication (401, wrong credential type) before reaching a status check, not "authenticated... `403`." This is a genuine premise ambiguity for whoever builds this guard; I did not find a resolution for it in `03`, `04`, or the contract.

**G-5 — `03`'s illegal-transition error code (`409`) doesn't match the contract's declared code for the same rule.**
US-2.2 Scenario 3 says an illegal transition attempt is rejected "with `409 Conflict`" `[VERIFIED: idea-lab/final_requirements/03_acceptance_criteria.md:245]`. The contract's `createMemberStatusTransition` operation — the concrete API surface for admin-driven transitions — declares `422 ILLEGAL_TRANSITION` for exactly this case, and a *separate* `409 PENDING_TRANSITION_EXISTS` for a different condition (a pending transition already exists) `[VERIFIED: backend/openapi/paths/ep2-shares.yaml:304-315]`. These are not the same thing: `03` says illegal-transition is `409`; the contract says it's `422`. Whoever builds the guard must pick one; I recommend following the contract (`422 ILLEGAL_TRANSITION`), since it's the more specific, machine-checked artifact, but this is a judgment call for the builder/PO, not something I can resolve here.

**G-6 — `ShareStatus.MEMBER = "ISSUED"` is a Python-name/wire-value mismatch that risks a silent serialization bug — [UNVERIFIED, flagged not confirmed by execution].**
`backend/app/models/membership.py:40-42` defines `ShareStatus` with member name `MEMBER` mapped to string value `"ISSUED"` (the other member, `REDEEMED`, has matching name/value). Every other enum I read in this codebase (`MembershipStatus`, `ShareClass`, `KycStatus`) has name == value for every member. SQLAlchemy's `Enum(PyEnumClass, name=...)` column type, by default, persists and validates against the Python enum **member's `.name`**, not `.value`, unless the column is constructed with `values_callable=...` — I grepped the whole `backend/app` tree for `values_callable` and found zero occurrences `[VERIFIED: grep -rn values_callable backend/app — no hits]`. If that default SQLAlchemy behavior applies here (I did not execute any code to confirm this, per this task's "no code executed" boundary — this claim about runtime behavior is **[UNVERIFIED]**, only the source-level facts above are verified), a Postgres `share_status` column could end up storing/round-tripping the literal string `"MEMBER"` rather than the contract's `"ISSUED"`, breaking the OpenAPI `ShareStatus` enum silently. This is worth a two-minute check (or a `values_callable=lambda e: [m.value for m in e]` fix) whenever `MembershipShare` is first exercised, ledger-gated or not.

**No other contract↔model↔AC↔`06` inconsistencies found.** I checked specifically for: (a) AC error codes absent from the contract — none found beyond G-5; (b) fields present in `04`'s entity tables but absent from the ORM beyond G-1/G-2; (c) `06` posting-rule accounts absent from `ledger.py`'s `AccountType` — confirmed absent as expected (do-not-implement), not treated as a new finding beyond G-2's schema-amendment framing; (d) DEC-11 par-value consistency across `01`/`04`/contract/`06` — all four consistently say 10,000₮ = 1,000,000 minor units, provisional pending legal `[VERIFIED: idea-lab/final_requirements/01_business_analysis.md:367; 04:776,1084; backend/openapi/schemas/ep2-shares.yaml:106-108; 06:98]`, no drift found.

---

## 6. Build sequence (once U1 lands)

1. **Schema amendments first.** Apply `06` §8.1/§8.2/§8.3 to `ledger.py` (chart-of-accounts fields on `Account`, `posting_class` on `LedgerEntry`, the ten new `Transaction` types) and G-1's two FKs to `membership.py`'s `MembershipShare` — in the same migration, so `check_migration` sees one consistent diff.
2. **The ledger posting service** (not EP-2-specific, but EP-2 is its first real consumer): a service that takes a `Transaction` + its `LedgerEntry` legs and posts them atomically, enforcing L-1 (sum-to-zero) and the corrected `available_balance = balance + signed_sum(MEMO_HOLD)` formula from the audit correction `[VERIFIED: idea-lab/final_requirements/06_ledger_addendum.md:151-165]`.
3. **`app/config.py:get_share_par_value()`** — the US-12.5 config seed for DEC-11's 10,000₮, mirroring `get_common_bond_rules()`.
4. **`app/adapters/payments/{port,mock}.py`** — the payment-initiation port, buildable independently of steps 1–2 (can be done first, in parallel).
5. **`app/repositories/shares.py` (`MembershipShareRepository`)** and the DEC-4 transition-guard service — also independent of steps 1–2, buildable first.
6. **`app/services/shares.py`** wiring the port + repository + par-value config + transition guard for the ratification-independent half of `purchaseMembershipShare` (validation, idempotency-key handling, `PENDING_PAYMENT` precondition) — the response only returns `SETTLED`/`ACTIVE` once step 2 exists; until then it can legitimately return `PENDING`.
7. **Wire the `SHARE_SUBSCRIPTION` posting + activation** into the same service once step 2 lands — this is the step that actually needs U1's sign-off to write.
8. **`getShareRegistry`'s `equity_ledger_reconciliation` and the L-4 nightly check** — last, since both need `balance(3000)` to be a real, correctly-derived number.
9. **`getClosurePreconditions`/`createClosureRequest`** — depends on EP-6 (lending, itself deferred per `CLAUDE.md`) and the `MEMO_HOLD` posting class from step 1/2, so naturally sequences after all of the above.

Steps 3–6 can start **today**, in parallel with U1 review, so that step 7 is a small, reviewable diff once ratification lands — the point of this document.
