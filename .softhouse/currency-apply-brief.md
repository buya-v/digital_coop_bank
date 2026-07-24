# Currency APPLY brief — USD → MNT (DEC-18), PO-confirmed

**This is the single source of truth for the currency-apply run.** Do NOT re-derive
values. Apply exactly what is confirmed below; HOLD exactly what is listed as held.
Provenance: derivation table `.softhouse/handoff/20260721-currency-policy/T3.md`
(re-derivation against Mongolian median wage, NOT conversion); PO confirmed the
anchors (share par ₮10,000 *provisional*; limits "accept recommended"; round-ups
*deferred*).

## Non-negotiable notation (from CLAUDE.md)
- Money is **integer minor units** conceptually; in prose, **display whole tugrik,
  postfix ₮ with thousands separators**: `1,150,000₮`. No decimal tugrik (möngö is
  obsolete). Never write a float money value.
- Do not invent precision. All figures are whole tugrik.
- When you replace a USD figure, replace the **whole token** including `$` and any
  `.00`. `$1,000.00` → `550,000₮`. Never leave a stray `$` or `.00`.

## CONFIRMED — apply these (income-anchored, W = median monthly wage ₮2,278,400)
| Role / where it appears | old USD | NEW MNT | notes |
|---|---|---|---|
| Membership share **par** (DEC-11 / OI-1) | $25 / $25.00 in the **par role** | **10,000₮** | **provisional** — on first use per document add "(provisional, pending DEC-11 / legal)". KEYSTONE. |
| AML external **step-up** threshold (DEC-36) | $1,000 / $1,000.00 (step-up role) | **550,000₮** | 0.25·W. Distinct from de-ratified loan cap — check role per line. |
| P2P **daily velocity** limit (DEC-33) | $2,000 / $2,000.00 | **1,150,000₮** | 0.50·W. "seed, not hard-coded" wording stays. |
| **Loan minimum** (DEC-45) | $100 / $100.00 in the **loan-bound role** | **100,000₮** | 0.05·W. MOST $100 tokens are scenario balances — see coupled examples; only the loan-min role maps here. |
| **Loan maximum** (DEC-45) | $5,000 / $5,000.00 in the **loan-cap role** | **5,700,000₮** | 2.5·W. Also appears as US-9.3 per-project match cap — split by line. |
| AML **aggregate-outbound** monitoring (DEC-73) | $10,000 / $10,000.00 (AML role) | **11,400,000₮** | 5·W. Distinct from DEC-65 program match-cap $10,000 (that is HELD). |
| Above-cap validation **example** | $6,000 / $6,000.00 | **6,840,000₮** | = 1.2 × loan max. RECOMPUTE from the confirmed max; do not scale the digits. |
| Zero / fee-zero | $0 / $0.00 | **0₮** | zero maps to zero. |

## CONFIRMED — worked examples: RE-DERIVE from the formula, never scale digits
Use share par P = 10,000₮ and the limits above. Label each re-derived example
"(illustrative, pending confirmed par)" where it depends on par. Formulas
(full detail in the T3 handoff §A–M — read it):
- Dividend reinvest: `shares = ⌊E / P⌋`, `reinvest = shares·P`, `residual = E − shares·P`.
- Ledger check `939 × $25` → `939 × 10,000₮ = 9,390,000₮`.
- Interest yield: `principal × APR` — **APR percent is unchanged**; re-derive only the principal, then recompute the interest. Do not scale the dollar interest.
- P2P remaining: `remaining = velocity_limit − sent` (recompute from re-derived operands).
- Step-up flag: `flag if amount > 550,000₮`.
- Balance/goal/lock/split/ROSCA: recompute the difference/quotient from re-derived operands — never linearly scale a coupled operand independently.
- AML structuring `9 × $980 < $10,000` → keep `n × amount` just under `11,400,000₮`; recompute the per-item amount to stay sub-threshold.

## HELD — DO NOT CHANGE (leave the USD token as-is). These are not oversights.
Add NOTHING in-line except, where natural, a brief `<!-- held: <reason> -->` HTML
comment is acceptable but not required (the run tracks these centrally). Held sets:
1. **KPI cluster** (magnitude-truncated by the earlier regex — the real values are $M):
   $25M AUM Y1, $150M AUM Y2, $1,500 avg deposit/member, CPA ≤ $25, $1.5M community
   capital (shown as `$1`), $25,000,000 AUM illustration. Reason: KPI re-baselining is
   a separate task (sector/market-size driven, not income-driven).
2. **Persona incomes**: $55k/$90k (P-1), $35k/$60k (P-2), $45k/$70k (P-3). Reason:
   these are the USD incomes the migration re-anchors AGAINST; routed to the
   income-basis task, not this pass.
3. **Round-up amounts** (DEFERRED by PO): the round-up denomination, $5.00 batch
   settle threshold (DEC-67), $3.45/$0.55-style round-up examples, all of EP-10's
   amounts. Reason: round-ups deferred; no confirmed ₮ denomination.
4. **$88.20 loan installment** (03:~904, ~931): BLOCKED on the rate model
   (DEC-48/49/52). Leave as-is.
5. **Program-config caps**: DEC-65 surplus-match ceiling ($10,000 and superseded
   $500), DEC-63 pitch-goal bounds ($1,000–$100,000). Reason: program-budget
   decision, held with the KPI cluster.
6. **Superseded / de-ratified values** in prose that DESCRIBES a rejected past
   decision: $10.00/$5 par drafts, $1,000 de-ratified loan cap (DEC-45 history),
   $2.00/$5.00 Sprint-1 round-up drafts. Leave as historical record — do not
   re-denominate a value the document is explaining it rejected.

## Documents in scope for THIS run
Apply: **01, 02, 03, 04, 05**. 
NOT this run: **06** (ledger addendum — do-not-implement, awaiting a controller
rewrite; re-denominating doomed content is wasted effort) and **00** (no USD refs;
needs its own Mongolia rewrite — backlog).

## Rules for every apply agent
- Edit **line by line, by ROLE**. The same token ($25, $100, $10,000) means
  different things in different places — the tables above disambiguate by role.
  A blind find-replace corrupts the polysemous tokens. When unsure of a token's
  role, STOP and flag it in your handoff rather than guess.
- Preserve each document's header block, `DEC-n`/`US-n.n`/`EP-n`/`E-n` IDs, and
  traceability. Do not renumber or restructure.
- If applying a value would contradict a ratified DEC-n's *meaning* (not just its
  number), STOP and report — that is a `user` decision.
- Run `.softhouse/verify-docs.sh` before finishing; it must not regress on HARD
  checks. The USD DRIFT count will legitimately DROP (that is the point); the
  verifier re-baselines it centrally — you do not edit the baseline.
- Record in your handoff: every token you changed (old→new + role), every token you
  deliberately HELD (with which held-set), and any token whose role you could not
  determine.
