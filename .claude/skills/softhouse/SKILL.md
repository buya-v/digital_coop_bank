---
name: softhouse
description: Digital Coop Bank project pipeline — plans a requirements change into a task graph, executes it with parallel isolated worktree agents, reviews every branch with an INDEPENDENT reviewer agent, verifies document invariants, then merges and records learned patterns. Use when the user runs /softhouse, asks to run the softhouse pipeline, or wants a multi-step requirements change planned and executed end-to-end. "/softhouse resume" continues an interrupted run.
---

# /softhouse — Digital Coop Bank pipeline (project variant)

**This is the project-scoped variant and it overrides the global `softhouse` skill inside this repository.** Do not edit the global one. The pipeline shape (9 steps, `tasks.json` schema, executor routing, resumability) is unchanged and compatible; what differs is that **this project's deliverables are requirements documents, not code.**

Adaptations, and why each exists:

| Change | Reason |
|---|---|
| Document roles (`analyst`, `spec_writer`, `verifier`) replace `coder`/`test_writer` as the default | There is no application code in this repo. Nothing to compile, no test suite. |
| **Review is performed by an independent `reviewer` agent, not the orchestrator** | The generic pipeline has the session that wrote the plan judge whether the plan was executed. That failure mode has already cost this project two rounds: `06_ledger_addendum.md` passed its author's own testing twice, and each round's fixes introduced new critical defects. |
| UAT = `.softhouse/verify-docs.sh` | There is no live system to smoke-test. Verification means the documents still satisfy the non-negotiables. |
| Push is retained | `origin` = `git@github.com:buya-v/digital_coop_bank.git`, `main` tracks `origin/main`. The generic pipeline's push steps apply unchanged. |
| Design stage inactive | No UI exists and no UI paradigm has been chosen. Do not invent one. |

## Usage
- `/softhouse <requirement>` — plan and execute a full run
- `/softhouse resume` — resume an interrupted run

## STEP 0 — Pre-flight
1. `git status` — abort if the tree is dirty. **Exception:** on `resume`, a tree dirty *only* under `.softhouse/` is expected (an interrupted run leaves partial state) and does not abort.
2. Read `CLAUDE.md` — it carries the non-negotiables, the blocking legal questions, and the market context. Planning without it will produce US-shaped tasks.
3. Read `.softhouse/patterns.md`.
4. Read `.softhouse/tasks.json`; read the newest `.softhouse/runs/*.json` and pull its `backlog` into planning input.
5. Environment facts for this project are fixed and already known — do not re-derive them:
   - **No live deployment. No server, no database, no container stack, no test suite.**
   - **Remote exists:** `origin` = `git@github.com:buya-v/digital_coop_bank.git`; `main` tracks `origin/main`. Push steps apply. Only the orchestrator pushes — workers commit to their branch.
   - The only executable code is `idea-lab/run_pipeline.py`. Running `next` / `redo` / `retro` **spends real LLM budget via the external `agy` binary and mutates `pipeline_state.json`** → always `executor: "orchestrator"`, never a worker agent.

## STEP 1 — Mode
`resume` → STEP 4. Otherwise treat the argument as the requirement → STEP 2.

## STEP 2 — Plan

Task schema is identical to the global skill:

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

### Roles

**Active now:**
- `analyst` — researches or derives a change (market, legal, regulatory). Must cite sources and mark confidence. **May not state a figure it did not verify** — see the honesty rule below.
- `spec_writer` — writes or edits a requirements document. Must preserve the document's header block, ID conventions (`DEC-n`, `US-n.n`, `EP-n`, `CAP-n`, `F-nnn`, `E-n`), and traceability.
- `reviewer` — **independent adversarial review of another task's output.** Spawned fresh, without the planning context. Default `model: "opus"`.
- `verifier` — runs `.softhouse/verify-docs.sh` and reports.

**Inactive until an application exists** — do not plan these; if a requirement seems to need one, stop and say so: `coder`, `test_writer`, `designer`, `cx_reviewer`.

### Executor routing (safety boundary, not a label)

- `"agent"` — document work, repo-contained, verifiable by re-reading the diff. Default.
- `"orchestrator"` — anything running `run_pipeline.py` (spends budget, mutates state), any git operation, any external fetch.
- `"user"` — decisions only the product owner can make. **In this project that includes all five blocking questions in `CLAUDE.md`** (common bond, biometric eKYC, data localisation, tax characterisation, e-vote quorum) plus any scope change to a ratified `DEC-n`.

### Planning rules

- Overlapping `files_hint` **must** be serialised via `dependencies`. The six `final_requirements/` documents cross-reference heavily — two agents editing `01` and `05` concurrently will produce contradictory `DEC-n` state.
- **Every `analyst` or `spec_writer` task gets a paired `reviewer` task that depends on it.** No document change lands unreviewed.
- **Never plan a task that edits `requirements_output/sprint_*/`** — superseded drafts, read-only history.
- **Never plan implementation from `06_ledger_addendum.md`** — it carries five confirmed critical defects including an inverted available-balance formula. Changes *to* it are fine; building *from* it is not.
- A task that would touch EP-5 (Cards), EP-10 (Round-Ups), or EP-6 (Lending) must first surface an `executor: "user"` task, because their lawfulness under an SCC licence is unresolved.
- Read `.softhouse/patterns.md` before finalising.
- `model`: `spec_writer`/`analyst` → `sonnet`; `reviewer` → `opus`; `haiku` for mechanical edits (renames, find-replace, formatting); `opus` for anything touching ledger mechanics, money arithmetic, or a ratified `DEC-n`.

### The honesty rule (project non-negotiable)

Every worker prompt must carry this, and review enforces it:

> State only what you verified. If you could not verify something, write that you could not — do not supply a plausible figure, citation, or mechanism to fill the gap. A gap marked "unverified" is a correct answer; a confident invention is a defect. Mark each material claim `[VERIFIED: <source>]` or `[UNVERIFIED]`.

This exists because this project has already lost work to exactly this: a research agent fabricated an e-money licensee list and had to retract it, and the ledger addendum's own author twice reported invented confidence in arithmetic that was wrong.

### After planning
1. Write `.softhouse/tasks.json` (`run_id`, `feature`, `requirement`, `status: "planning"`, `backlog: []`, `tasks: [...]`).
2. Print the task graph as a table: `| ID | Title | Role | Executor | Model | Target | Deps | Files |`.
3. **Wait for approval** — "Approve this plan? (yes/edit/abort)".
4. On approval: `git add .softhouse/tasks.json && git commit -m "softhouse: plan — <feature>" && git push`.

## STEP 3 — Execute

Process in dependency order, routed by `executor`. Orchestrator and user tasks run inline; agent tasks spawn workers.

**Before any batch:** commit **and push** main — workers must fork from current main, and a stale fork base makes their diffs look destructive.

Spawn with the **Agent tool**, `isolation: "worktree"`, `model: task.model`. A retry (`attempts > 0`) upgrades to `opus`.

**Every worker prompt begins with:**

> CRITICAL CONTEXT — this repository contains NO application code.
> - There is no live deployment, no database, no service, no test suite. Do not attempt to build, run, deploy, or test an application. If your task appears to require one, STOP and report that instead.
> - Do NOT run `idea-lab/run_pipeline.py`. It spends real LLM budget and mutates project state; it is orchestrator-only.
> - Do NOT `git push` from a worktree. Pushing is the orchestrator's job; you commit to your branch only.
> - You are in an ISOLATED GIT WORKTREE forked from current main. Create branch `softhouse/<taskid>-<slug>`, commit to it, never touch main.
> - Read `CLAUDE.md` first. Its non-negotiables are graded in review; violating one is a rejection.
> - Write your handoff to `.softhouse/handoff/{run_id}/{task.id}.md` **and commit it to your branch** (`git add -f` is not needed — the directory is deliberately tracked). This is not optional even for draft-only tasks that change no other file: the reviewer runs in a DIFFERENT worktree and reads your handoff from git. A branch with no commit is treated as unchanged, its worktree is auto-pruned, and your entire output is destroyed. Both level-0 tasks of run 20260720-161202 were lost this way.
> - {the honesty rule, verbatim}
> - End your final message with the literal line `no code executed`.

**`spec_writer` / `analyst` additionally receive:**
> - Edit only the files in `files_hint`. Preserve the document header block and existing ID conventions.
> - If your change contradicts a ratified `DEC-n`, STOP and report — amending a decision is a `user` task, not yours.
> - If you introduce a new term, enum value, or threshold, add it to the document's glossary or decision table; do not leave it floating.
> - Run `.softhouse/verify-docs.sh` before finishing. It must not regress.
> - Handoff sections: `## Changes Made` / `## Decisions` / `## Sources` / `## Unverified` / `## Blockers` / `## Follow-ups`.

**`reviewer` agents receive** (spawned fresh — do **not** pass the planning rationale, or you reproduce the self-review problem):
> You are an INDEPENDENT reviewer. You did not plan this work and must not assume it is correct. Assume defects exist.
> - Read `CLAUDE.md` and `.softhouse/patterns.md` from your own worktree.
> - **Read the upstream handoff from the BRANCH, not from your working tree** — the branch under review is not merged yet, so the file does not exist on disk for you:
>   `git show <branch>:.softhouse/handoff/{run_id}/{dep_task.id}.md`
>   Worktrees share the repository's object store, so this works from any worktree. Reading the path directly returns "No such file" and is the single most likely way to review nothing and report APPROVED.
> - Read the diff with `git diff main...<branch>` (three dots — diff against the merge base). Two dots will render every commit `main` gained since the branch forked as a deletion by the branch, which looks alarming and is an artifact.
> - Check: (1) every non-negotiable in CLAUDE.md; (2) no ratified `DEC-n` silently changed; (3) every `[VERIFIED]` claim actually traces to its cited source; (4) every number that can be checked, checked — arithmetic, totals, invariants; (5) internal consistency with the other `final_requirements/` documents; (6) `.softhouse/verify-docs.sh` does not regress.
> - Report each finding as: severity / location / what is wrong / the correct fix.
> - Verdict: APPROVED, MICRO-FIX (≤10 lines, mechanical only), or REJECTED with specifics.
> - If you find nothing, say so plainly — but state what you checked, so silence is distinguishable from not looking.

## STEP 4 — Resume
Read `tasks.json`; find tasks not `done`/`approved`; check `.softhouse/handoff/{run_id}/` for partials; resume at the earliest incomplete dependency level.

## STEP 5 — Review
1. **Scope check** — `git diff --stat main..<branch>` vs `files_hint`.
2. **Fork-freshness** — `git merge-base main <branch>`; if behind, scrutinise co-edited files. A three-way merge preserves disjoint files but not co-edited ones.
3. **Read the independent reviewer's handoff.** The orchestrator's job here is to adjudicate the reviewer's findings, **not** to substitute its own judgment for the review.
4. **Non-negotiables grep** against `CLAUDE.md` and `patterns.md`.
5. Verdict: **APPROVED** / **MICRO-FIX** (mechanical only — never logic, never a number) / **REJECTED** (one retry, model → opus, reviewer notes injected).

## STEP 5.5 — Verification
Run `.softhouse/verify-docs.sh` against merged state.
- HARD checks must be zero.
- DRIFT checks must not increase against `.softhouse/baseline.txt`.
- To re-baseline deliberately after a migration step: `.softhouse/verify-docs.sh --baseline`, and say so in the postmortem.

Gate: must PASS before the run completes. Failure marks the responsible task `uat_failed` — one retry, model → opus.

## STEP 6 — Merge
`git merge --no-ff <branch>` in dependency order. On conflict: abort that merge, mark `conflict`, report, continue with independent tasks. Re-run the verifier and **push after each merge batch**.

## STEP 7 — Integration
Run `.softhouse/verify-docs.sh` on final merged main. Additionally re-read any document another merged task cross-references, since cross-document contradictions are this project's characteristic failure — they are what `final_requirements/` was created to resolve.

## STEP 8 — PostMortem
Append between the markers in `.softhouse/patterns.md`:

```markdown
### Run {run_id} — {feature} ({date})
- **What worked**:
- **What the independent reviewer caught**:   (the value of this step is measurable — record it)
- **Claims marked UNVERIFIED**:               (carried forward as open questions, not silently dropped)
- **New knowledge**:
- **Planning advice**:
- **Verifier**: HARD n/n · DRIFT deltas · re-baselined? why
- **Backlog carried forward**:
```

## STEP 9 — Cleanup
1. Archive `tasks.json` → `.softhouse/runs/{run_id}.json` (preserves `backlog`).
2. Reset `tasks.json` to idle.
3. Worktree/branch hygiene: `git worktree remove` + `prune`; delete merged `softhouse/*` branches; list unmerged ones rather than deleting.
4. `git add .softhouse/ && git commit -m "softhouse: complete — {feature}" && git push`.
5. Report: tasks by executor, reviewer findings, verifier state, backlog, patterns learned.

## Error handling
- Catastrophic agent failure → mark `failed`, continue independent tasks, and **mark every dependent task `blocked`** with the blocking id in `note`. Do not leave dependents silently unrunnable.
- >50% of tasks failed → abort and report.
- All state in `.softhouse/tasks.json`; any interruption resumes with `/softhouse resume`.
