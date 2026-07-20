# UAT config — Digital Coop Bank

**There is no system under test.** This repository contains requirements documents and a
requirements-generation script — no application, no service, no database, no test suite.

UAT here means: do the documents still satisfy the non-negotiables in `CLAUDE.md`?

## Pre-flight

- `test -d idea-lab/final_requirements` — the baseline must exist.
- Nothing to deploy, start, or health-check. If asked to bring a system up, there isn't one.

## Deploy / refresh

Not applicable. Nothing is deployed.

Note: `idea-lab/run_pipeline.py` is the only executable code. It shells out to the external
`agy` binary, **spends real LLM budget**, and mutates `pipeline_state.json`.
It is **orchestrator-only** and is never part of verification.

## Suites

- **all** (default): `.softhouse/verify-docs.sh`
- **hard**: HARD checks only — must be zero
- **drift**: DRIFT checks only — must not exceed `.softhouse/baseline.txt`

## Pass criteria

- Every HARD check reports 0.
- Every DRIFT check is at or below its baseline.
- Exit 0.

## Evidence

Console output. Baseline counts in `.softhouse/baseline.txt`, which is committed so drift is
reviewable in git history.

## Known-failing baseline (2026-07-20)

Two HARD checks fail against real pre-existing defects, both requiring a `DEC-n` amendment
and therefore a product-owner decision:

- FDIC/NCUA references — `04_technical_architecture.md` §1.2
- `first_name`/`last_name` — DEC-6, `01_business_analysis.md`

Do not silence these. FAIL is the correct verdict until the decisions are made.

## What this does not verify

Text patterns only. It cannot detect cross-document contradictions, arithmetic errors,
fabricated citations, or invented thresholds — the defect classes this project has actually
suffered. Those are the independent `reviewer` role's job in `/softhouse`.
A PASS means "no known-bad patterns", not "correct".
