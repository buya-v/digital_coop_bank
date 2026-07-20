# Ledger Design Addendum — Digital Coop Bank

**Document ID:** 06_ledger_addendum
**Version:** Draft 2 (incorporates adversarial accounting review; see §11 changelog)
**Status:** Draft for review (engineering + finance + counsel). Blocks S1 implementation.
**Upstream sources of truth:** `01_business_analysis.md` §5 (KPIs) and §6 (DEC-1…DEC-20), `04_technical_architecture.md` §2.3 (E-6 Account, E-7 LedgerEntry, E-8 Transaction), `05_prd_and_roadmap.md` §3 (DEC-21…DEC-75).

**Authority note.** This document is normative for the chart of accounts, posting rules, precision and rounding conventions, interest accrual, and the Patronage Dividend calculation. Where it conflicts with `04` §2.3 on **ledger mechanics**, this document prevails and `04` is to be amended per §8.

It has **no authority over `01` §6 (DEC-1…DEC-20) or the `01` §5 KPIs**, which `05` §6.3 makes normative ("no other document may redefine a term or value"). Where the ledger design touches a ratified value — the surplus split, share non-withdrawability, dividend eligibility — this document states the constraint it must satisfy and raises an open item in §9 rather than deciding. It changes no member-facing behaviour except where §6.5 resolves a previously unspecified rounding outcome and where §9/LA-13 is adjudicated.

**Why this document exists.** `04` mandates a double-entry ledger, declares it the source of truth for every balance, and routes 26 transaction types through it — while collapsing every internal account into a single `SYSTEM` enum value and providing exactly one worked debit/credit pair. No engineer can write the first ledger migration from that. All thirteen services post here, so this gap blocks roughly 70% of the backlog.

---

## 1. Accounting model and conventions

### 1.1 Entity posture

The cooperative operates over a sponsor-bank/BaaS FBO structure (`04` §4.3). The platform ledger is the **book of record for member positions**; the sponsor bank's FBO statement is an external control reconciled daily. Member deposits are **liabilities of the cooperative**; FBO cash is an **asset**.

This posture is independent of the charter outcome (`05` OI-3). If the charter route changes, only the regulatory reporting mapping in US-13.2 changes — not the chart of accounts.

### 1.2 Sign convention

| Category | Default normal balance | Debit effect | Credit effect |
| :--- | :--- | :--- | :--- |
| ASSET | DEBIT | increase | decrease |
| EXPENSE | DEBIT | increase | decrease |
| LIABILITY | CREDIT | decrease | increase |
| EQUITY | CREDIT | decrease | increase |
| INCOME | CREDIT | decrease | increase |

**Signed balance** is computed in the account's own normal direction:

```
debit-normal:   balance = Σ(DEBIT amounts) − Σ(CREDIT amounts)
credit-normal:  balance = Σ(CREDIT amounts) − Σ(DEBIT amounts)
```

**Contra accounts** carry a `normal_balance` *opposite* to their category default (1190 Allowance for Loan Losses is an ASSET with a CREDIT normal balance). The pairing is explicit per account and must **not** be derived from category — any validator inferring normal balance from category will wrongly flag contra accounts.

**Clearing accounts are bidirectional.** 1010–1050 routinely carry credit balances between the two settlement stages (a payable to the network or ACH operator). They are exempt from normal-balance assertions; only their *aged* balance is monitored (§7.3).

A member's savings account is credit-normal, so a positive member-facing balance is a credit balance. **The API contract is unchanged** — `04` §3.3 continues to return `balance` as a positive integer for a funded account. The sign convention is internal.

**Invariant L-1.** For every Transaction, `Σ(DEBIT amounts) = Σ(CREDIT amounts)` exactly, in minor units. Enforced as a deferred database constraint, not by application code alone.

### 1.3 Subsidiary and control accounts

E-6 `Account` rows are **subsidiary** accounts; each rolls up to a GL control account via a new `gl_control_code` attribute (§8.1). The trial balance is computed over control accounts; member-level balances over subsidiaries.

Critically, **every subsidiary must be an E-6 row**, because only E-6 rows carry LedgerEntries. Loans, pooled circles, and project escrows are therefore each given a backing `Account` (§8.10) — without it, Invariant L-2 is uncomputable for three of the control accounts.

**Invariant L-2.** For each control account, `Σ(subsidiary balances) = control balance`. Verified nightly (§7.3).

---

## 2. Chart of accounts

`system_account_code` is a new required attribute on E-6 where `account_type = SYSTEM` (§8.1). Codes are configuration-seeded via US-12.5, never hard-coded in service logic.

### 2.1 Assets (1000–1999, debit-normal unless noted)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 1000 | FBO Cash at Sponsor Bank | Settled cash at the partner institution. The reconciliation anchor. |
| 1010 | Stripe Clearing | Share-subscription collections in flight (US-2.1). |
| 1020 | ACH Clearing | ACH originations and receipts in flight, including returns. |
| 1030 | Card Network Settlement Clearing | Card activity between authorization and network settlement. |
| 1040 | Wire Clearing | Outbound wires in flight. |
| 1050 | RTP / FedNow Clearing | Real-time rail activity in flight. |
| 1100 | Loans Receivable — Principal | Control; subsidiary = one Account per E-24 Loan (§8.10). |
| 1110 | Loan Interest Receivable | Accrued, unposted loan interest. Subsidiary per loan. |
| 1120 | Loan Fees Receivable | Assessed, uncollected loan fees. Required by the §4.6 waterfall. |
| 1190 | Allowance for Loan Losses | **Contra-asset, credit-normal.** |
| 1900 | Suspense / Unidentified Receipts | Unmatched inbound funds. Must be zero at period close (§7.4). |
| 1950 | Rounding Differences | The designated rounding account required by L-5. Monitored; a growing balance indicates a rounding defect. |

### 2.2 Liabilities (2000–2999, credit-normal)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 2000 | Member Deposits — Savings | Control for `PRIMARY_SAVINGS`. |
| 2010 | Member Deposits — Transaction | Control for `TRANSACTION`. |
| 2020 | Member Deposits — Group Pots | Control for `GROUP_POT`. |
| 2050 | Accrued Savings Interest Payable | **Period-end stub accrual only** (§6.2). Not a per-member ledger. |
| 2060 | Pooled Circle (ROSCA) Funds | Control; one subsidiary Account per E-27 (§8.10). |
| 2100 | Community Project Escrow | Backings held all-or-nothing per DEC-66; one subsidiary Account per E-43 (§8.10). |
| 2200 | Dividend Payable | Declared, unpaid Patronage Dividend entitlements. |
| 2300 | Community Grant Pool — Restricted | The 10% surplus appropriation (E-45, KPI-4.2). |

### 2.3 Equity (3000–3999, credit-normal)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 3000 | Member Share Capital | Control for `MEMBERSHIP_SHARE`, at DEC-11 par ($25.00). |
| 3100 | Retained Surplus | Accumulated surplus not otherwise appropriated. |
| 3150 | Statutory & General Reserves | The reserve tranche implied by KPI-4.1/4.2 ("60% dividends + 10% community + **remainder to reserves**"). Its absence in Draft 1 silently deleted the reserve allocation. |
| 3200 | Current Year Surplus | Current fiscal year result. Closed and appropriated at the AGM (§7.4). |

### 2.4 Income (4000–4999, credit-normal)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 4000 | Loan Interest Income | Accrued interest on the loan book. |
| 4010 | Loan Interest Reversed | **Contra-income, debit-normal.** Reversal of accrued interest on write-off (§4.9). |
| 4100 | Fee Income | Wire fees, loan fees, and other member fees (US-12.5 configured). |
| 4200 | Interchange Income | Card interchange received via the issuer processor. |
| 4900 | Recoveries | Post-charge-off recoveries. |

### 2.5 Expenses (5000–5999, debit-normal)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 5000 | Savings Interest Expense | Interest credited to member savings. |
| 5100 | Loan Charge-Off Expense | Write-offs exceeding the allowance. |
| 5200 | Provision for Loan Losses | Periodic provisioning to 1190. |
| 5400 | Payment Processing Fees | Stripe/processor fees withheld from remittance (§4.1). |

> **Note.** Draft 1 defined a `5300 Surplus Match Grant Expense` that no posting rule used. It is **deleted**: the Community Grant pool is an *appropriation of surplus* (equity → restricted liability), not an operating expense. See §4.7.

### 2.6 Memorandum accounts (9000–9999, excluded from the trial balance)

| Code | Account | Purpose |
| :--- | :--- | :--- |
| 9000 | Card Authorization Holds | Counter-account for card auth `MEMO_HOLD` pairs. |
| 9010 | Guarantee Pledge Holds | Counter-account for E-23 pledge holds. |
| 9020 | Group Pot Pending Holds | Counter-account for E-12 pending approvals. |

Memorandum accounts satisfy L-1 (holds post in balanced pairs) while being excluded from the financial trial balance in §7.3.

---

## 3. Holds: the memorandum posting class

`04` §5.1 requires that "holds (pledges, pot approvals, card auths) are ledger postings, **not mutable flags**." Read literally against a financial ledger this is wrong — a card authorization must not change a member's deposit liability, only their spendable amount.

**Resolution [NEW].** LedgerEntry gains `posting_class` (§8.2):

| `posting_class` | In `balance` | In `available_balance` | In `goal_balance` | Use |
| :--- | :--- | :--- | :--- | :--- |
| `FINANCIAL` | yes | yes | yes | All real money movement. |
| `MEMO_HOLD` | **no** | yes (as a reduction) | no | Card authorizations, guarantee pledges (E-23), Group Pot pending approvals (E-12). |
| `ATTRIBUTION` | no | no | yes | Savings Goal sub-allocation within one account (§4.2). |

Derived quantities:

```
balance           = signed_sum(FINANCIAL entries on the account)
available_balance = balance − signed_sum(MEMO_HOLD entries on the account)
goal_balance(G)   = signed_sum(FINANCIAL + ATTRIBUTION entries where savings_goal_id = G)
```

**Holds are released arithmetically, never by mutation.** A release posts an entry in the opposite direction; the hold's residual is the signed sum, not a status field. Draft 1's phrase "active MEMO_HOLD" implied a mutable status on an append-only entry — exactly the anti-pattern this section exists to avoid — and is withdrawn. This also makes partial pledge release (§4.6) representable, which a single `hold_ledger_entry_id` FK cannot express (§8.11).

**Invariant L-3 (withdrawn as an invariant).** Draft 1 asserted that a hold may never drive `available_balance` negative. That cannot hold: `04` §4.5 stand-in authorizations, ACH returns, and card force-posts all drive balances negative independently of holds. It is demoted to a **validation rule**: hold *placement* is rejected with `422 INSUFFICIENT_AVAILABLE_BALANCE` if it would breach zero. A negative `available_balance` is a legitimate observable state and requires a deposit-side collections path, which does not currently exist in the backlog — raised as LA-14.

`Σ(goal_balance) ≤ balance(Member SAV)` at all times.

---

## 4. Posting rules

Notation: `Dr` / `Cr`. "Member TXN" = the member's `TRANSACTION` account; "Member SAV" = `PRIMARY_SAVINGS`; "Member SHARE" = `MEMBERSHIP_SHARE`. Every rule is atomic within one Transaction and satisfies L-1.

### 4.1 Membership and equity

| Type | Stage | Dr | Cr |
| :--- | :--- | :--- | :--- |
| `SHARE_SUBSCRIPTION` | collection (US-2.1) | 1010 Stripe Clearing | Member SHARE |
| | processor remittance | 1000 FBO Cash **and** 5400 Processing Fees | 1010 Stripe Clearing |
| `SHARE_REDEMPTION` | closure at par (DEC-11) | Member SHARE | Member SAV |
| `SHARE_SUBSCRIPTION_REFUND` | aborted application (`04` §4.4) | Member SHARE | 1010 Stripe Clearing |

The remittance leg is split because Stripe remits **net of fees**; posting par against par would leave 1010 permanently uncleared.

**Aborted applications** have no savings account (accounts open only at `ACTIVE`, `04` E-6), so the refund returns to the original funding instrument via the clearing account — it cannot credit Member SAV. This is a distinct type from `SHARE_REDEMPTION` (§4.9).

**Invariant L-4.** `count(ISSUED shares) × par_value = balance(3000)`, checked by US-2.3.

### 4.2 Deposits and internal movement

| Type | Dr | Cr |
| :--- | :--- | :--- |
| `P2P_INTERNAL` | Sender TXN | Recipient TXN |
| `SAVINGS_TRANSFER` | Member TXN | Member SAV *(optionally goal-attributed)* |
| `GOAL_TRANSFER` | Member SAV *(goal A)* | Member SAV *(goal B)* — `posting_class = ATTRIBUTION`, net zero on the account |
| `GROUP_POT_CONTRIBUTION` | Member TXN | Group Pot account |
| `GROUP_POT_OUTBOUND` | approval pending | Group Pot account → 9020 — `MEMO_HOLD` |
| | on m-of-n approval | Group Pot account | Destination account or rail clearing *(hold released)* |
| `ROUND_UP_TRANSFER` → Savings Goal | Member TXN | Member SAV *(goal-attributed)* |
| `ROUND_UP_TRANSFER` → Community Project | Member TXN | 2100 Escrow *(project subsidiary)* |

`SAVINGS_TRANSFER` is new (§4.9). Draft 1 defined only *intra*-savings `GOAL_TRANSFER`, leaving the single most common member flow — funding a Savings Goal from the Transaction Account, which `04` E-9 `auto_transfer` schedules and `04` §3.3 exposes as `POST /savings-goals/{id}/transfers` — with no posting rule at all.

### 4.3 External rails

Every rail follows the same three-stage shape: **hold → origination → settlement**. Draft 1 omitted the hold on outbound and the settlement leg on wire and RTP, which left 1040 and 1050 permanently unclearable.

| Type | Stage | Dr | Cr |
| :--- | :--- | :--- | :--- |
| `EXTERNAL_ACH_OUT` | request accepted (`04` §4.3) | Member TXN → 9000-class hold | `MEMO_HOLD` |
| | origination | Member TXN | 1020 ACH Clearing *(hold released)* |
| | settlement | 1020 ACH Clearing | 1000 FBO Cash |
| `EXTERNAL_ACH_IN` | receipt | 1020 ACH Clearing | Member TXN |
| | settlement | 1000 FBO Cash | 1020 ACH Clearing |
| `WIRE_OUT` | origination | Member TXN | 1040 Wire Clearing |
| | settlement | 1040 Wire Clearing | 1000 FBO Cash |
| | fee (if configured) | Member TXN | 4100 Fee Income |
| `RTP_IN` | receipt | 1050 RTP Clearing | Member TXN |
| | settlement | 1000 FBO Cash | 1050 RTP Clearing |
| `RTP_OUT` | origination | Member TXN | 1050 RTP Clearing |
| | settlement | 1050 RTP Clearing | 1000 FBO Cash |

**Returns.** `Transaction.status = RETURNED` requires a **reversing Transaction**, never an update. The reversal posts the exact inverse and carries `reversal_of_transaction_id` (§8.3). ACH return codes populate `failure_reason`.

### 4.4 Cards

| Type | Stage | Dr | Cr |
| :--- | :--- | :--- | :--- |
| `CARD_PURCHASE` | authorization | Member TXN | 9000 Card Authorization Holds — `MEMO_HOLD` |
| | settlement | Member TXN | 1030 Card Settlement Clearing *(hold released)* |
| | network settlement | 1030 Card Settlement Clearing | 1000 FBO Cash |
| `CARD_REFUND` | | 1030 Card Settlement Clearing | Member TXN |
| `CARD_ATM_WITHDRAWAL` | settlement | Member TXN | 1030 Card Settlement Clearing |

Interchange is **not** posted here — it is a platform-level Transaction (`INTERCHANGE_SETTLEMENT`, §4.9), not a member transaction. Draft 1 posted it in both places, which would have double-counted income.

`CARD_ATM_WITHDRAWAL` is new: `04` E-18 `controls.channel_toggles` includes `atm`, but cash withdrawal had no posting rule.

### 4.5 Savings interest

**Daily accrual is not a ledger posting.** It accumulates in `InterestAccrualAccumulator` (§8.6) at micro-cent precision. Draft 1 posted daily to the ledger, which — against §5.1's integer-cent storage rule — truncated daily and cost a member with a $500 balance roughly 3–5% of annual interest, contradicting §5.4's own promise.

| Stage | Dr | Cr |
| :--- | :--- | :--- |
| Monthly posting | 5000 Savings Interest Expense | Member SAV |
| Period-end stub (only if the accounting period ends between postings) | 5000 Savings Interest Expense | 2050 Accrued Interest Payable |
| Stub reversal (first day of next period) | 2050 Accrued Interest Payable | 5000 Savings Interest Expense |

2050 therefore needs no per-member subsidiary — it holds a single period-end accrual figure for financial reporting only.

### 4.6 Lending

| Type | Dr | Cr |
| :--- | :--- | :--- |
| `LOAN_DISBURSEMENT` | 1100 Loans Receivable *(loan subsidiary)* | Member TXN |
| Daily loan accrual | 1110 Loan Interest Receivable | 4000 Loan Interest Income |
| Loan fee assessed | 1120 Loan Fees Receivable | 4100 Fee Income |
| `LOAN_REPAYMENT` | Member TXN | 1120 *(fees)*, 1110 *(accrued interest)*, 1100 *(principal)* |
| `GUARANTEE_PLEDGE` | Guarantor SAV → 9010 | `MEMO_HOLD` |
| `GUARANTEE_RELEASE` (pro-rata, US-6.4) | 9010 → Guarantor SAV | `MEMO_HOLD` reversal |
| `GUARANTEE_APPLICATION` | Guarantor SAV | 1100 Loans Receivable |
| `POOLED_CIRCLE_CONTRIBUTION` | Member TXN | 2060 *(circle subsidiary)* |
| `POOLED_CIRCLE_PAYOUT` | 2060 *(circle subsidiary)* | Recipient TXN |

**Repayment waterfall:** fees → accrued interest → principal, oldest installment first. The interest leg credits the **accrued** balance in 1110, *not* the scheduled interest figure — crediting the schedule causes 1110 to drift every month and hold a residue at payoff. Overpayment reduces principal and triggers schedule recomputation (US-6.7).

**Guarantee application is restricted to `pledge_source = SAVINGS`.** Draft 1 permitted debiting Member SHARE, which (a) retires share capital from an ACTIVE member against DEC-11's non-withdrawability, (b) breaks L-4 whenever the amount is not a multiple of $25.00, since E-5 has no partial-redemption model, and (c) violates §4.8's own prohibition on touching 3000. `04` E-23 does allow `pledge_source = SHARE_CAPITAL`, but explicitly behind `jurisdiction_flag` (`05` OI-2) — it was left open, not ratified. **Raised as LA-9; until adjudicated, share-capital pledges are not implementable.**

`GUARANTEE_PLEDGE` / `GUARANTEE_RELEASE` are new types — Draft 1 posted only *application*, leaving DEC-51's pre-disbursement revocability and US-6.4's pro-rata release unrepresentable.

**ROSCA missed contributions (DEC-54)** — the three ratified backstops post as: (a) pro-rata absorption → `Dr` each participant TXN / `Cr` 2060; (b) reduced payout → no posting, the payout leg is smaller; (c) forfeiture → participant's contributions remain in 2060 and redistribute at circle close.

### 4.7 Surplus appropriation, dividends, and community funding

Sequence matters here, and Draft 1 had it wrong (see §7.4).

| Stage | Dr | Cr |
| :--- | :--- | :--- |
| Fiscal year close | 4xxx Income accounts | 3200 Current Year Surplus |
| | 3200 Current Year Surplus | 5xxx Expense accounts |
| **AGM appropriation** (DEC-10, US-12.6) | 3200 Current Year Surplus | 2200 Dividend Payable *(pool)*, 2300 Community Grant Pool *(10%)*, 3150 Reserves *(remainder)* |
| `DIVIDEND_PAYOUT` → `SAVINGS` | 2200 Dividend Payable | Member SAV |
| `DIVIDEND_PAYOUT` → `SHARE_REINVESTMENT` | 2200 Dividend Payable | Member SHARE *(whole shares)* **and** Member SAV *(residual, §6.5)* |
| `PROJECT_BACKING` | Member SAV | 2100 Escrow *(project)* |
| `BACKING_REFUND` (DEC-66) | 2100 Escrow *(project)* | Member SAV |
| `BACKING_DISBURSEMENT` | 2100 Escrow *(project)* | 1020 ACH Clearing → settlement `Dr 1020 / Cr 1000` |
| `SURPLUS_MATCH_DISBURSEMENT` | 2300 Community Grant Pool | 1020 ACH Clearing → settlement `Dr 1020 / Cr 1000` |

The appropriation entry zeroes 3200 and is the **only** debit to it. The Community Grant pool is an appropriation of equity to a restricted liability — **not an expense** — which is why the `5300` account of Draft 1 is deleted.

**Surplus Match accrual** (E-46 `ACCRUING`, E-45 `committed`) is a **commitment, not a posting**: it reserves pool capacity without moving money. Only `SURPLUS_MATCH_DISBURSEMENT` posts. E-45's `committed` is maintained as a derived field over `ACCRUING` matches.

### 4.8 Fees and adjustments

| Type | Dr | Cr |
| :--- | :--- | :--- |
| `FEE` (deposit-side) | Member account | 4100 Fee Income |
| `ADJUSTMENT` | per reason code | per reason code |

**`ADJUSTMENT` is the highest-risk type in the system** — the only one without a fixed pair. It requires a closed reason-code list seeded in US-12.5, maker-checker dual approval (E-53), a mandatory narrative, and a counter-account restricted to **1900 Suspense, a 5xxx expense account, or the original income account of the transaction being corrected**. (Draft 1 forbade the income account, which made a fee waiver — the most common legitimate adjustment — impossible to book without permanently overstating fee income.) It may **never** touch 3000 Member Share Capital.

### 4.9 Transaction types that must be added to E-8

Draft 1 identified five; review found six more. None adds member-facing scope.

| Proposed type | Why required |
| :--- | :--- |
| `SAVINGS_TRANSFER` | Funding a Savings Goal from the Transaction Account — the most common member flow — had no rule (§4.2). |
| `BACKING_DISBURSEMENT` | DEC-66 escrow has a refund path; the success path exists in the data model (E-43 `amount_disbursed`, `FUNDED`, `COMPLETED`) but has **no transaction type**, so a funded project cannot be paid. |
| `SHARE_SUBSCRIPTION_REFUND` | `04` §4.4 requires refund on aborted applications; `SHARE_REDEMPTION` credits a savings account the applicant does not have. |
| `GUARANTEE_PLEDGE` / `GUARANTEE_RELEASE` | DEC-51 revocability and US-6.4 pro-rata release. |
| `CARD_ATM_WITHDRAWAL` | `04` E-18 enables the `atm` channel with no posting rule. |
| `LOAN_WRITE_OFF` | `Dr 1190` *(and 5100 for any excess)* `/ Cr 1100`, **and** `Dr 4010 Interest Reversed / Cr 1110`. Draft 1 wrote off principal only, leaving uncollectible interest in 1110 and phantom income in 4000. |
| `LOAN_PROVISION` | `Dr 5200 / Cr 1190`. Required for KPI-2.5 NPL reporting. |
| `RECOVERY` | Post-charge-off collection. Routes through `Member TXN` or `1020 ACH Clearing` like any other inbound receipt — **not** directly to 1000 as Draft 1 had it. |
| `INTERCHANGE_SETTLEMENT` | `Dr 1030 / Cr 4200`, posted once, at platform level (§4.4). |
| `ACCOUNT_CLOSURE_DISBURSEMENT` | Residual balance disposition on account or Group Pot closure. |

**Non-accrual policy [NEW].** Daily interest accrual **stops** when a loan reaches `DEFAULTED` (90 DPD, DEC-52). Interest accrued while `DELINQUENT` is reversed on transition to `DEFAULTED` via 4010. Without this, a written-off loan accrues income forever.

### 4.10 Flows still without posting rules

Stated plainly rather than claimed complete:

1. **Group Pot / account closure residual disposition** — type proposed above; the *policy* (where residuals go, how disputes are handled) is undecided.
2. **Deposit-account negative-balance collections** — see L-3 above; LA-14.
3. **Card disputes / provisional credit** — `04` handles disputes "via case notes at launch"; provisional credit under Reg E is a real posting path with statutory clocks and does not exist in the backlog. Out of scope here, flagged as LA-15.

---

## 5. Precision, rounding, and day-count conventions

`03` EP-3 asserts that rounding "follows a single documented rule" and `03` EP-7 that the dividend "rounding-remainder allocation rule [is] documented and applied deterministically." Neither rule was ever stated. Both are stated here.

### 5.1 Storage precision

All persisted monetary amounts are **signed 64-bit integers in USD minor units (cents)**, per DEC-18. No floating-point type may appear in any monetary code path, schema column, API field, or test fixture — including intermediate calculation.

### 5.2 Computation precision

Interest accrual and rate tiering compute in **scaled integer micro-cents — minor units × 10⁶**. This is the "high precision" `03` EP-3 refers to without defining. Accumulators (§8.6) persist micro-cents in a dedicated column, which is the one documented exception to §5.1's cents rule.

**Dividend apportionment is different** and uses the exact integer method in §6.4 at `SCALE = 10¹²`, with an **int128 (or arbitrary-precision) intermediate**. `pool_¢ × 10¹² × w_bps × F_k` overflows int64 at realistic magnitudes; the widening is mandatory, not an optimization.

### 5.3 Rounding rule [NEW]

**Round half-even (banker's rounding) to the nearest minor unit, once, at the point of posting.** Intermediate results are never rounded.

Half-even is chosen because accrual and apportionment run across a large population, and half-up introduces a systematic upward bias that accumulates into a reconciliation break.

Two deliberate exceptions, and no others without amending this section:
- **Monthly savings-interest posting floors** (§6.2), so the cooperative never credits unearned interest.
- **Fees floor:** `fee = ⌊exact_fee⌋`, with no subsequent rounding step. (Draft 1 said fees "floor before the rounding step," which is a no-op — flooring already yields an integer.)

### 5.4 Residual carry

**Invariant L-5.** No monetary computation may discard value. Every rounding step either posts the residue, carries it in a named accumulator, or posts it to **1950 Rounding Differences**.

- **Savings interest:** the accumulator (§6.2) retains micro-cent precision; only the monthly posting rounds, and the residue carries forward.
- **Dividend:** largest-remainder allocation (§6.4) distributes every residual cent, so the pool is exhausted exactly.

### 5.5 Day-count convention [NEW]

**Actual/365 Fixed (ACT/365F)** for all interest, savings and lending alike. Leap years divide by 365, not 366 — the 366th day accrues normally. This ratifies the convention already implied arithmetically by `03` EP-3 ("$1,000.00 × 2.00%/365").

---

## 6. Interest and dividend calculation

### 6.1 Savings interest — accrual

Accrual is on the **end-of-day `FINANCIAL` balance** of the `PRIMARY_SAVINGS` account — not the average daily balance and not the available balance. Holds do not reduce accrual.

```
daily_accrual_μ¢ = round_half_even( eod_balance_¢ × 10⁶ × annual_rate_bps / 10 000 / 365 )
```

The job runs once per calendar day, idempotent and checkpointed, keyed on `(account_id, accrual_date)` so a re-run cannot double-count. It writes only to the accumulator, never to the ledger (§4.5).

### 6.2 Savings interest — posting

On the last calendar day of each month:

```
posted_¢    = ⌊ accumulated_μ¢ / 10⁶ ⌋         // floor, NOT half-even
accumulator = accumulated_μ¢ − posted_¢ × 10⁶   // always ≥ 0, carries forward
```

Rounding half-even here can round *up*, crediting interest that has not accrued and driving the accumulator negative — the cooperative would pay unearned interest and carry a receivable against the member. Flooring guarantees a non-negative accumulator; the residue is not lost, it posts in a later month.

Worked check at $1,000.00 and 2.00% APR: the twelve monthly postings total $19.99, with $0.0099 remaining in the accumulator and posting in January. Value is conserved (L-5); only timing shifts by one period.

Rate changes take effect from the ConfigurationParameter effective date (US-12.5); each day accrues at the rate in force that day. Reg DD/TISA disclosure obligations attach here — LA-7.

### 6.3 Loan interest and amortization

**Accrual and schedule must use the same basis.** Draft 1 mandated ACT/365F simple-interest accrual while generating the schedule from a monthly-compounded annuity — two different interest totals, guaranteeing that 1110 drifts every month and never zeroes at payoff, and falsifying L-6's APR-reconciliation clause.

Both now use **ACT/365F simple interest on outstanding principal, no compounding**:

```
interest_k = ⌊ outstanding × apr_bps × days_in_period_k / (10 000 × 365) ⌋
```

where `days_in_period_k` is the actual day count between installment due dates.

**Level payment** is solved, not computed in closed form: the smallest integer payment `p` such that applying the recurrence above for `n` installments drives outstanding to zero or below. Binary search over `[1, principal + total_interest_ceiling]` converges in ~30 iterations and is fully deterministic.

The **final installment absorbs the residue**: `final = outstanding + interest_n`. It differs from the level payment by at most a few cents.

This formulation has three properties the annuity lacked: it is consistent with daily accrual, it needs **no zero-interest special case** (Draft 1's `principal × i / (1 − (1+i)^(−n))` divided by zero at `i = 0`, reachable via a `HARDSHIP_RESCHEDULE` under E-25 since DEC-49's 4% floor is a config seed, not a code guarantee), and it handles `n = 1`.

`SEASONAL` and `INCOME_LINKED` schedules apply `seasonal_profile` weighting to the **principal** component while interest continues to accrue on actual outstanding balance. **The generation algorithm is not derivable from current requirements — LA-2.**

**Invariant L-6.** For any loan, `Σ(installment principal) = principal_amount` exactly, and the schedule reconciles to the disclosed APR (`03` EP-6: "no hidden cost versus the disclosed APR"). Checked nightly (§7.3).

### 6.4 Patronage Dividend formula [NEW]

No formula exists anywhere in the current baseline. This is reconstructed from DEC-10 (the four factors), E-31, E-32, and KPI-4.1/4.2.

**Step 1 — Surplus appropriation.** The `01` §5 KPI note is explicit: *"60% dividends + 10% community + remainder to reserves."*

```
community_grant_allocation = round_half_even( ratified_surplus × 1000 / 10 000 )       // 10%, KPI-4.2
distributable_pool         = round_half_even( ratified_surplus × dividend_share_bps / 10 000 )
retained_to_reserves       = ratified_surplus − distributable_pool − community_grant_allocation
```

`dividend_share_bps` is a US-12.5 config seed of **6000** (60%), governed by `FINANCIAL_POLICY` ballot per DEC-10, constrained to `6000 ≤ dividend_share_bps ≤ 9000` so KPI-4.1's floor holds and the reserve tranche cannot be zeroed without a governance decision.

Draft 1 set `distributable_pool = surplus − 10%`, distributing 90% to members and silently deleting the reserve tranche. **The exact split above is a Board/Finance decision, not an engineering one — LA-8.** The formula is correct for any ratified split.

**Step 2 — Eligibility.** Members `ACTIVE` holding an `ISSUED MEMBERSHIP` share at the declaration date. Per DEC-56, a zero-patronage eligible member receives a **$0.00 entitlement statement, not an error**.

This excludes a member who was ACTIVE all fiscal year but closed before the AGM, and excludes `SUSPENDED` members. Neither exclusion is derivable from DEC-4, DEC-10 or DEC-56 — it is a member-facing policy decision and is **not settled here. LA-13.**

**Step 3 — Factor sums.**

```
for each factor k ∈ {avg_savings_balance, transaction_volume,
                     loan_repayment_performance, governance_participation}:

    F_k(m) = the member's fiscal-year aggregate of monthly E-31 values for factor k
    S_k    = Σ_over_eligible_members F_k(m)
```

Member *m*'s share of factor *k* is conceptually `F_k(m) / S_k`, but is **never computed as an isolated division** — Step 4 folds it into an exact integer expression.

If `S_k = 0` for a factor (no loans in year one), that factor is dropped and its weight redistributed pro-rata across survivors, so a dormant factor cannot void the run.

**Aggregation differs by factor type.** `avg_savings_balance` and `transaction_volume` are *volume* measures and aggregate by **sum**. `loan_repayment_performance_score` and `governance_participation_score` are `Decimal(5,4)` *rate* measures — summing them penalizes a member with perfect repayment over three months at one quarter the rate of an equally perfect twelve-month member. Rate factors therefore aggregate as a **membership-month-weighted average**. Draft 1 summed all four, a category error.

**E-31 absent-value semantics are undefined in `04` and move real money** — a member with no loan may plausibly record `0`, `1.0`, or no row. Recommended: members with no loan are **excluded from that factor's denominator** rather than scored zero. **LA-11.**

**Degenerate case.** If *every* `S_k = 0`, no patronage basis exists and Step 6 would silently under-allocate. The run **aborts**: the declaration moves to `status = CANCELLED` with reason `NO_PATRONAGE_BASIS` and no allocations are written. This is distinct from DEC-56's individual zero-patronage member, who is eligible and receives $0.00.

**Step 4 — Weighted score, as an exact integer.** `W` is the summed weight of surviving factors.

```
SCALE = 10¹²
N(m)  = Σ_k  ⌊ weight_k_bps × SCALE × F_k(m) / ( W × S_k ) ⌋      // int128 intermediate
T     = Σ_m N(m)                                                   // ascending member_id
```

**This must not be implemented in floating-point or fixed-precision decimal.** The natural formulation — a fractional share relying on `Σ P(m) = 1` — is wrong: that identity fails under finite-precision division, and with a single eligible member the resulting remainder exceeds the member count. Integer arithmetic makes apportionment exact by construction. Accumulation order is fixed (ascending `member_id`) so summation is reproducible.

If `T = 0`, abort per the degenerate case.

**Step 5 — Entitlement floor.**
```
floor(m) = ⌊ distributable_pool × N(m) / T ⌋
```

**Step 6 — Remainder allocation (largest remainder / Hamilton).**
```
allocated = Σ_m floor(m)
remainder = distributable_pool − allocated
```

**Precondition R-1:** `0 ≤ remainder < eligible_member_count`, guaranteed by Step 5 whenever `T > 0`. Assert it explicitly; violation means the run reached Step 5 degenerate and must abort without writing allocations.

Rank by `(distributable_pool × N(m)) mod T` descending, ties by `member_id` ascending — deterministic, no randomness, since runs must be exactly reproducible per `E-32.calculation_run_ref`. The top `remainder` members each receive one additional minor unit.

**Invariant L-7.** `Σ(entitlement) = distributable_pool` exactly. This is the reconciliation assertion `03` EP-7 already requires; §6.4 is what makes it mechanically true. Verified against 1–50,000 member populations.

**Legal flag.** DEC-10 includes **governance participation** as a patronage factor. Under US Subchapter T, patronage dividends must be allocated on business done with the cooperative; voting is not patronage, and a governance-weighted allocation may both fail Subchapter T and read as paying members to vote. The formula supports a weight of `0` without code change. **Counsel decision — LA-1.**

### 6.5 Share reinvestment and fractional shares [NEW]

DEC-11 fixes par at $25.00 and E-5 permits `share_class = REINVESTED_PATRONAGE`, but an entitlement is rarely a multiple of $25.00.

**Rule:** issue `⌊ entitlement / par_value ⌋` whole `REINVESTED_PATRONAGE` shares; credit the residual to `PRIMARY_SAVINGS`. For $84.60 at $25.00 par: **3 shares issued, $9.60 to savings.** No fractional shares are created, so L-4 holds and voting eligibility — binary per E-5 regardless of holdings — is unaffected.

This makes a **split payout the normal case** for every reinvesting member, which E-33 cannot currently record (singular `payout_transaction_id` / `reinvested_share_id`, no split status). See §8.12.

---

## 7. Balance integrity and operations

### 7.1 Single writer

Per `04` §1.1, the Ledger Service (S-3) is the only writer of financial postings. Other services *initiate* money movement through S-3's posting API. Cross-service atomicity uses the transactional outbox in `04` §1.2 — **the posting itself is never distributed.** A posting commits wholly within S-3's database transaction or does not occur.

### 7.2 Materialized balance maintenance

`E-6.balance` is materialized and never directly writable. It updates in the **same database transaction** as the LedgerEntry insert, under `SERIALIZABLE` isolation, with `E-7.sequence` assigned monotonically per account.

### 7.3 Nightly integrity checks

| Check | Assertion |
| :--- | :--- |
| Trial balance | `Σ debits = Σ credits` across all non-memorandum accounts |
| L-1 | every Transaction balances |
| L-2 | each control = Σ its subsidiaries |
| L-4 | `count(ISSUED shares) × par = balance(3000)` |
| L-5 | 1950 Rounding Differences within tolerance; growth investigated |
| L-6 | every active loan's schedule reconciles to principal and disclosed APR |
| L-7 | on declaration runs only |
| Drift | materialized `balance` = recomputed signed sum, per account |
| Clearing aging | no 10xx–105x item older than its rail's settlement window |

Draft 1 omitted L-5 and L-6 from the nightly set — including L-6, the one invariant §6.3 shows was false as constructed.

Any mismatch opens a `HIGH` ComplianceCase (matching `04` §4.3's reconciliation-break behaviour) and freezes the affected account pending investigation. To keep drift detection `O(entries since checkpoint)`, `AccountBalanceCheckpoint` (§8.5) stores a daily `(account_id, as_of_date, sequence, balance)`.

### 7.4 Accounting periods and year-end

`AccountingPeriod` (§8.4) carries `status ∈ {OPEN, CLOSING, CLOSED}`; entries carry `period_id`. Postings to a `CLOSED` period are rejected; late activity posts to the current open period with `value_date` retained.

Period close requires 1900 Suspense at zero, all three-way reconciliations clean, and the trial balance in balance.

**Fiscal year close** nets 4xxx income and 5xxx expense into **3200 Current Year Surplus** (§4.7). 3200 then holds the result that becomes `E-32.ratified_surplus`, and the AGM appropriation (§4.7) is the only entry that debits it — zeroing 3200 into 2200, 2300 and 3150.

Draft 1 had this backwards: it closed 3200 into 3100 *before* the declaration and then debited 3200 for the dividend, which — since DEC-10 places the AGM after year-end — would have debited the *new* year's surplus to pay the *prior* year's dividend, driving 3200 negative and misstating both years. It also defined no rule closing income and expense into 3200 at all, so 3200 was permanently zero and could not produce the surplus figure the entire dividend cycle depends on.

### 7.5 The card authorization read path

Card authorization has a 200 ms ceiling (`04` §5.2) and `04` §4.5 permits a cached balance view. Caching a balance that gates money movement needs a stated safety rule:

- The cache updates synchronously on commit of any entry affecting the account.
- Authorization reads tolerate at most **2 seconds** of staleness; beyond that they fall through to the authoritative row.
- The `MEMO_HOLD` placed at authorization is written authoritatively, never cache-only.
- On cache unavailability the read falls through to the database; if that breaches 200 ms, **the processor's stand-in rules govern**. Per `04` §4.5 stand-in *does* approve on an unknown balance by design ("conservative low-limit approval for card-present, decline for high-risk MCCs"), with all stand-in activity reconciled and flagged next cycle. The *platform* never approves on an unknown balance; the processor may, and the resulting exposure is an accepted, reconciled risk — not an error state. (Draft 1 asserted the opposite of its own source.)

---

## 8. Required schema amendments to `04` §2

| # | Entity | Change |
| :--- | :--- | :--- |
| 8.1 | **E-6 Account** | Add `account_category` Enum `ASSET \| LIABILITY \| EQUITY \| INCOME \| EXPENSE \| MEMO`; `normal_balance` Enum `DEBIT \| CREDIT` (explicit, never derived from category); `gl_control_code` String; `system_account_code` String nullable (required when `account_type = SYSTEM`). Extend `account_type` with `LOAN \| CIRCLE_POOL \| PROJECT_ESCROW \| MEMO`. Retire the parenthetical "SYSTEM covers cash clearing, interest expense, surplus, Community Grant pool, suspense" — those are now distinct accounts per §2. |
| 8.2 | **E-7 LedgerEntry** | Add `posting_class` Enum `FINANCIAL \| MEMO_HOLD \| ATTRIBUTION`; `value_date` Date (distinct from `posted_at`); `period_id` FK→AccountingPeriod; `reversal_of_entry_id?` FK→LedgerEntry. **Replace the self-referential `entry_type` definition** ("mirrors Transaction type + …") with an explicit enumeration — it currently defines ~30 values by reference to another enum and is not implementable as written. |
| 8.3 | **E-8 Transaction** | Add the ten types in §4.9. Add `reversal_of_transaction_id?` FK→Transaction. |
| 8.4 | **New: AccountingPeriod** | `id`, `fiscal_year`, `period_number`, `starts_on`, `ends_on`, `status`, `closed_at?`, `closed_by?`. |
| 8.5 | **New: AccountBalanceCheckpoint** | `account_id`, `as_of_date`, `sequence`, `balance`; UQ(account, as_of_date). |
| 8.6 | **New: InterestAccrualAccumulator** | `account_id` or `loan_id`, `accrual_date`, `accrued_μ¢` (int64, micro-cents), `posted_through_date`; UQ on the natural key for idempotency. |
| 8.7 | **E-20 LoanApplication** | Fix `referral_case_id? FK→ComplianceCase-style loan referral` — add `LOAN_REFERRAL` to `ComplianceCase.case_type` or drop the field. Currently unwritable. |
| 8.8 | **DEC-20 / E-20** | `04` introduces `DECLINED_CLOSED`, absent from DEC-20's canonical `LoanStatus`, despite `04`'s front matter promising glossary enums are used "exactly as defined." Amend DEC-20 or record the outcome solely in `decision.outcome`. |
| 8.9 | **E-17 PaymentRequest** | The `shares` child rows have no E-number, PK, or FK. Promote to a first-class entity. *(Draft 1 cited E-16; E-16 is ScheduledPayment.)* |
| 8.10 | **E-24 Loan, E-27 PooledLoanCircle, E-43 CommunityProject** | Add `ledger_account_id` / `pool_account_id` / `escrow_account_id` FK→Account. Without these, these entities cannot carry LedgerEntries and L-2 is uncomputable for controls 1100, 2060 and 2100. (E-45 already has `pool_account_id`.) |
| 8.11 | **E-23 PeerGuarantee** | Replace singular `hold_ledger_entry_id` with a 1—N relation. One FK cannot represent an initial hold plus N partial releases (US-6.4 pro-rata), making the remaining hold underivable and creating a double-count vector. |
| 8.12 | **E-33 DividendAllocation** | Support split payout: `payout_transaction_id` and `reinvested_share_id` must both be populatable on one allocation, and `status` needs a `SPLIT_PAID` value. §6.5 makes this the normal case for reinvesting members. |

---

## 9. Open items for adjudication

| ID | Item | Owner | Gate |
| :--- | :--- | :--- | :--- |
| LA-1 | **Governance participation as a patronage factor** (§6.4) — Subchapter T exposure. Formula supports weight 0 without code change. | Counsel + PO | Before S5 |
| LA-2 | **`SEASONAL` / `INCOME_LINKED` schedule generation** (§6.3) — not derivable from current requirements. | PO + Lending | Before S3 |
| LA-3 | **Rounding mode** — §5.3 proposes half-even with two stated exceptions. Confirm. | Finance | Before S1 |
| ~~LA-4~~ | *Closed in Draft 2.* Draft 1 asked Finance to confirm that fees "floor before rounding" — a no-op, since flooring already yields an integer. Restated in §5.3 as `fee = ⌊exact_fee⌋` with no subsequent rounding. Number retired, not reused. | — | — |
| LA-5 | **Ten missing transaction types** (§4.9) — particularly `SAVINGS_TRANSFER` (S2) and `BACKING_DISBURSEMENT` (S6). | PO | Per epic |
| LA-6 | **Allowance/provisioning methodology** — accounts and postings exist; the *model* (incurred loss, CECL-style, aging matrix) is undecided and affects KPI-2.5. | Finance + Counsel | Before S4 |
| LA-7 | **Reg DD / TISA disclosure obligations** attach to §6.1–6.2 and are absent from the baseline. | Counsel | Before launch |
| LA-8 | **Surplus split** (§6.4 Step 1) — dividends vs community vs reserves. KPI-4.1/4.2 imply 60/10/30; needs Board ratification and a `dividend_share_bps` seed. | Board + Finance | Before S5 |
| LA-9 | **Share-capital guarantee pledges** (§4.6) — currently conflicts with DEC-11 and L-4; restricted to SAVINGS until resolved. | Counsel + Lending | Before S4 |
| LA-10 | **Non-accrual policy** (§4.9) — proposed: stop at `DEFAULTED`, reverse `DELINQUENT` accruals. Confirm. | Finance | Before S3 |
| LA-11 | **E-31 absent-factor semantics** and rate-vs-volume aggregation (§6.4 Step 3). | PO + Finance | Before S5 |
| LA-12 | **ROSCA backstop postings** (§4.6) — DEC-54's three options are ratified; the ledger treatment of forfeiture at circle close needs confirmation. | PO | Before S4 |
| LA-13 | **Dividend eligibility** (§6.4 Step 2) — members closing between fiscal year end and AGM; `SUSPENDED` members. Member-facing policy. | Counsel + PO | Before S5 |
| LA-14 | **Deposit negative-balance collections** (§3) — no path exists for a member account driven negative by stand-in, returns, or force-posts. | PO + Ops | Before S2 |
| LA-15 | **Reg E provisional credit postings** (§4.10) — disputes are "case notes at launch"; the statutory path has real ledger effects. | Counsel + PO | Before card launch |

---

## 10. What this unblocks

With §2, §4, §5 and §6 ratified, the S1 ledger migration and the Account & Ledger Service (S-3) become implementable, and with them the downstream money paths: savings, payments, cards, lending, round-ups, community funding, and dividends.

Items that still block specific epics: LA-2 (full US-6.7 servicing scope), LA-8 and LA-13 (the US-7.1 dividend engine, on Board and policy dependencies), LA-9 (share-capital pledges in Loan Circles), and LA-14 (a deposit-side gap that should be closed before cards ship). `BACKING_DISBURSEMENT` is a one-line enum addition, not an EP-9 blocker — Draft 1 overstated it.

---

## 11. Changelog — Draft 1 → Draft 2

Draft 2 incorporates an adversarial accounting review. Substantive corrections, in order of money at risk:

1. **Surplus split** — Draft 1 allocated 90% of surplus to members and omitted reserves entirely, contradicting KPI-4.1/4.2. Added account 3150 and a governed `dividend_share_bps` (§6.4 Step 1, LA-8).
2. **Year-end sequencing** — Draft 1 closed 3200 before the declaration and then debited it, and defined no rule closing income/expense into it. Rewritten (§4.7, §7.4).
3. **Loan interest basis** — Draft 1 accrued ACT/365F simple but scheduled a monthly-compounded annuity; 1110 would drift every month. Both now ACT/365F; level payment solved rather than closed-form, which also removes the zero-interest division-by-zero (§6.3).
4. **Daily accrual** — Draft 1 posted daily to a cents-only ledger, truncating ~3–5% of member interest. Accrual now accumulates at micro-cents and posts monthly (§4.5, §6.1).
5. **Guarantee application** — Draft 1 permitted debiting share capital, breaking DEC-11, L-4, and its own §4.8 rule. Restricted to SAVINGS (§4.6, LA-9).
6. **Write-off** — Draft 1 wrote off principal only, leaving uncollectible interest and phantom income. Added interest reversal and a non-accrual policy (§4.9).
7. **Missing accounts** — hold-control (9000–9020), 1120 Loan Fees Receivable, 1950 Rounding Differences, 3150 Reserves, 4010 Interest Reversed, 5400 Processing Fees. Deleted unused 5300.
8. **Missing subsidiary FKs** — E-24/E-27/E-43 had no backing Account, making L-2 uncomputable for three controls (§8.10).
9. **Holds** — removed the mutable "active" semantic; releases are arithmetic (§3). L-3 demoted from invariant to validation rule.
10. **Five further missing transaction types**, including `SAVINGS_TRANSFER` — funding a Savings Goal from the Transaction Account, the most common member flow, had no posting rule.
11. **Fee waterfall** — the three-bucket waterfall had a two-leg posting; added 1120.
12. **Rail settlement** — wire and RTP had no settlement leg, so 1040/1050 could never clear; ACH outbound had no hold stage, silently changing member-facing behaviour.
13. **Interchange** — was posted in two places; now once.
14. **Cross-reference fixes** — E-17 not E-16; FBO structure is `04` §4.3 not §1.2; stand-in and cached balance are `04` §4.5 not §4.3; §7.5 no longer contradicts its own source on stand-in behaviour.

*End of document.*
