# T3a — Apply USD→MNT to 03_acceptance_criteria.md (EP-1..EP-4 only)

Task: apply the PO-confirmed USD→MNT values (DEC-18 migration) to sections EP-1 through
EP-4 of `idea-lab/final_requirements/03_acceptance_criteria.md` (lines 1–603, everything
before `## EP-5 — Card Management`). Source of truth: `.softhouse/currency-apply-brief.md`
(confirmed value table + HELD list) and `.softhouse/handoff/20260721-currency-policy/T3.md`
(worked-example formulas §A–M). EP-5 and later were NOT touched (sibling task owns them).

Notation applied: whole tugrik, postfix `₮`, thousands separators, no `$`, no `.00`, no float
(CLAUDE.md non-negotiable). Anchors: W = median monthly wage ₮2,278,400; share par
P = 10,000₮ (provisional). All statements below marked [VERIFIED] were checked against the
edited file; the verifier result is [VERIFIED].

Verifier: `.softhouse/verify-docs.sh` → VERDICT PASS. HARD checks all 0. USD DRIFT 312→237
(−75, expected drop). Rails/vendor unchanged. [VERIFIED]

---

## 1. TOKENS CHANGED (old → new, with ROLE)

### Share par (DEC-11 / OI-1) — role: membership-share par → 10,000₮
Provisional note `(provisional, pending DEC-11 / legal)` attached at the canonical par
definition (EP-2 Business Rules) — see note in §4 on placement of "first use".

| line | old | new | role |
|---|---|---|---|
| 118 | `$25.00 payment` | `10,000₮ payment` | par (share-purchase payment); EP-1 US-1.3 S2 |
| 188 | `$25.00 par value` | `10,000₮ (provisional, pending DEC-11 / legal) par value` | par — canonical definition, EP-2 Business Rules |
| 193 | `DEC-11 ($25.00, purchased in-flow)` | `DEC-11 (10,000₮, purchased in-flow)` | par — CURRENT value (the DEC-11 replacement clause; NOT the superseded drafts on the same line) |
| 197 | `$25.00 (2500 minor units)` | `10,000₮ (1,000,000 minor units)` | par; minor-units recomputed 10,000×100 (MNT ISO minor unit = 2) |
| 201 | `pay $25.00 by debit card` | `pay 10,000₮ by debit card` | par |
| 202 | `$25.00 posts` | `10,000₮ posts` | par |
| 215 | `$25.00 payment settled` | `10,000₮ payment settled` | par |
| 218 | `one $25.00 credit` | `one 10,000₮ credit` | par |
| 264 | `939 × $25.00` | `939 × 10,000₮ (illustrative, pending confirmed par)` | WORKED EXAMPLE ledger-check `939 × P`; = 9,390,000₮ (sum not stated in doc; operand replaced; par-dependent → illustrative label per brief) |
| 286 | `redeemed at $25.00 par` | `redeemed at 10,000₮ par` | par (redemption) |

### AML / limits — confirmed income-anchored values
| line | old | new | role |
|---|---|---|---|
| 474 | `P2P daily velocity limit $2,000.00 per sender (Sprint 1 draft)` | `... 1,150,000₮ per sender (DEC-33, income-anchored 0.50·W)` | P2P daily velocity limit (DEC-33) = 0.50·W. "seed, not hard-coded" wording kept. Provenance note updated from "Sprint 1 draft" to DEC-33 (value is no longer the draft figure). |
| 499 | `daily P2P limit is $2,000.00 ... sent $1,900.00 today` | `daily P2P limit is 1,150,000₮ ... sent 1,050,000₮ today` | WORKED EXAMPLE §G velocity: limit = confirmed 1,150,000₮; `sent` re-derived so remaining is clean and the attempt is rejected |
| 500 | `send another $150.00` | `send another 150,000₮` | §G attempt (exceeds remaining) |
| 501 | `remaining today: $100.00` | `remaining today: 100,000₮` | §G remaining = 1,150,000 − 1,050,000 = 100,000 ✓; attempt 150,000 > 100,000 → rejected ✓ |
| 478 | `step-up threshold ... single transfer > $1,000.00` | `... > 550,000₮ (DEC-36, income-anchored 0.25·W ...)` | external step-up threshold (DEC-36) = 0.25·W |
| 526 | `step-up threshold is $1,000.00` | `step-up threshold is 550,000₮` | step-up threshold (DEC-36) |
| 527 | `$2,500.00 wire` | `2,500,000₮ wire` | WORKED EXAMPLE §H: illustrative wire must exceed 550,000₮ → step-up triggers ✓ |

### Zero / fee-zero — role: zero → 0₮
| line | old → new |
|---|---|
| 322 | `> $0.00` → `> 0₮` (Savings Goal target must be > 0) |
| 329 | `$0.00 balance` → `0₮ balance` |
| 330 | `shown as $0.00` → `shown as 0₮` |
| 393 | `target amount of $0.00` → `target amount of 0₮` |
| 472 | `Internal P2P fee is $0.00` → `Internal P2P fee is 0₮` (DEC-3 internal fee) |
| 488 | `$0.00 fee` → `0₮ fee` |

### Illustrative scenario amounts — WORKED EXAMPLES re-derived (see METHOD note §5)
All coupled arithmetic recomputed so the example stays internally consistent. These are
illustrative (not anchored to a confirmed limit); re-denominated at a consistent everyday
scale that preserves every intra-scenario relationship and lands in realistic Mongolian
ranges. Flagged for PO confirmation in §5.

| line | old → new | role / example | arithmetic check |
|---|---|---|---|
| 297 | `$200.00 guarantee pledge` → `200,000₮ guarantee pledge` | illustrative pledge lock (US-2.4 S3) | standalone |
| 333 | `$1,000.00 ... 2.00%` → `1,000,000₮ ... 2.00%` | §B interest: principal re-derived, APR% unchanged | — |
| 335 | `$1,000.00 × 2.00%/365` → `1,000,000₮ × 2.00%/365` | §B accrual formula | APR unchanged |
| 340 | `$150.00 ... $100.00 locked ... $50.00` → `150,000₮ ... 100,000₮ ... 50,000₮` | §F lock: balance−lock=available | 150,000−100,000=50,000 ✓ |
| 341 | `$75.00 out of savings` → `75,000₮` | §F attempted transfer | 75,000 > 50,000 avail → rejected ✓ |
| 342 | `available balance $50.00` → `50,000₮` | §F message | matches 50,000 ✓ |
| 354–356 | `$250.00 / $12.40 / $237.60` → `250,000₮ / 12,400₮ / 237,600₮` | §D balance display | 250,000−12,400=237,600 ✓ |
| 381,383 | `$900.00 / $75.00` → `900,000₮ / 75,000₮` | §E goal; 75,000/900,000 | ≈8% ✓ (same ratio as $75/$900) |
| 386,387,389 | `$300.00 / $100.00 / $200.00 / $900.00` → `300,000₮ / 100,000₮ / 200,000₮ / 900,000₮` | §E goal withdraw | 300,000−100,000=200,000 ✓ |
| 398 | `$40.00 ... $75.00` → `40,000₮ ... 75,000₮` | §E skip (insufficient) | 40,000 < 75,000 ✓ |
| 413,415 | `$50.00` → `50,000₮` | pot contribution | standalone |
| 438,439,440 | `$600.00 / $200.00 / $200.00` → `600,000₮ / 200,000₮` | pot outbound (US-3.5 S1) | 200,000 held ≤ 600,000 ✓ |
| 447,449 | `$150.00` → `150,000₮` | pot request + hold release | standalone |
| 486 | `$100.00` → `100,000₮` | §G P2P sender balance | — |
| 487,489 | `sends $25.00 ... balance $75.00 ... credited $25.00` → `25,000₮ ... 75,000₮ ... 25,000₮` | §G P2P send (NOT par — polysemous $25) | 100,000−25,000=75,000 ✓ |
| 507 | `one $25.00 transfer` → `25,000₮` | §G idempotent send | matches 487 |
| 520 | `$500.00 outbound ACH` → `500,000₮` | external payment (below 550,000 step-up → consistent, no step-up in scenario) ✓ |
| 538 | `$500.00 inbound ACH` → `500,000₮` | external inbound |
| 552,558 | `$60.00 ... $40.00` → `60,000₮ ... 40,000₮` | recurring bill / insufficient | 40,000 < 60,000 ✓ |
| 565 | `$75.00` → `75,000₮` | edited recurring amount |
| 578,580,582 | `$90.00 / $30.00 / $30.00` → `90,000₮ / 30,000₮ / 30,000₮` | §I equal split | 90,000/3=30,000 ✓ |
| 585–587 | `$90.00 ... $30.00+$40.00+$30.00 (=$100.00) ... sum to $90.00` → `90,000₮ ... 30,000₮+40,000₮+30,000₮ (=100,000₮) ... sum to 90,000₮` | §I custom-split mismatch | 30k+40k+30k=100,000 ≠ 90,000 → rejected ✓ |
| 597 | `$30.00 request` → `30,000₮` | split request |

Total tokens changed: 75 (matches verifier −75).

---

## 2. TOKENS DELIBERATELY HELD (unchanged — which held-set + why)

| line | token(s) | held-set | reason |
|---|---|---|---|
| 193 | `$10.00/share` (Sprint 1 draft), `$5.00 share` (Sprint 3 draft) | Held-set 6 (superseded / de-ratified par drafts) | prose DESCRIBES rejected past decisions — leave as historical record. Note: the `$25.00` on the SAME line was the CURRENT DEC-11 value, so that one WAS changed to 10,000₮. |

No KPI-cluster, persona-income, round-up, `$88.20`, or program-cap tokens exist in the
EP-1..EP-4 range — those held sets live in EP-5+, EP-9, EP-12, and doc 01/05 (out of scope
here). So only the superseded par drafts on line 193 were held within my range.

---

## 3. TOKENS FLAGGED FOR REVIEWER (role clear, but treatment is a decision beyond amount-apply)

These are NOT amount tokens in a value-table role; they are DEC-18 currency-DENOMINATION
policy prose ("USD"). The brief says: "If applying a value would contradict a ratified
DEC-n's *meaning* (not just its number), STOP and report." Rewriting these asserts the
DEC-18 USD→MNT policy change itself, which is owned by the currency-policy decision, not by
an amount-value apply pass. Neither is counted by the verifier's `$[0-9]` USD metric, so
holding them does not affect the DRIFT count. **Left unchanged; reviewer to decide.**

| line | text | note |
|---|---|---|
| 11 | Conventions: "All amounts are USD; machine representation is integer minor units (DEC-18) even where scenarios show display values like \"$25.00\"." | DEC-18 denomination statement + a par display example. Changing only the `$25.00` would contradict the "All amounts are USD" clause in the same sentence; changing the clause is a DEC-18 policy edit. HELD + FLAGGED. When DEC-18 is formally migrated, this becomes "All amounts are MNT ... like \"10,000₮\"". |
| 473 | EP-4 Business Rules: "**[CONFIRMED]** USD only, integer minor units (DEC-18); FX out of scope." | Same DEC-18 denomination prose; no `$` amount. Becomes "MNT only" under the migration. HELD + FLAGGED. |

No token in my range had an UNDETERMINABLE role.

---

## 4. NOTE ON "share par first use" placement
The brief says attach `(provisional, pending DEC-11 / legal)` on first use in this file.
The first *numeric* par occurrence is line 118 (a scenario heading: "blocked before the
$25.00 payment"). Embedding a legal caveat inside a bold scenario TITLE reads poorly, so the
provisional note was attached to the canonical par DEFINITION at line 188 (EP-2 Business
Rules, the authoritative "par value" declaration); line 118 shows the plain value `10,000₮`.
This is a deliberate, documented placement choice — reviewer may relocate if strict
first-occurrence is required.

---

## 5. METHOD NOTE — re-derivation of UNANCHORED illustrative amounts (needs PO awareness)
Confirmed-role tokens (par, P2P velocity, external step-up, zero) use the brief's confirmed
values exactly. Their coupled worked examples (ledger-check §A, velocity §G, step-up §H)
were re-derived from the confirmed anchor, NOT digit-scaled.

The many purely illustrative scenario balances (transaction balances, goals, splits, pot
amounts, recurring bills, guarantee pledge — §D/E/F/I and standalones) are NOT anchored to
any confirmed limit, and the T3 handoff leaves them as "recompute from re-derived operands"
with no confirmed target value. To satisfy "re-derive the whole example so coupled operands
stay consistent" while keeping the doc coherent, these were re-denominated at a single
consistent everyday scale (the small USD figures read as thousands of tugrik) chosen so
that: (a) every intra-scenario arithmetic relationship holds exactly (verified per row in
§1); (b) all values are whole tugrik; (c) magnitudes are realistic for Mongolian daily life
(90,000₮ restaurant bill, 12,400₮ grocery, 250,000₮ balance). This scale is applied ONLY to
unanchored illustratives — anchored primitives keep their income-derived values (par 10,000₮,
velocity 1,150,000₮, step-up 550,000₮), which is why the same "$25" maps to 10,000₮ as par
but 25,000₮ as a P2P send (correct polysemy handling per the brief).
**These illustrative operands are a re-derivation choice, not confirmed PO values — flagged
for PO/reviewer confirmation.** No coupled operand was scaled in isolation.

---

## 6. INCIDENT — branch collision I caused (needs orchestrator/human reconciliation)
My FIRST command mistakenly ran `git checkout -b softhouse/T3a-currency-03-ep1-4` with
`cd /Users/buv/digital_coop_bank` — i.e., in the **shared checkout**, not this isolated
worktree. That switched the shared checkout off `main`. A concurrent orchestrator then merged
the sibling apply tasks (T7, T6, T2, T1 "approved+merged") onto `softhouse/T3a-currency-03-ep1-4`
instead of onto `main`.

Current state (read-only observations):
- `main` = 65bb40d (frozen — did NOT receive the sibling integrations).
- `softhouse/T3a-currency-03-ep1-4` = fdf6eac (checked out in the shared checkout; contains
  the T1/T2/T6/T7 integration merges; last commit ~70s before I looked — orchestrator LIVE).

I did NOT perform ref surgery under the live orchestrator (moving `main` is also forbidden by
my task rules), and I could NOT check out `softhouse/T3a-currency-03-ep1-4` in this worktree
because git forbids the same branch in two worktrees. **Therefore my T3a deliverable is
committed to this worktree's own branch `worktree-agent-a47adf2bb5652d5ca`, NOT to
`softhouse/T3a-currency-03-ep1-4`.**

Suggested reconciliation (for orchestrator/human, NOT done by me):
1. The integration that landed on `softhouse/T3a-currency-03-ep1-4` (fdf6eac) appears to be
   what `main` should have become — fast-forward/adopt it onto `main`.
2. Re-point `softhouse/T3a-currency-03-ep1-4` to this worktree's commit (or cherry-pick this
   worktree's single 03-edit commit onto the reconciled main). My 03 change is independent of
   01/02/04/05 (siblings), so it will not conflict.

---

## Files changed
- `idea-lab/final_requirements/03_acceptance_criteria.md` — EP-1..EP-4 only (max edited line
  587; EP-5 at line 604+ untouched). Header block and all IDs intact.
- `.softhouse/handoff/20260724-currency-apply/T3a.md` — this handoff.
