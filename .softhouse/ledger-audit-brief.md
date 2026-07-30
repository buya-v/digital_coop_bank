# Ledger design — independent adversarial audit brief

**Goal:** produce a controller-ready verdict on the current ledger design
(`idea-lab/final_requirements/06_ledger_addendum.md`, 608 lines) via THREE
independent adversarial audits from distinct lenses, then a synthesis. This is a
DESIGN audit — no code, no live money. The output for a controller is: is this
design correct enough to implement, and exactly what (if anything) is still wrong.

## Why an audit, not a rewrite
CLAUDE.md flags 06 as "Draft 2, five confirmed critical defects incl. an inverted
hold formula (balance + hold)". But the CURRENT 06 already reads
`available_balance = balance − signed_sum(MEMO_HOLD)` (§3, ~line 151) and its own
text claims to have fixed Draft-1 errors (the inverted formula, the L-3 invariant,
dividend summing, the fractional-share identity, stand-in authorization). So 06 is
plausibly a LATER, largely-corrected version than its reputation. The audit's job is
to VERIFY that independently — adopt nothing on faith, re-derive everything.

## The honesty rule (non-negotiable for this task)
This is a financial ledger — a plausible-but-wrong posting rule is dangerous. State
only what you VERIFIED by re-deriving it. If a posting rule doesn't balance, show the
non-zero sum. If the hold formula is right, prove it against the acceptance criteria
with numbers. If you are unsure whether something is a defect, say "unverified —
needs a controller", do NOT guess. A false "this is correct" is the worst outcome.

## Ground truth to check against (NOT 06's own assertions)
- **CLAUDE.md non-negotiables**: double-entry + append-only; balances DERIVED, never
  written; corrections are reversing entries; **holds are postings, not mutable flags**;
  money is integer minor units, NO float anywhere (incl. intermediate calc); MNT.
- **04 §2.3** (E-6 Account / E-7 LedgerEntry / E-8 Transaction): every Transaction
  produces ≥2 entries that sum to zero; `balance` derived from LedgerEntry sums;
  `available_balance` = balance minus active holds (guarantee pledges, pot approvals,
  card auths); account_type incl. the SYSTEM catch-all that 06 must break out.
- **03 acceptance criteria the ledger MUST satisfy** (re-derive against 06's rules):
  - **03:340 (THE hold case)**: savings balance 150,000₮ with 100,000₮ locked as a
    guarantee pledge → available = **50,000₮**; a 75,000₮ transfer is REJECTED (422),
    no ledger entry, pledge untouched. (06's inverted Draft-1 formula would have given
    250,000₮ — verify 06 now yields 50,000₮.)
  - Group Pot 600,000₮, 2-of-3 approval, a 150,000₮ request cancelled → the 150,000₮
    hold RELEASED (03:438/449).
  - Guarantee pledge 200,000₮ locked against another member's active loan; closure
    blocked; pledge untouched (03:296).
  - Share purchase 10,000₮ (PENDING_PAYMENT → ACTIVE); Idempotency-Key mandatory on
    every money-movement; P2P instant 0₮ fee, balanced pair.
- **CLAUDE.md's 5 claimed defects** — for EACH, determine PRESENT vs ALREADY-FIXED in
  the current 06, with line-cited evidence: (1) inverted hold formula; (2)+(3)+(4)+(5)
  the other four (06's text references Draft-1 errors it claims to have fixed: the L-3
  "hold can't drive available negative" invariant, the dividend rate-vs-volume summing,
  the fractional-share Σ P(m)=1 identity, and the stand-in-authorization direction —
  verify each is actually corrected, not just re-asserted).

## The three lenses (one auditor each, independent — do NOT read each other's work)
- **A1 — POSTING CORRECTNESS**: §1.2 sign convention, §2 chart of accounts, §4 posting
  rules (4.1–4.10). For EVERY posting rule, do the debits and credits BALANCE (sum to
  zero) and hit the RIGHT accounts? Re-derive the worked flows: share purchase, deposit,
  internal transfer, P2P, external rail (ACH+/RTGS), card auth+settle, interest posting,
  loan disburse/repay, dividend payout. Contra accounts (normal-balance opposite to
  category) handled correctly? Are §4.9 "types to add" and §4.10 "flows without rules"
  gaps that block implementation? Any unbalanced rule = a defect with the non-zero sum.
- **A2 — HOLDS, AVAILABLE BALANCE, PRECISION**: §1.2 signs, §3 holds-as-memorandum,
  §5 precision/rounding/day-count, and the available-balance formula. PROVE
  available = balance − active holds against 03:340 (=50,000₮) and the pot/pledge cases.
  Confirm a memo hold changes available but NOT the deposit liability (balance). Verify
  NO float / integer minor units end-to-end incl. rounding; the rounding account/residual
  carry is sound. Is the inverted-hold defect present or fixed? Is hold placement/release
  sequenced correctly (no negative-available where 06 says it's a rejected placement)?
- **A3 — INVARIANTS, INTEREST/DIVIDEND MATH, COMPLETENESS, NON-NEGOTIABLES**: §6 interest
  & dividend, §7 balance integrity. Append-only? balances derived-not-written (single
  writer, materialized cache reconciled)? corrections as reversals? Re-derive the savings
  interest accrual (end-of-day FINANCIAL balance) and the Patronage Dividend (rate factors
  membership-month-weighted, volume factors summed — the §6.4 fix) and the integer
  fractional-share apportionment (§6.5). Every money non-negotiable held. Anything a
  controller would reject on sight.

## Output (each auditor)
A findings report: for each checked item, VERIFIED-correct (with the re-derivation) or
DEFECT (severity + exact location + the wrong result + the fix) or UNVERIFIED (why, needs
controller). Explicit verdict on your lens: is this part controller-ready? Plus your
line-cited call on each of CLAUDE.md's claimed defects that falls in your lens.
Do NOT edit any document. Return the report as your final message.
