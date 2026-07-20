---
name: softhouse-uat
description: Verifies the Digital Coop Bank requirements baseline against its documented invariants by running .softhouse/verify-docs.sh — HARD checks that must be zero and DRIFT counts that must not increase during the Mongolia migration. Use when the user runs /softhouse-uat, asks to run UAT or acceptance checks, or wants to confirm a requirements change did not regress the baseline.
---

# /softhouse-uat — requirements verification (project variant)

**Project-scoped; overrides the global `softhouse-uat` inside this repository.**

The generic skill verifies a running system: health endpoints, smoke URLs, an isolated test stack. **None of that exists here** — this repository contains no application, no service, no database, and no test suite. Running the generic skill would fall through to its fallback and find nothing.

Here, UAT means: **do the requirements documents still satisfy the non-negotiables in `CLAUDE.md`?**

## Usage
- `/softhouse-uat` — run all checks
- `/softhouse-uat hard` — HARD checks only
- `/softhouse-uat drift` — DRIFT checks only
- `/softhouse-uat --baseline` — deliberately re-baseline DRIFT counts (requires a stated reason)

## What it runs

```bash
.softhouse/verify-docs.sh
```

Exit 0 = PASS, 1 = FAIL, 2 = could not run.

### HARD checks — must be zero

| Check | Why |
|---|---|
| US deposit-insurance regime (FDIC/NCUA) | Wrong jurisdiction. Mongolian SCC deposits are **not** insured at all; the Deposit Insurance Law covers banks only. |
| Stale MNT 3m RTGS threshold | Mongolbank's English page says 3m; the **Mongolian page says 5m and is authoritative**. The wrong figure would route payments incorrectly. |
| `first_name` / `last_name` | Mongolian names are three parts — ovog, patronymic, given name. A two-field model cannot represent them, and the patronymic occupies the passport surname slot. |
| float / double-precision / `DECIMAL(p,s)` money types | Money is integer minor units. Any float in a money path is a correctness defect. |
| Hardcoded UTC+8 | Two zones: `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07, ~5–6% of the population). |

A HARD hit is a failure regardless of context. If a hit is a genuine false positive, **fix the checker's pattern** — do not add an exception to make a failure disappear.

### DRIFT checks — must not increase

USD amounts, US payment rails, US vendor references. These are non-zero today by design: the baseline was written for a US market and the Mongolia migration is in progress. The contract is that they **go down, never up**. Baseline counts live in `.softhouse/baseline.txt`.

## Steps

1. **Pre-flight** — confirm `idea-lab/final_requirements/*.md` exists. Nothing to deploy, nothing to start; if a caller asks to bring a system up, tell them there isn't one.
2. **Run** the script (or the requested subset).
3. **Report** — per-check pass/fail with counts, and for DRIFT the delta against baseline. Overall verdict PASS or FAIL.
4. **On failure** — name the specific documents and lines. `grep -rn '<pattern>' idea-lab/final_requirements/` locates them. Do not attempt an automatic fix; a HARD failure usually means a ratified `DEC-n` needs amending, which is a `user` decision.

## Re-baselining

Only after a deliberate migration step that legitimately changes the counts, and only with the reason recorded in the postmortem:

```bash
.softhouse/verify-docs.sh --baseline
```

**Never re-baseline to clear a failure.** A rising DRIFT count means a change reintroduced US-market assumptions — that is the check working.

## Current state (2026-07-20)

Two HARD checks fail against real, verified defects — both are pre-existing baseline problems, not regressions:

- **FDIC/NCUA (2 hits)** — `04_technical_architecture.md` §1.2 describes the sponsor bank as "an FDIC/NCUA-insured partner institution".
- **`first_name`/`last_name` (31 hits)** — DEC-6 in `01_business_analysis.md` ratifies a two-part name model.

Both need a `DEC-n` amendment, so both are `executor: "user"` decisions. Until they are fixed, `/softhouse-uat` returns FAIL — correctly. Treat the current verdict as a known-failing baseline, not as a broken checker.

## Limits — read before trusting a PASS

This checker greps text. It verifies that certain wrong things are **absent**; it cannot verify that the right things are **present or correct**. It will not catch a contradiction between two documents, an arithmetic error, a fabricated citation, or an invented threshold. Those are what the independent `reviewer` role in `/softhouse` is for. **A PASS here means "no known-bad patterns found", not "the change is right".**
