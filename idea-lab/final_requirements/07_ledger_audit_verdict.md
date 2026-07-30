# Ledger Design — Independent Audit Verdict

**Document ID:** 07_ledger_audit_verdict
**Status:** Audit findings for controller ratification (2026-07-30). NOT an implementation authorization.
**Scope:** An adversarial audit of `06_ledger_addendum.md` (Draft 2, 608 lines) by three
independent auditors with distinct lenses (posting correctness; holds/available/precision;
invariants/interest-dividend/completeness), each re-deriving the accounting from first
principles + `04` §2.3 + `03` acceptance criteria + the CLAUDE.md non-negotiables. This is
a **design audit** — no code was written, no money moves. A qualified controller / core-banking
engineer must ratify this before any implementation.

> **Why this exists.** CLAUDE.md flags `06` as carrying five critical defects incl. an
> "inverted hold formula". The current `06` *reads* `available = balance − signed_sum(MEMO_HOLD)`,
> which superficially looks corrected. The audit tested that — and everything else — by
> re-derivation, not by trusting `06`'s prose.

---

## Bottom line

`06` is a **materially better, largely-correct** design than its reputation — four of the five
historically-claimed defects are genuinely fixed, and the internal double-entry model, interest
math, integer dividend apportionment, invariants, and precision model are **verified sound**.
But it is **NOT yet controller-ready**, blocked by:

1. **CRITICAL / money-loss — the inverted-hold formula is still present** (source-verified below).
   A one-line correction is proposed and applied to `06` §3 as an audit fix (pending ratification).
2. **HIGH — `06` was never Mongolia-migrated.** It is entirely USD, US payment rails/vendors,
   hard-coded $25.00 par, and US-law framing. The market's `RTGS_OUT` (Banksüljee) has no posting rule.
3. **MEDIUM / open — the patronage-dividend factor aggregation** is corrected in prose but not
   encoded, and depends on unratified decisions (LA-8/LA-11/LA-13).

**Recommended path:** implement the **core ledger + interest** after (1) and a full MNT
re-denomination; **gate the dividend engine** on LA-8/LA-11/LA-13; supply the completeness items.

---

## 1. CRITICAL — inverted available-balance formula (§3, verified against source)

`06` computes (§3): `available_balance = balance − signed_sum(MEMO_HOLD entries on the account)`.
- §1.2: a *signed balance* is computed in the account's **own normal direction** — a savings
  account is **credit-normal**, so `signed_sum = Σ(CREDIT) − Σ(DEBIT)`.
- §4.4/§4.6: every hold posts as a **debit to the member account** (`Dr Member TXN / Cr 9000`;
  `Dr Guarantor SAV / Cr 9010`).

**Re-derivation of the canonical acceptance case (03:340** — savings 150,000₮, 100,000₮ pledge,
required available = **50,000₮**, a 75,000₮ transfer must be **rejected**):
```
balance                    = Σcr − Σdr (FINANCIAL)  = 150,000
signed_sum(MEMO_HOLD)      = Σcr − Σdr = 0 − 100,000 = −100,000   (the hold is a DEBIT)
available = balance − signed_sum(MEMO_HOLD) = 150,000 − (−100,000) = 250,000₮   ✗
```
This equals Draft-1's `balance + hold` (150,000+100,000). The minus operator double-negates the
already-negative credit-normal memo sum, so it **adds** the hold. The "fix" was cosmetic.

**Money-loss consequence:** against available = 250,000₮ the 75,000₮ transfer is **allowed** — a
member spends 100,000₮ of pledged loan collateral; on the guaranteed loan's default the pledge
cannot be honoured. The card case is identical (a hold would *raise* available).

**This is the value of the audit:** the disguised defect survived two prior reviews and fooled one
of the three fresh auditors here (who asserted `150,000 − 100,000` without forcing the sign);
only re-deriving through `06`'s own §1.2 + §4 conventions surfaces it.

**Proposed fix (applied to `06` §3, pending controller ratification):**
`available_balance = balance + signed_sum(MEMO_HOLD entries on the account)`
→ 03:340: `150,000 + (−100,000) = 50,000₮` ✓; card auth reduces available ✓; release restores ✓.
A regression must pin **03:340 available = 50,000₮**. (Equivalent alternatives — post holds as
credits, or define the memo sum as a debit-positive magnitude — were rejected as less consistent
with §1.2; the operator flip is the minimal source-consistent correction.)

---

## 2. HIGH — `06` is not Mongolia-migrated (excluded from the currency/rails/vendor runs)

`06` was deferred in every baseline migration, so it alone still carries the US framing that
`00`–`05` and the backend no longer do:
- **Currency:** USD throughout; hard-coded **$25.00 par** in §4.1 / L-4 / §6.5 (must be **10,000₮**,
  DEC-11; par is US-12.5 config, never hard-coded). Note: the integer (no `float`, no `DECIMAL`) precision model is
  **currency-agnostic and survives** re-denomination (MNT minor unit is also 2) — this is a
  denomination change, not a precision-model change.
- **Rails/vendors:** chart of accounts has accounts `1010 Stripe Clearing`, `1040 Wire Clearing`, `1050 RTP/FedNow Clearing` (US payment-processor- and instant-rail-named); posting rules cover `WIRE_OUT`/`RTP_*`. The market is **ACH+ /
  Banksüljee (RTGS) / NETC**. **`RTGS_OUT` (the >₮5m rail) has NO posting rule**, and `06`'s rail
  transaction types do not reconcile with `04`'s migrated E-8 enum (`EXTERNAL_ACH_PLUS_* | RTGS_OUT`).
  The external-out flow is **unimplementable as written**.
- **Law:** disclosure obligations are framed as US deposit/transfer disclosure rules / Subchapter T; the Mongolian
  (FRC / Bank of Mongolia) analogues are unspecified.
- **MEDIUM:** an external-payment hold posts to `9000` (Card Authorization Holds) — no dedicated
  payment-hold memo account exists (§2.6 defines only 9000/9010/9020).

---

## 3. MEDIUM / open — patronage-dividend factor aggregation (§6.4)

The **direction** is corrected in prose (§6.4 Step 3): volume factors (avg savings, txn volume)
**sum**; rate factors (loan-repayment, governance scores) are **membership-month-weighted averages**
— "Draft 1 summed all four, a category error." **But the pseudocode does not encode the distinction**
(a single uniform "aggregate"), so an implementer coding to the formula reintroduces the bug. It is
formally open (**LA-11**), as is the surplus split (**LA-8**, needs Board ratification of
`dividend_share_bps`) and eligibility boundaries (**LA-13**). Worked example of the stakes: with one
governance factor and two members (12-month vs 3-month, both perfect), the weighted-average reading
splits a 600,000,000₮ pool 50/50 while the sum reading gives 80/20 — a **180,000,000₮/member swing**.
Not certifiable as correct until encoded and the decisions land.

---

## What is VERIFIED sound (controller-ready once §1 lands + MNT re-denomination)

Re-derived and confirmed by the audits:
- **Internal double-entry model** — the `04` `SYSTEM` catch-all is properly broken out into real
  cash/clearing/equity/income/expense/suspense/rounding/memo accounts; **contra accounts** carry an
  explicit per-account normal balance (not inferred from category).
- **Posting rules balance** (Σ debits = Σ credits, right accounts) for: share collection/remittance,
  internal transfer, P2P (0₮ fee balanced pair), group-pot contribution/approval, card auth→settle
  (interchange correctly not double-counted), interest posting, loan disburse + repayment waterfall
  (fees→interest→principal, accrued-interest account zeroes at payoff), and surplus→dividend→funding
  (year-end sequencing fixed).
- **Holds as real balanced postings** that change *available* but **not the deposit liability**
  (`balance`), released arithmetically (no mutable status) — the model is right; only the §3 operator
  was wrong.
- **L-3 correctly demoted** from a false invariant to a hold-placement validation (422); negative
  available is a legitimate observable state (LA-14 collections gap disclosed, not hidden).
- **Savings interest** re-derived exact (03:333 → 1,643.83₮): accrual on end-of-day FINANCIAL
  balance, ACT/365F, micro-cent accumulator, floored monthly posting with residual carry.
- **Integer dividend apportionment** (largest-remainder / Hamilton) **exact by construction**
  (`Σ entitlement = pool`), including the single-eligible-member edge case that broke the fractional
  method; fractional-share reinvestment integer-correct.
- **Invariants:** append-only; balances derived from entry sums with the materialized column a
  reconciled cache (nightly Drift check freezes on mismatch); single-writer/serializable; a
  meaningful nightly integrity set (L-1 trial balance, control=subsidiaries, shares×par, rounding,
  Σentitlement=pool).
- **Precision / no `float` or `DECIMAL`:** integer minor units end-to-end incl. int128 dividend and micro-cent
  interest intermediates; half-even rounding once at posting; residual carry to a monitored 1950
  Rounding Differences account — no value leak.
- **Four of the five historically-claimed defects are genuinely FIXED:** fractional-share identity,
  L-3 invariant, stand-in-authorization direction (now matches `04` §4.5), and the dividend
  category-error *direction* (though not yet encoded — §3 above). The fifth — the inverted hold
  formula — was **NOT** fixed (§1).

---

## Open items a controller must supply/decide before implementation

- Ratify the §1 hold-formula correction + add the 03:340 regression.
- Full **MNT re-denomination** of `06` (par 10,000₮; remove the $25.00 USD par); replace the US-vendor/rail-named
  clearing accounts (`1010 Stripe Clearing` / `1040 Wire Clearing` / `1050 RTP/FedNow Clearing`)
  + `WIRE_OUT`/`RTP_*` rules with **ACH+/Banksüljee(RTGS)/NETC**; add the **`RTGS_OUT`
  posting rule** and reconcile transaction types with `04`'s E-8 enum; add a payment-hold memo account.
- **LA-8** surplus split (`dividend_share_bps`), **LA-11** rate-vs-volume aggregation + E-31
  absent-value semantics (encode it), **LA-13** dividend eligibility boundaries.
- **§4.9** ten transaction types to add to E-8; **§4.10** policy + postings for account/pot closure
  residuals, deposit negative-balance collections (**LA-14**), provisional-credit-analogue provisional credit.
- Re-ground US-law disclosure framings (US deposit/transfer disclosure, Subchapter T) in FRC / Bank-of-Mongolia rules.
- Confirm PROPOSED thresholds (card-auth staleness, clearing-aging windows, rate/expiry seeds).

---

## Method note

Three auditors worked independently. Two, doing the arithmetic, found the §1 defect; one asserted
the formula was fixed. The orchestrator adjudicated **from the source** (§1.2 + §4.4/§4.6 → 250,000₮),
not by majority. A financial ledger is exactly where "prove it with numbers" must beat "reads correct":
this defect had already passed two prior reviews. Nothing here is asserted correct without a
re-derivation; every claimed defect shows its wrong number and its fix.
