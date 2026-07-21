# Softhouse learned patterns — Digital Coop Bank

Softhouse reads this file during pre-flight and applies it when planning. Anything above the markers is hand-written project knowledge; everything between the markers is appended automatically by each run's postmortem.

## Project constraints

Rules a worker agent must not violate. These get grepped against diffs during review.

### Money and the ledger

- **No floating-point in any monetary path** — not in schema columns, not in API fields, not in test fixtures, not in intermediate calculation. Integer minor units only (MNT, ISO 4217 numeric 496, minor unit 2).
- **Balances are derived, never written.** Any diff that assigns to a balance column directly is a rejection.
- **The ledger is append-only.** Corrections are reversing entries. A diff that `UPDATE`s or deletes a posted ledger entry is a rejection.
- **Holds must not alter `balance`** — only `available_balance`. A hold that changes the posted balance is the exact defect that failed review twice.
- **`Idempotency-Key` is mandatory on every money-movement POST.** No exceptions for "internal" transfers.
- **Do not implement from `final_requirements/06_ledger_addendum.md`.** Draft 2 carries five confirmed critical defects, including an inverted available-balance formula. It has failed two adversarial reviews, each finding new critical errors introduced by the previous round's fixes. It needs a human controller before any code is written against it.

### Market and legal

- **Never render member savings as insured, protected, or guaranteed.** SCC deposits are not covered by Mongolian deposit insurance. Misrepresentation carries criminal exposure. This applies to UI copy, emails, notifications, and API-returned strings.
- **No US payment rails.** ACH, FedNow, SEPA, wire are not applicable. Mongolia: RTGS (Banksuljee) above MNT 5,000,000, ACH+ at or below, NETC for cards. The threshold is set by Governor's order — read it from configuration, never hard-code it.
- **No Stripe / Plaid / Lithic / Persona.** These are assumed throughout `04_technical_architecture.md` and are not the Mongolian market. Note they are leaked into schema field names and error codes; renaming those is a requirements change, not an integration change.
- **UI is Cyrillic Mongolian.** English is not a viable fallback (EF EPI 95/123, "Very Low"). Do not build a traditional Mongol bichig UI — zero adoption measured across all major Mongolian bank and government sites, no Android vertical writing mode, no bold weight in Noto Sans Mongolian.

### Data model

- **Names are three fields** — ovog, patronymic, given name. A diff introducing `first_name`/`last_name` is a rejection. Store Cyrillic as canonical; match on registration number, never on name.
- **National ID is 10 characters** (2 Cyrillic letters + 8 digits), not 10 digits. Numeric-only validation breaks on real IDs. The month field carries **+20 for births from 2000 onward** — omitting this rejects every applicant born after 1999. The check digit algorithm is unpublished: validate structurally, never with a guessed formula.
- **Post-2022 ID cards no longer print the registration number on the card face.** Any OCR flow that expects to read it there fails on current cards.
- **Two time zones, no DST.** `Asia/Ulaanbaatar` (+08) and `Asia/Hovd` (+07, three western aimags). Use the tz library; never hardcode an offset. DST has been toggled three times since 1983.
- **Formatting:** dates `y.MM.dd`, week starts Monday, 24-hour clock. Currency displays postfix with zero decimals (`1,250,000₮`) but stores 2 decimals.

### Scope

- **EP-5 (Cards) and EP-10 (Round-Ups) are likely unlawful for an SCC.** Do not plan build work on them until the entity question is settled.
- **Lending is deferred.** Do not plan EP-6 work.
- **Do not treat `requirements_output/sprint_*/` as a source.** Those are superseded drafts with known contradictions. `final_requirements/` is the baseline.

## Environment topology

This is what makes `executor` routing correct.

- **Live deployment on this host: NO.** There is no application, no server, no database, no container stack. Nothing in this repository runs.
- **No test suite** — there is no application to test. Verification is instead `.softhouse/verify-docs.sh`, declared in `.softhouse/uat.md`: HARD checks that must be zero, DRIFT counts that must not rise against `.softhouse/baseline.txt`. It greps text, so it proves the absence of known-bad patterns — never correctness. Cross-document contradictions and arithmetic errors are the independent `reviewer` role's job.
- **The only executable code** is `idea-lab/run_pipeline.py`, a CLI that shells out to an external `agy` binary and writes Markdown. It has no tests. Running `next`, `redo` or `retro` **spends real LLM budget and mutates `pipeline_state.json`** — treat as `executor: orchestrator`, never hand it to a worker agent.
- **Host-managed config:** none.
- **Secrets:** none in this repo. `.gitignore` covers `.env`; nothing currently depends on one.
- **Remote:** `origin` = `git@github.com:buya-v/digital_coop_bank.git` (reachable; `main` tracks `origin/main`). Softhouse's "push main before launching a batch" rule applies as written. Only the orchestrator pushes — worker agents commit to their branch and never push.

## Codebase facts

- `run_pipeline.py` defines **7 phases**, including `sprint_planner`, but no sprint output contains a `sprint_planner.md`. The current prompts also mandate sections ("Consistency Check", "Proposed Business Rules") that appear in none of the committed outputs. **The code was rewritten after the outputs were generated; nothing here reproduces what is checked in.**
- `validate_output()` in `run_pipeline.py` catches two real defects in the committed files: a `"Marcus Aurelius"` placeholder in `sprint_2/technical_architect.md:407`, and a duplicate H1 in `sprint_3/technical_architect.md` where a truncated first attempt restarts at line 185. The validator postdates the content.
- **Validation retry is blind** (`run_pipeline.py:196`) — it re-runs the identical prompt without telling the model what failed, so deterministic failures recur.
- **`redo_phase()` can skip a phase** — the guard at line 285 rejects `idx > current_phase_index` but permits `==`, then advances the index, silently marking an unrun phase done. Should be `>=`.
- **The retro/learning loop has never been exercised.** All three recorded retros say "No specific feedback", so `sprint_learnings.md` still holds only its two boilerplate rules.
- `final_requirements/` totals ~458 KB across six documents; `03_acceptance_criteria.md` alone is 140 KB / 247 scenarios. Reading all of them at once will exhaust context — read the one document a task actually needs.
- There is **no OpenAPI or JSON Schema artifact** anywhere, despite ~192 endpoints being described. API contracts are key names only, with no types, nullability, or formats.

<!-- LEARNED PATTERNS START -->

### Run 20260720-161202 — Mongolia correction phase 1 (2026-07-21)

Cleared both HARD verifier failures the run targeted: DEC-6's two-field name model and the FDIC/NCUA sponsor-bank framing. Gate went FAIL -> PASS for the first time, by changing documents, not by weakening the checker. 6 approved branches merged; the 2 rejected first drafts left unmerged.

**What worked**
- Independent reviewers caught two defects self-review would have shipped, and one the orchestrator's own non-negotiables grep missed. Both draft tasks were REJECTED on first pass. The cost of the reviewer role paid for itself on day one.
- The verifier is a genuine gate: it blocked the run's own final task and forced a document change rather than rubber-stamping.

**What the independent reviewers caught**
- T2: the DEC-6 replacement text would have FAILED the project's own verifier — it contained `ACH` twice, once inside the sentence retiring it, pushing rails 56->57. Reasoning right, wording self-defeating.
- T2: the map silently retired the term `legal_name` (9 lines) but mapped only 5, leaving the API contract `422 LEGAL_NAME_NOT_EDITABLE` dangling — invisible to the token check.
- T7: the sponsor-bank draft attached `[VERIFIED: CLAUDE.md]` to a claim CLAUDE.md contradicts, and decided a charter question that ratified open items hold open. A fabricated provenance marker is worse than none.
- T10 (adversarial, ruling on the orchestrator's own conflict of interest): ruled against the orchestrator on the bigger of two gate disputes — FDIC/NCUA was a document defect, not a checker false positive, because exempting withdrawal-prose would leave a HARD check matching nothing in the corpus. Authorised exactly one checker change (ACH+ is Mongolia's system, wrongly matched by \bACH\b). Rejected the HTML-comment exemption as a permanent laundering channel.

**Orchestrator's own errors this run (all caught, none by the orchestrator's first pass)**
- Gitignored `.softhouse/handoff/`, which destroyed BOTH level-0 tasks' output before the reviewer chain could read it. Root cause: followed the upstream README's commit guidance, which predates handoffs travelling across worktrees. Fixed in .gitignore + worker preamble + this file.
- `git add -A` during an active run committed two agent worktrees as embedded gitlinks. Fixed by untracking + ignoring `.claude/worktrees/`. Rule: stage explicit paths while workers are live.
- Reviewer prompt initially told agents to read the handoff from a filesystem path that does not exist in their worktree (branch not merged). Fixed to `git show <branch>:<path>` + three-dot diffs.
- Plan put the FDIC/NCUA text in "§1.2"; it is §1.1. Two agents corrected it independently.
- T3 was made to depend on the review task (T2) rather than on an APPROVED draft, so a rejected draft looked ratifiable. Held manually. **Planning rule for next time: a ratify/apply task must depend on the artifact reaching `approved`, never merely on the review having run.**
- Nearly concluded both gate failures were checker false positives; an independent reviewer showed one was a document defect. Do not let the checker's author rule on whether the checker is wrong.

**New knowledge**
- The verifier greps tokens, so any name-model or market assumption expressed in PROSE evades it. Confirmed live: DEC-35 / 03:476 still say "first name + last initial", which now contradicts DEC-6 and inverts DEC-35's own privacy rationale. Two agents correctly declined to fix it (ratified DEC-3 territory).
- `legal_name` is 9 lines / 11 occurrences; `04:767` is uppercase `LEGAL_NAME_NOT_EDITABLE` and is NOT among them — a reviewer's census had both facts at once; the retry corrected the reviewer.
- Post-2022 Mongolian ID cards do not print the registration number, so any OCR-populated `registration_number` path is unimplementable — the verified-value channel (XYP / MRZ / attested entry) is an open question.

**Planning advice**
- Verify section anchors against the document before writing them into a task description.
- When a spec_writer will introduce ratified text containing a token the verifier counts (a rail name, a currency), pre-check the wording against verify-docs.sh at plan time — T2's F1 was foreseeable.

**Verifier**: HARD 5/5 pass, DRIFT all = baseline (usd 312 / rails 56 / vendor 83). baseline.txt never re-based. One checker pattern narrowed (ACH+), adversarially retested: bare ACH/FDIC/first_name/SEPA still FAIL.

**Backlog carried forward**: 12 items — headline is the DEC-6/DEC-35 "first name + last initial" contradiction (needs a product-owner ratification, involves a privacy trade-off), then the currency/rails/vendor migration proper (312 USD amounts, 56 rails, 83 vendor refs still to convert), the verifier's prose blind spot, and 00_market_research.md still being entirely US/EU-framed.

### Infrastructure — handoffs must be committed (found during run 20260720-161202)

`.softhouse/handoff/` was initially gitignored, following the upstream Softhouse README's
advice that only `patterns.md`, `uat.md` and `design/` are worth committing.

That advice is wrong for the worktree execution model, and it destroyed real work:

1. A worker writes its handoff inside its own worktree.
2. Gitignored, so it cannot commit it.
3. The branch therefore has no changes.
4. The harness auto-prunes the worktree as "unchanged".
5. The handoff — the task's entire deliverable for a draft-only role — is gone.
6. The reviewer, running in a DIFFERENT worktree, has nothing to read.

Both level-0 tasks of the first run were lost this way, after completing successfully.

Two fixes, both applied:
- `.gitignore` no longer ignores `.softhouse/handoff/`, with a comment saying why.
- The worker preamble in `.claude/skills/softhouse/SKILL.md` now requires an explicit
  `git commit` of the handoff and a `git log` check before the final message. Writing the
  file is not enough; a draft-only task that commits nothing has produced nothing.

Rule for future runs: **a task whose only deliverable is a handoff must still commit.**
When re-running after this class of loss, do NOT apply the retry model upgrade — the model
did not fail, the harness did.
<!-- LEARNED PATTERNS END -->
