---
name: softhouse-plan
description: Planning-only phase of the Digital Coop Bank pipeline — breaks a requirements change into a reviewable task graph with executor routing, paired independent reviewers, and dependencies, writes it to .softhouse/tasks.json, and stops. Never spawns worker agents or edits requirements documents. Use when the user runs /softhouse-plan or wants to review a plan before executing it with /softhouse resume.
---

# /softhouse-plan — plan only (project variant)

**Project-scoped; overrides the global `softhouse-plan` inside this repository.** Planning rules are IDENTICAL to this project's `/softhouse` STEP 2 — a plan written here must execute unmodified under `/softhouse resume`.

This command never spawns workers and never edits a requirements document. It only reads.

## Usage
- `/softhouse-plan <requirement>` — generate a task plan

## STEP 0 — Pre-flight
1. `git status` — abort if dirty.
2. Read `CLAUDE.md`. **Planning without it produces US-shaped tasks** — it carries the Mongolia correction, the non-negotiables, and the five blocking legal questions.
3. Read `.softhouse/patterns.md`.
4. Read `.softhouse/tasks.json`. If a run is in progress, warn. If the previous run is terminal, archive it to `.softhouse/runs/` before replacing.
5. Read the newest `.softhouse/runs/*.json` and pull its `backlog` into planning input.
6. Environment facts are fixed — do not re-derive: **no application code, no live system, no test suite.** `origin` exists and `main` tracks `origin/main`, so push steps apply. `idea-lab/run_pipeline.py` spends real LLM budget and is orchestrator-only.

## STEP 1 — Mode
Always plans. If a run is in progress, ask whether to replace or abort.

## STEP 2 — Plan

Schema:

```json
{
  "id": "T1",
  "title": "Short title",
  "description": "What to change, in which file, and the acceptance criteria",
  "agent_role": "spec_writer",
  "executor": "agent",
  "model": "sonnet",
  "target": "requirements",
  "files_hint": ["idea-lab/final_requirements/01_business_analysis.md"],
  "dependencies": [],
  "status": "pending",
  "attempts": 0,
  "note": ""
}
```

**Roles — active:** `analyst` (research/derive, must cite and mark confidence), `spec_writer` (write/edit a document), `reviewer` (independent adversarial review, `opus`), `verifier` (runs `.softhouse/verify-docs.sh`).

**Roles — inactive until an application exists:** `coder`, `test_writer`, `designer`, `cx_reviewer`. Do not plan these. If the requirement seems to need one, stop and say so rather than planning around it.

**Executor routing:**
- `"agent"` — repo-contained document work. Default.
- `"orchestrator"` — anything running `run_pipeline.py`, any git operation, any external fetch.
- `"user"` — product-owner decisions. **Includes all five blocking questions in `CLAUDE.md`** and any change to a ratified `DEC-n`.

**Rules:**
- Overlapping `files_hint` **must** be serialised. The six `final_requirements/` documents cross-reference heavily; concurrent edits to `01` and `05` produce contradictory `DEC-n` state.
- **Every `analyst`/`spec_writer` task gets a paired `reviewer` task depending on it.** This is not optional — the project has twice shipped defects that its own author's review missed.
- Never plan edits to `requirements_output/sprint_*/` — superseded, read-only.
- Never plan implementation from `06_ledger_addendum.md` (five confirmed critical defects). Editing it is fine.
- Any task touching EP-5 (Cards), EP-10 (Round-Ups) or EP-6 (Lending) must be preceded by a `user` task — their lawfulness under an SCC licence is unresolved.
- Apply `.softhouse/patterns.md`.
- `model`: `spec_writer`/`analyst` → `sonnet`; `reviewer` → `opus`; `haiku` for mechanical edits; `opus` for ledger mechanics, money arithmetic, or a ratified `DEC-n`.

**Scale check before you finalise:** `03_acceptance_criteria.md` is 140 KB and `04_technical_architecture.md` is 126 KB. A task whose `files_hint` spans several whole documents will exhaust its worker's context. Split by document, or by section within a document.

## After planning
1. Write `.softhouse/tasks.json` with `run_id`, `feature`, `requirement`, `status: "planning"`, `backlog: []`, `tasks`.
2. Print the table: `| ID | Title | Role | Executor | Model | Target | Deps | Files |`.
3. Show the dependency/parallelism structure, and call out every `orchestrator` and `user` task — the `user` ones are decision gates that will block their dependents.
4. `git add .softhouse/tasks.json && git commit -m "softhouse: plan — <feature>" && git push`.

## Output
> Plan saved to `.softhouse/tasks.json`. Review the task graph above.
> To execute: `/softhouse resume`
> To re-plan: `/softhouse-plan <updated requirement>`

## Notes
- Never spawns workers; never edits requirements documents.
- Safe to re-run — each run replaces the previous plan; prior runs live in `.softhouse/runs/` and git history.
