# Digital Coop Bank — project context

## What this is

A requirements baseline for a digital cooperative banking platform. **Primary market: Mongolia.**

**The application is at the SCAFFOLD stage.** As of 2026-07-22 a backend skeleton exists at `backend/` — FastAPI + Postgres, a `/health` and `/ready` endpoint, and the money non-negotiable encoded and tested (`backend/app/money.py`). **No feature endpoints exist yet** — no member, account, ledger, payment or governance routes. The OpenAPI contract and the ORM schema (derived from `04_technical_architecture.md`) are not built. Stack decision: `docs/adr/0001-technology-stack.md`.

An agent asked to build a FEATURE (an endpoint, a table, a flow) should confirm the OpenAPI contract and schema for it exist first, and that the epic is not entity-gated (Cards/EP-5, Round-Ups/EP-10, Lending/EP-6 are unlawful-until-the-entity-decision — do not build them). Health/scaffold work is fine; feature work needs its contract and its legal clearance.

## Repository layout

```
idea-lab/
  run_pipeline.py            # LLM agent pipeline (requirements generation), CLI: init/next/redo/retro/status
  agent_prompts.py           # system prompts for the 7 pipeline roles
  pipeline_state.json        # pipeline state (sprint 4, phase 0)
  requirements_output/       # sprint_1..3 raw role outputs — SUPERSEDED DRAFTS, do not build from these
  final_requirements/        # the reconciled baseline (00..05) + 06 ledger addendum
```

### `final_requirements/` is the baseline; `requirements_output/` is not

`final_requirements/00..05` is an independently written reconciliation that supersedes the sprint drafts. It resolved real contradictions across them (three different share prices, two loan-pricing models, conflicting enums) and documents what it dropped. Verbatim overlap with the sprint files is effectively zero.

**Nothing in `run_pipeline.py` produces `final_requirements/`.** Its provenance is not recorded in this repo. It cannot currently be regenerated.

## Current status: the baseline is US-designed and the market is Mongolia

The baseline was written against a US/EU market. That assumption is wrong, and the correction is not cosmetic.

**Invalidated by the market change:**

- **Currency** — DEC-18 fixes USD. Should be MNT (ISO 4217 numeric 496, minor unit 2). 78 distinct USD amounts across the docs need re-denominating *and* re-justifying against Mongolian incomes.
- **Payment rails** — ACH / FedNow / SEPA / wire do not exist here. Mongolia has RTGS (**Банксүлжээ / Banksuljee**) above **MNT 5,000,000**, and **ACH+** at or below it, 24/7. Cards clear through **NETC**, a Bank of Mongolia entity. Threshold is set by Governor's order → treat as configuration, never hard-coded. (Mongolbank's *English* page says MNT 3m; the Mongolian page says 5m and is authoritative.)
- **Vendors** — Stripe, Plaid, Lithic, Persona are all assumed and are not the Mongolian market. Note `04` leaks vendor names into the schema (`persona_inquiry_id`, `plaid_item_ref`) and API error codes (`502 PLAID_UNAVAILABLE`), so the docs' claim that vendor substitution is "an integration change, not a requirements change" is false.
- **Regulator** — FDIC/NCUA → **FRC** (Financial Regulatory Commission) for cooperatives; **Bank of Mongolia** for banks and all payment/e-money licensing.
- **Language** — the entire baseline is English. Mongolia ranks 95/123 on EF EPI ("Very Low"). Product must ship in **Cyrillic Mongolian**. Do **not** build a traditional Mongol bichig UI — measured: zero U+1800–18AF codepoints across all seven major Mongolian bank and government sites.

**Market facts that change the product thesis:**

- Account ownership is **98.3%** (World Bank Findex 2024) — there is no "underbanked" gap. Rural ownership (98.8%) exceeds urban.
- Borrowing is **68.3%**, roughly twice the peer average; saving is **47.9%**. The market is over-credited and under-saved.
- Khan Bank has **2.9m customers (82% of the population)**, 99.4% of transactions digital, and a 58-mini-app super-app. "Neobank parity" is not a differentiator here.
- The SCC sector totals **172 cooperatives / 78,608 members / MNT 390bn** — the baseline's KPI of 100,000 members exceeds the entire sector.

## Non-negotiables

Grep diffs against these. Violating one is a rejection, not a discussion.

- **Money is integer minor units.** No floating-point type in any monetary code path, schema column, API field, or test fixture — including intermediate calculation. Display 0 decimals (local practice is `1,250,000₮`, postfix); store 2 (ISO).
- **The ledger is double-entry and append-only.** Balances are derived, never directly written. Corrections are reversing entries. Holds are postings, never mutable flags.
- **`Idempotency-Key` is mandatory on every money-movement POST.**
- **Never describe member savings as insured, protected, or guaranteed.** SCC deposits are **not** covered — the Law on Insurance of Bank Deposits covers banks only, and SCC Law Art. 55.1's promise of insurance is an unimplemented cross-reference. Misrepresentation carries criminal exposure under Art. 30.2.
- **Names are three fields, not two** — ovog (clan), patronymic, given name. Never `first_name`/`last_name`. The patronymic occupies the passport surname slot; siblings share one, a parent and child never do.
- **National ID is 10 *characters*** — 2 Cyrillic letters + 8 digits. Month field carries **+20 for births from 2000 onward**. The check-digit algorithm is unpublished — validate structurally, never with a guessed formula.
- **Two time zones, no DST** — `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07, ~5–6% of the population). Never hardcode an offset.
- **Dates are `y.MM.dd`, week starts Monday, 24-hour clock.**

## Blocking questions — do not plan build work past these

All require a Mongolian lawyer. None can be resolved by further research.

1. **Common bond (SCC Law Art. 19.3)** — members must share an employer, association, or aimag/district. A nationwide open-membership app may not be a lawful SCC. This bounds the entire product.
2. **Biometric eKYC** — two law-firm sources read the Personal Data Protection Law as restricting biometric collection to enumerated *state* bodies, which would forbid face-match onboarding. But bank practice reportedly *is* face-match + liveness. Contradiction unresolved. The compliant alternative is ХУР/XYP state-register lookup.
3. **Data localisation** — the MDDIC Information Security Requirement (11 Sept 2023) may require servers in Mongolia accessible only from Mongolia. If literal, foreign public cloud is foreclosed for regulated workloads.
4. **Tax** — SCC distributions are capital-proportional, so they read as dividends at 10% withholding, with no apparent patronage deduction. Potential double taxation undermines the cooperative's economics.
5. **E-vote quorum** — electronic vote submission is valid (Art. 32.6, amended 12 Jan 2024), but whether an e-vote counts toward the Art. 32.1 quorum is undefined. Determines whether digital governance functions at all.

## Known defects in the baseline

- **`06_ledger_addendum.md` (Draft 2) carries five confirmed critical defects**, including an inverted hold formula that computes available balance as `balance + hold` instead of `balance − hold`. It has failed two adversarial reviews, each finding new critical errors inside the previous round's fixes. **Do not implement from it.** It needs a controller or core-banking engineer, not another LLM pass.
- **EP-5 (Cards) and EP-10 (Round-Ups) are likely unlawful for an SCC** — SCCs have no payment-service power and none appears on Bank of Mongolia's PSP register. Round-ups depend on card settlement events, so they fall with cards.
- **Lending should be deferred.** Four independent arguments: DEC-48's 12% APR is below the 17.45% bank-funded market rate; the FRC folded fintech credit into DTI limits on 29 Jan 2026; the market already borrows at 68.3%; and the SCC constraint set makes it hardest to deliver.
- **Story point scale is uncalibrated.** S/M/L/XL → 1/2/3/5 means the largest possible item is 5 points and the whole institution is 128. Two MVP stories admit in their own INVEST notes that they may each exceed a full sprint.

## Conventions

- Requirements documents are Markdown, numbered `NN_name.md`, each with a header block declaring Document ID, Status, and upstream sources of truth.
- Decisions are tracked as `DEC-n` in `01_business_analysis.md` §6 (DEC-1…20, normative) and `05_prd_and_roadmap.md` §3 (DEC-21…75).
- `01` §6 is normative for DEC-1…20; no other document may redefine those terms or values.
- Stories are `US-n.n`, epics `EP-n`, capabilities `CAP-n`, features `F-nnn`, entities `E-n`.

## Verification

There is no test suite, no build, and no deployable system. `/softhouse-uat` has nothing to run. Until an application exists, verification means: does the change contradict a non-negotiable above, a ratified `DEC-n`, or a blocking question?
