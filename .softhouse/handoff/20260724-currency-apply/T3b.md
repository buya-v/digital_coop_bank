# T3b — Apply USD→MNT to 03_acceptance_criteria.md (EP-5..EP-7 only)

Task: apply the PO-confirmed USD→MNT values (DEC-18 migration) to sections **EP-5, EP-6, EP-7**
of `idea-lab/final_requirements/03_acceptance_criteria.md` (from the `## EP-5` header at line 604
up to the `## EP-8` header at line 1080). EP-1..EP-4 (merged via T3a) and EP-8+ were NOT touched.
Source of truth: `.softhouse/currency-apply-brief.md` (confirmed value table + HELD list) and
`.softhouse/handoff/20260721-currency-policy/T3.md` (worked-example formulas §A–M). Established
×1000 everyday-scale precedent for unanchored illustratives: T3a handoff (EP-1..EP-4) — followed
here for consistency.

Notation applied: whole tugrik, postfix `₮`, thousands separators, no `$`, no `.00`, no float
(CLAUDE.md non-negotiable). Anchors from the brief: share par P = 10,000₮ (provisional); loan
min 100,000₮ / loan max 5,700,000₮ (DEC-45); $6,000 above-cap example → 6,840,000₮ (= 1.2 × loan
max, recomputed).

**Verifier** [VERIFIED]: `.softhouse/verify-docs.sh` → VERDICT **PASS**. HARD checks all 0. USD
DRIFT 140 (−172 from baseline 312; reflects whole-tree migration incl. this pass). Rails/vendor
counts unchanged. All hunks confined to lines 679–1056 (inside the 604–1079 range) — confirmed by
`git diff -U0` hunk headers. **58 USD tokens re-denominated** (matches ₮ tokens added).

---

## 1. TOKENS CHANGED (old → new, with ROLE)

### EP-5 — Card Management (illustrative card scenarios; ×1000 everyday scale)
| line | old → new | role / example | arithmetic check |
|---|---|---|---|
| 679 | `$15.00` → `15,000₮` | frozen-card declined auth (US-5.3 S1) | standalone |
| 683 | `$200.00 ... $190.00` → `200,000₮ ... 190,000₮` | weekly spending limit / spent (US-5.3 S2) | remaining = 10,000 |
| 684 | `$25.00` → `25,000₮` | auth that exceeds remaining (polysemous $25 — NOT par) | 190,000+25,000=215,000 > 200,000 → declined ✓ |
| 686 | `$10.00` → `10,000₮` | boundary auth still approved | 190,000+10,000=200,000 = limit exactly ✓ |

### EP-6 — Lending & Loan Circles
**Confirmed loan bounds (DEC-45):**
| line | old → new | role |
|---|---|---|
| 707 | `min $100.00 / max $5,000.00 seed` (ADJUDICATED clause) → `min 100,000₮ / max 5,700,000₮ seed` | CURRENT DEC-45 loan bounds. The Sprint-1-draft `minimum $100.00, maximum $1,000.00` and the trailing `de-ratified $1,000.00 cap` on the SAME line were HELD (§2). |
| 735 | `$6,000.00 (above the $5,000.00 launch cap` → `6,840,000₮ (above the 5,700,000₮ launch cap` | above-cap validation example = 1.2 × 5,700,000 (recomputed, not scaled) + loan max |
| 736 | `"maximum loan amount is $5,000.00"` → `"maximum loan amount is 5,700,000₮"` | loan max in validation message |

**Illustrative loan / circle scenarios (×1000 everyday scale; all coupled arithmetic re-derived):**
| line | old → new | role / example | arithmetic check |
|---|---|---|---|
| 723 | `$500.00` → `500,000₮` | loan application amount (within [100,000; 5,700,000]) ✓ | drives disbursement L900 |
| 780 | `$1,000.00` → `1,000,000₮` | loan principal (US-6.3 payoff example) | couples to L820/826 |
| 807 | `$500.00` → `500,000₮` | guarantor available balance | |
| 808 | `$200.00` → `200,000₮` | pledge amount | |
| 809 | `$200.00 ... $300.00 ... $500.00` → `200,000₮ ... 300,000₮ ... 500,000₮` | pledge lock | 500,000−200,000=300,000 avail ✓ |
| 814 | `$150.00` → `150,000₮` | Member C available | |
| 815 | `$200.00` → `200,000₮` | attempted pledge | 200,000 > 150,000 → rejected ✓ |
| 816 | `$150.00` → `150,000₮` | rejection message balance | |
| 820 | `$1,000.00 ... $600.00 (60% coverage)` → `1,000,000₮ ... 600,000₮` | coverage tier | 600,000/1,000,000 = 60% ✓ |
| 822 | `$600.00` → `600,000₮` | circle contribution to rate | |
| 823 | `$200.00` → `200,000₮` | revoked pledge → reprices 40% | (600,000−200,000)/1,000,000 = 40% ✓ |
| 826 | `$200.00 ... 20% of the $1,000.00 principal` → `200,000₮ ... 1,000,000₮` | pledge coverage | 200,000/1,000,000 = 20% ✓ |
| 827 | `$300.00` → `300,000₮` | principal repayment | |
| 828 | `$60.00 (20% × $300.00) to $140.00` → `60,000₮ (20% × 300,000₮) to 140,000₮` | pro-rata lock release | 20%×300,000=60,000; 200,000−60,000=140,000 ✓ |
| 832 | `$500.00` → `500,000₮` | defaulted principal outstanding | |
| 840 | `$50.00/month` → `50,000₮/month` | ROSCA contribution (§K) | |
| 843 | `$200.00` → `200,000₮` | ROSCA payout | 50,000×4 = 200,000 ✓ |
| 848 | `$50.00 ... (4 × $50.00) ... $200.00` → `50,000₮ ... (4 × 50,000₮) ... 200,000₮` | ROSCA debit + payout | 4×50,000 = 200,000 ✓ |
| 852 | `$10.00` → `10,000₮` | Member B insufficient balance | 10,000 < 50,000 ✓ |
| 853 | `$50.00` → `50,000₮` | failed ROSCA debit | |
| 867 | `$200.00 ... $200.00` → `200,000₮ ... 200,000₮` | ROSCA reconciliation | each paid 200,000 in / one 200,000 payout ✓ |
| 900 | `$500.00` → `500,000₮` | loan disbursement (= L723 application) ✓ | |
| 911 | `$300.00` → `300,000₮` | payoff principal outstanding | |
| 924 | `$100.00` → `100,000₮` | extra payment (polysemous $100 — NOT loan-min; a repayment) | |
| 925 | `$100.00` → `100,000₮` | idempotent single post | matches L924 |

### EP-7 — Dividends & Surplus Distribution
| line | old → new | role / example | note |
|---|---|---|---|
| 966 | `$0.00` → `0₮` | zero-patronage entitlement statement | zero → zero |
| 967 | `one $25.00 share` → `one 10,000₮ share` | par (current share value, in prose). Provisional note already placed document-wide at L188 by T3a → plain value used here. | par 10,000₮ |
| 972 | `$600,000.00` → `600,000,000₮` | §A distributable pool (×1000) | |
| 975 | `Σ entitlements = $600,000.00` → `600,000,000₮` | reconciliation total = pool | |
| 978 | `$84.60` → `84,600₮` | §A Member A entitlement (×1000; straight cash entitlement here, NOT decomposed into shares in this doc) | |
| 990 | `Σ = $599,999.87 against a $600,000.00 pool` → `599,999,870₮ against a 600,000,000₮ pool` | deliberate reconciliation-defect fixture | 600,000,000−599,999,870 = 130₮ residual (×1000 of the original 13-minor-unit gap) ✓ |
| 1006 | `$84.60` → `84,600₮` | entitlement posts to savings | matches L978 |
| 1034 | `~$1.20` → `~1,200₮` | illustrative estimator delta (×1000) | standalone |
| 1040 | `$0.00` → `0₮` | "not a result" empty state | zero → zero |
| 1043 | `$0.00` → `0₮` | zero/negative forecast surplus | |
| 1045 | `$0.00` → `0₮` | projection displays zero | |
| 1051 | `near-$0.00` → `near-0₮` | brand-new member estimate | |
| 1056 | `$84.60` → `84,600₮` | annual statement received amount | matches L978/L1006 |

---

## 2. TOKENS DELIBERATELY HELD (unchanged — which held-set + why)

| line | token(s) | held-set | reason |
|---|---|---|---|
| 640 | `$12.40` (card purchase) | Held-set 3 (round-up, DEFERRED by PO) | This is US-5.1 Scenario 4, an explicit Round-Up demonstration ("Round-Ups are enabled ... Round-Up capture engine computes $0.60"). No confirmed ₮ round-up denomination exists; the purchase is the coupled operand that generates the held round-up, so it is held with it to keep the example coherent. |
| 643 | `$0.60` (round-up amount) | Held-set 3 (round-up) | Directly a `$X.YY`-style round-up example ($13.00 − $12.40). Deferred; no ₮ denomination. |
| 707 | `minimum $100.00, maximum $1,000.00` (Sprint-1 draft) AND `de-ratified $1,000.00 cap` | Held-set 6 (superseded / de-ratified prose) | Prose DESCRIBING a rejected past decision. The line explicitly says this Sprint-1 pair was "de-ratified"; `$1,000.00 de-ratified loan cap` is named verbatim in held-set 6. Follows the T3a L193 precedent (superseded drafts held; current value on the same line changed). **NOTE (flag):** the draft min $100.00 numerically equals the confirmed loan-min (100,000₮ post-migration). Held as historical draft text, but a reviewer may prefer to align it for reader clarity — see §3. |
| 904 | `$88.20 monthly installment` | Held-set 4 (BLOCKED — rate model) | Loan installment blocked on DEC-48/49/52 amortization; recompute only when the rate model is fixed. Left USD per explicit task instruction. |
| 931 | `$88.20 installment` | Held-set 4 (BLOCKED — rate model) | Same installment, arrears scenario. Held. |
| 931 | `$40.00` (account balance) | Coupled to Held-set 4 | The scenario is "installment $88.20 due, account holds $40.00" → shortfall. Re-deriving $40 to 40,000₮ while $88.20 stays USD would break the shortfall comparison (40,000₮ vs $88.20 is incoherent). Held with the blocked installment; re-derive together once the rate model unblocks. Flagged in §3. |

No KPI-cluster, persona-income, or DEC-65/DEC-63 program-cap tokens exist in the EP-5..EP-7 range
(those held sets live in doc 01/05, EP-9, EP-12). No token in range had an UNDETERMINABLE role.

---

## 3. FLAGGED FOR REVIEWER / PO (role clear; treatment is a decision beyond amount-apply)

1. **Unanchored illustratives re-derived at ×1000 everyday scale (needs PO confirmation).** Every
   card/loan/ROSCA/dividend scenario balance that is NOT anchored to a confirmed limit (EP-5 auths,
   EP-6 loan/pledge/ROSCA operands, EP-7 pool + $84.60 entitlement + $1.20 estimator) was
   re-denominated at the same consistent ×1000 scale that merged T3a used for EP-1..EP-4, chosen so
   every intra-scenario relationship holds exactly (verified per row in §1), all values are whole
   tugrik, and magnitudes are realistic for Mongolian life (500,000₮ personal loan, 50,000₮/month
   ROSCA, 600,000,000₮ ≈ MNT 600m cooperative surplus pool). **These illustrative operands are a
   re-derivation choice, not confirmed PO values.** No coupled operand was scaled in isolation. Same
   PO-confirmation flag T3a raised for EP-1..EP-4.

2. **Line 707 Sprint-1-draft min $100.00 held as historical text.** The draft loan-min happens to
   equal the confirmed loan-min (100,000₮). Held per held-set 6 (it is de-ratified draft prose),
   consistent with the T3a L193 precedent, but a reviewer wanting the historical narrative to read
   cleanly against the migrated adjudicated bound may relocate/annotate. Decision, not a bug.

3. **$88.20 loan installment + coupled $40.00 (L904, L931) BLOCKED.** Held per held-set 4 (rate
   model DEC-48/49/52). Consequence: US-6.7/6.8 scenarios now mix a ₮ principal (500,000₮ disbursed,
   L900) with a still-USD installment ($88.20). This cross-scenario inconsistency is inherent to the
   block and expected — the installment cannot be computed until the amortization convention is
   fixed. When unblocked, recompute the installment via amortization over the re-derived principal
   and re-derive the coupled $40.00 balance together (do NOT digit-scale either).

---

## 4. Files changed
- `idea-lab/final_requirements/03_acceptance_criteria.md` — EP-5..EP-7 only (edited lines 679–1056;
  EP-1..EP-4 ≤603 and EP-8+ ≥1080 untouched). Header block and all DEC-/US-/EP-/CAP- IDs intact.
- `.softhouse/handoff/20260724-currency-apply/T3b.md` — this handoff.

## 5. Verification status
- `.softhouse/verify-docs.sh` → PASS, HARD 0, USD DRIFT 140 [VERIFIED].
- All intra-scenario arithmetic re-checked per §1 [VERIFIED].
- 58 tokens changed / 5 held sets in range accounted for [VERIFIED].
