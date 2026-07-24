# T3c — Apply USD→MNT to 03_acceptance_criteria.md, EP-8..EP-13 + checklist

Task T3c (APPLY). Scope: `idea-lab/final_requirements/03_acceptance_criteria.md`, from
the `## EP-8` header (line ~1080) to end of document. EP-1..EP-7 were already merged by
T3a/T3b and were **not touched**. Branch: `softhouse/T3c-currency-03-ep8-13`.

Inputs read in full: `CLAUDE.md`; `.softhouse/currency-apply-brief.md` (confirmed table +
HELD sets); `.softhouse/handoff/20260721-currency-policy/T3.md` (derivation formulas §A–M).
Convention followed (merged T3a/T3b): confirmed anchors from the brief applied exactly;
unanchored illustrative amounts re-derived at a consistent **×1000 everyday scale** so every
intra-scenario relationship stays exact; each is a PO-confirmation choice pending the wage-unit
caveat (T1 D1). No float, whole-tugrik postfix `N,NNN₮`, no stray `$`/`.00`.

**Honesty posture:** [VERIFIED] = I confirmed the line/token and role directly in the file.
Ambiguous-role tokens are flagged, not guessed. This range is HELD-heavy; I erred toward HOLD.

---

## EP-8 — Democratic Governance & Voting
**No monetary tokens.** [VERIFIED] Numbers present are signature thresholds (500 sigs),
field-length bounds, and HTTP status codes — not money. Nothing to change.

---

## CHANGED tokens (old → new, with role)

| Line | Old | New | Role / derivation | Tag |
|---|---|---|---|---|
| EP-11 US-11.1 Sc1 (1495) | `$25.00` | `25,000₮` | P2P send illustrative (same role as EP-4 P2P send, already 25,000₮). ×1000. | [VERIFIED] |
| EP-12 US-12.3 Sc2 (1618) | `$400.00` | `400,000₮` | Loan counter-offer amount; within loan bounds (100,000–5,700,000₮). ×1000. | [VERIFIED] |
| EP-12 US-12.3 Sc2 (1618) | `$500.00` | `500,000₮` | Requested loan amount (matches EP-6 500,000₮ loan). ×1000. Kept exact vs the 400,000₮ counter. | [VERIFIED] |
| EP-12 US-12.3 Sc5 (1636) | `$50.00` | `50,000₮` | Partial guarantee-pledge release (EP-6 pledge role). ×1000. | [VERIFIED] |
| EP-12 US-12.3 Sc5 (1637) | `$50.00` | `50,000₮` | Same release amount — lock reduction; kept identical to the release above. ×1000. | [VERIFIED] |
| EP-12 US-12.6 Sc3 (1705) | `$12.40` | `12,400₮` | Dividend-run reconciliation drift illustrative. ×1000. | [VERIFIED] |
| EP-13 BR (1728) | `$10,000.00` | `11,400,000₮` | **CONFIRMED** DEC-73 AML aggregate-outbound (5·W). Added `(DEC-73, income-anchored 5·W)`. Not ×1000 — confirmed anchor. | [VERIFIED] |
| EP-13 US-13.1 Sc1 (1736) | `$980.00` | `1,250,000₮` | AML structuring §M. **RE-DERIVED, not scaled:** 9 × 1,250,000₮ = 11,250,000₮, held just under the 11,400,000₮ monitor. Added the aggregate note inline. | [VERIFIED] |
| EP-13 US-13.5 Sc3 (1839) | `$0.00` | `0₮` | Zero → zero (brief confirmed). Generic "zero-derived figures" display principle in the Impact Scorecard (US-13.5) — not the held $25M AUM (US-13.4). | [VERIFIED] |

**Structuring recompute rationale (§M):** brief says keep `n × amount` just under the DEC-73
aggregate (11,400,000₮) and recompute the per-item, do NOT scale $980. Chosen per-item
1,250,000₮ → 9× = 11,250,000₮ (98.7% of threshold), a strong "just under" structuring signal;
1,250,000₮ is a clean whole-tugrik value (matches CLAUDE.md's display example). Deliberately
avoided 1,150,000₮ to prevent collision with the P2P velocity limit.

**Count:** 9 USD tokens converted. Verifier USD DRIFT 140 → 131 (−9). HARD checks all still 0.

---

## HELD tokens (left as USD — deliberate, not oversights)

### EP-9 — Community Funding Hub — HELD IN FULL (held-set 5 program-config + held-set 1 KPI)
Rationale: EP-9's entire monetary illustration is coupled to program-config/KPI values the
brief holds — DEC-63 pitch-goal bounds ($1,000–$100,000), DEC-65 surplus-match ceiling
($10,000 / superseded $500), and the KPI-4.2 Community Grant pool (10% of surplus, tied to the
held KPI-4.4 $1.5M community capital). Re-denominating member-side amounts while their governing
bounds/caps/pool stay USD would mix currencies inside single scenarios. Held the whole epic
(incl. its `$0.00` project-funding/escrow zeros) so each project stays internally USD-consistent
until the program-budget decision. This is the safe direction per the brief's "if unsure, HOLD
and flag" and "THIS RANGE IS HEAVY ON HELD SETS — do NOT over-apply."

| Line | Token(s) | Held-set / reason |
|---|---|---|
| 1302 | `$1,000.00`, `$100,000.00` | 5 — DEC-63 pitch-goal bounds |
| 1304 | `$500.00` (superseded flat cap), `$10,000` (DEC-65 ceiling) | 6 / 5 |
| 1311 | `$50,000.00` | 5 — pitch budget within DEC-63 bounds |
| 1315 | `$0.00` | project-space zero (kept USD for scenario consistency) |
| 1324 | `$500.00` | 5 — pitch goal example vs DEC-63 min |
| 1326 | `$1,000.00` | 5 — DEC-63 min bound (validation message) |
| 1338 | `$800.00`, `$20,000.00` | goal → 5; `$800` savings-side **[FLAGGED — see below]** |
| 1339,1340 | `$100.00` ×2 | Backing amounts, EP-9 space **[FLAGGED]** |
| 1344 | `$250.00`, `$200.00`, `$50.00` | savings avail-balance arithmetic **[FLAGGED — arguably ×1000]** |
| 1345,1346 | `$100.00`, `$50.00` | Backing / available **[FLAGGED]** |
| 1350 | `$20,000.00`, `$18,000.00` | 5 — goal + raised (DEC-63 space) |
| 1353 | `$0.00` | escrow-drain zero (project-space) |
| 1363 | `$150,000.00`, `$5,000.00` | 1 (KPI-4.2 pool) / 5 (DEC-65 project cap) — §L worked example |
| 1364,1365 | `$100.00` ×2 | §L match example (backing + match) |
| 1369 | `$4,000.00` | §L accrued matches |
| 1376 | `$4,950.00`, `$5,000.00` | §L cap-boundary example (DEC-65 cap) |
| 1377,1378 | `$100.00`, `$50.00` | §L backing + partial match |
| 1382,1383,1384 | `$10.00`, `$100.00`, `$10.00` | §L pool-exhaustion example |
| 1395 | `$20,000.00`, `$5,000.00`, `$18,000.00` | 5/1 — project raised/matched/disbursed |
| 1409 | `$100.00` | project-contribution display fallback |

**FLAGGED (ambiguous role — held, not guessed):** US-9.2 Scenarios 1 & 2 amounts
(`$800`, `$100`, `$250`, `$200`, `$50`) are savings-side available-balance illustratives,
structurally identical to EP-3/EP-6 scenarios that WERE converted ×1000. They are *not*
themselves program-config. I held them anyway because (a) each is a "Backing" inside the
held community-funding space, and (b) converting them would place MNT member amounts against
held-USD project goals/caps in the same scenario. **PO/reviewer decision:** if EP-9 is to show
member amounts in MNT, these five tokens convert cleanly at ×1000 ($800→800,000₮, $100→100,000₮,
$250→250,000₮, $200→200,000₮, $50→50,000₮) — but only alongside a decision on the held project
goals/caps to keep each scenario single-currency.

### EP-10 — Round-Up Savings — HELD IN FULL (held-set 3, DEFERRED by PO)
Every token left as USD; round-ups have no confirmed ₮ denomination. [VERIFIED] none touched.
Lines/tokens: 1420 `$0.00`; 1422 `$5.00` ×2; 1424 `$2.00`/`$5.00` (superseded, held-set 6);
1430 `$50.00`; 1437 `$0.00`; 1449 `$4.60`; 1450 `$3.45`; 1451 `$0.55`; 1452 `$5.00`,`$5.15`;
1457 `$15.00`; 1458 `$0.00`; 1462 `$12.40`; 1463 `$0.60`,`$1.20`; 1464 `$1.20`; 1467 `$5.00`,
`$3.00`; 1473 `$50.00`,`$49.40`; 1474 `$0.90`; 1475 `$0.60`.

### EP-13 — one held token
| Line | Token | Held-set / reason |
|---|---|---|
| 1806 | `$25,000,000.00` | 1 — KPI AUM illustration (ties to $25M AUM Y1; sector/market rebaseline, not income-driven) |

---

## Verification
- `.softhouse/verify-docs.sh`: **VERDICT PASS.** HARD all 0 (unchanged). USD DRIFT 140 → **131**
  (−9, below baseline 312). Rails/vendor unchanged. [VERIFIED — ran the script]
- No float introduced; all new values whole tugrik with `₮` postfix; no stray `$` or `.00` in
  any converted token. [VERIFIED — re-grepped EP-8..end: remaining `$` tokens are exactly the
  held EP-9 / EP-10 / $25M sets above.]
- Header block, DEC-n/US-n.n/EP-n/CAP-n IDs, and the Story Coverage Checklist untouched (the
  checklist has no monetary tokens). [VERIFIED]

## Blockers / follow-ups for the PO
1. **EP-9 whole-epic hold** — resolve DEC-63 pitch-goal bounds, DEC-65 match cap, and the
   KPI-4.2 pool budget together, then re-derive EP-9 in one pass (member amounts at ×1000,
   caps/bounds/pool re-derived proportionally to the program budget).
2. **US-9.2 flagged savings amounts** — cheap ×1000 conversion available once (1) lands.
3. **Round-up ₮ denomination** (EP-10) — still deferred; unblocks EP-10 amounts.
4. **Wage-unit caveat (T1 D1)** rides on all ×1000/income-anchored values here.

no code executed
