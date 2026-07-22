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

### Run 20260721-currency-policy — currency re-derivation POLICY table (2026-07-22)

Read-only run: gathered Mongolian income benchmarks, categorised all 312 USD amounts, produced a reviewable derivation table, and got the product owner to confirm the anchors. NO documents edited — a separate apply run does that.

**What worked**
- Splitting the currency migration into POLICY (this run) then APPLY (next) was the right call. The table surfaced ~6 real anchor decisions for the PO instead of 312 conversions; the PO approved in one pass.
- Re-derivation, not conversion: limits anchored to median monthly wage W=₮2,278,400, landing ~6x below naive USD/MNT conversion — correct for lower local incomes, and the loan band independently bracketed the real NBFI avg outstanding loan (₮2.24M).

**What the reviewers / scouts caught**
- T2 found the killer that would have wrecked a blind pass: POLYSEMY + MAGNITUDE TRUNCATION. The regex \$[0-9]... can't tell the $25 share from $25M AUM; $1 is really $1.5M. Same digits, different meanings. LESSON FOR THE APPLY RUN: convert LINE-BY-LINE BY ROLE, never a global find-replace, and handle magnitude-truncated tokens by TRUE value.
- T4 caught an arithmetic slip (5·W rounded to ₮11.5m not ₮11.4m) and, more importantly, VALIDATED the load-bearing unit inference three independent ways (the thousand-MNT wage reading — a wrong unit would have put every limit off by 1000x). The reviewer proving the anchor is the highest-value check in a re-derivation.
- Honesty discipline held under research pressure: minimum wage [NOT OBTAINED] not fabricated; SCC ₮399k flagged cumulative-not-share-price; Mongolbank/FRC SPA blocks noted, not proxied around.

**Confirmed anchors (product owner)**: share par ₮10,000 (PROVISIONAL, legal flag stays); step-up ₮550,000; P2P velocity ₮1,150,000; loan min ₮100,000; loan max ₮5,700,000; AML monitor ₮11,400,000. Round-ups DEFERRED with EP-10. KPIs held out. $88.20 blocked on rate model.

**Planning advice for the APPLY run**
- Line-by-line by role (polysemy). Held-out sets ($-KPIs, round-ups, $88.20) must KEEP their $ — so the usd DRIFT counter will drop from 312 but NOT to 0; re-baseline usd deliberately AFTER, and say so.
- DEC-18 itself must change (USD -> MNT, whole tugrik, möngö obsolete). The gate's stale-MNT-3m and usd patterns interact — check verify-docs.sh behaviour on MNT amounts before applying.
- Decide 06_ledger_addendum.md scope: it carries the SAME worked examples ($600k pool, $84.60) but is flagged do-not-implement. Convert for consistency or exclude — a scoping call.
- Recompute worked examples from P=₮10,000 (dividend 8 shares + ₮5,000 residual), don't scale digits.

**Verifier**: not run (no doc edits). Gate remains PASS from the prior run.
**Backlog carried**: 10 items; the currency APPLY run is now well-specified by the confirmed table at .softhouse/runs/20260721-currency-policy.json.

### Run 20260721-dec35 — DEC-35 Mongolian P2P confirmation + lookup rate-limit (2026-07-21)

Resolved the DEC-6/DEC-35 contradiction left open by run 20260720-161202. Product owner ratified "short form + rate-limit" via AskUserQuestion (present, so no delegation this time). 5-task chain, gate held at PASS throughout, all 4 branches merged.

**What worked**
- Small, single-decision run: draft -> review -> apply -> review -> verify. Proportionate to a 3-file change; two opus reviewers still each earned their keep.
- The reviewers verified rather than trusted: T2 re-ran the census from scratch, T4 byte-compared applied text against the map and ran the gate itself.

**What the reviewers / appliers caught**
- T2 found that run 20260720-161202 (the DEC-6 run) had ALREADY planted a latent contradiction: 03:45 uses Cyrillic field-value examples (Болд/Батын) while 03:10 still says "No placeholder personal names are used." Nobody caught it at the time; it surfaced only because the DEC-35 example would be a third instance. Fixed here with a 03:10 carve-out (map item [6]). LESSON: an amendment that adds an EXAMPLE can violate a document's own style rule; check the style/convention lines, not just the semantic ones.
- T3 (applier) correctly OVERRODE the approved draft: T1 drafted `429 LOOKUP_RATE_LIMITED`; the real API precedent is `_THROTTLED` (REMINDER_THROTTLED, REPORT_THROTTLED). T3 used LOOKUP_THROTTLED and disclosed it. An applier that spots a naming inconsistency should fix + disclose, not apply the approved-but-wrong token silently.

**New knowledge**
- Decision-log idiom: an AMENDed DEC keeps its original text in the Proposal column and records the change in the Verdict + Adjudication columns. So "first name + last initial" legitimately survives in DEC-35's proposal column — that is NOT a missed edit. Precedent: DEC-37. Do not "fix" proposal-column history.
- The token verifier is blind to prose, confirmed again: this whole run existed because a prose rule ("first name + last initial") contradicted a ratified model and the gate could not see it. Every semantic migration needs a reviewer sweep, not just a green gate.
- Naming precedent for throttle errors is `429 <X>_THROTTLED`, not `_RATE_LIMITED` (the latter is only the generic common code at 04:751).

**Planning advice**
- When a run adds an on-page EXAMPLE (a name, an amount, a code), pre-check the document's own convention lines (03:10-style "no placeholder names", actor conventions) — examples interact with style rules the token gate cannot police.
- The apply-task-depends-on-review shape recurred (T3 dep T2). It was safe this time only because the orchestrator held T3 on T2's actual VERDICT, not on T2 being "done." Still worth encoding a real "approved" gate state rather than relying on orchestrator discipline.

**Verifier**: HARD 5/5 pass, DRIFT all = baseline (usd 312 / rails 56 / vendor 83). PASS held before, during and after. No re-baselining. $25.00 at 03:486 deliberately preserved to keep usd at 312.

**Backlog carried forward**: 10 items — currency/rails/vendor migration proper, KPI re-baselining, the inverted rate model, 00_market_research.md rewrite, the verifier's prose blind spot (now doubly evidenced), and the etsgiin_ner-vs-'etsgiin ner' spacing. The DEC-6/DEC-35 contradiction is CLEARED.

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
