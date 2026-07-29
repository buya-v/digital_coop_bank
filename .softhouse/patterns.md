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

### Run 20260729-mfa-stepup — MFA enrollment + step-up (security-critical) + revokeDevice (2026-07-29)

Completed the EP-1 identity epic: MFA enrollment (TOTP, secret ENCRYPTED at rest; SMS mock port), step-up (mint a single-use member-bound step_up_token), and the now-unblocked revokeDevice (session + step-up). 2 coders (serial) + 2 DEDICATED SECURITY reviews + verifier. All 4 gates PASS (116 tests). No money/ledger. The member journey is now complete up to the ledger: onboard -> KYC -> promote -> authenticate -> profile/consents/devices -> MFA -> step-up-gated sensitive actions.

**Two security-critical components, two adversarial reviews that PROBED not read**
- Secret at rest (enrollment): the reviewer BYPASSED the ORM and read the raw secret_ciphertext column after a real enrollment — confirmed it is a Fernet token, NOT the base32 seed (seed not even a substring), decrypts only with the key, fails closed with no key. Proved the guarding test non-vacuous by swapping in a plaintext 'cipher' and watching the test fail. 'Encrypted at rest' is only credible when someone looked at the bytes on disk.
- Step-up credential (issuance): the reviewer independently probed 6 attacks — replay/single-use, expiry, cross-member binding, hash-only storage/entropy, lockout persistence, revokeDevice IDOR — all blocked. The keystone design: single-use is an ATOMIC conditional UPDATE (`SET consumed_at WHERE consumed_at IS NULL AND member_id=:caller AND expires_at>now`) acted on by rowcount==1 — no TOCTOU, member-binding and expiry folded into the same guarded write, consumed-and-committed BEFORE the route body so there's no reuse-on-failure. This is the correct shape for a single-use server-issued credential; a stateless-JWT-with-JTI-blocklist would have been more code and more foot-guns.

**A subtle bug the coder caught themselves**: lockout counters must be committed on the ERROR path — a failed step-up rolls back the session by default, which would roll back the failed-attempt increment and make lockout a no-op. The router commits the increment in its except block; a test proves it (the override session only closes, so an uncommitted increment would never reach the threshold).

**Two micro-fixes at merge**: declared the reachable 502 SMS_DELIVERY_FAILED in the contract (consistency); broke a latent import cycle (auth.deps <-> services.stepup) with a lazy import — it worked in the running app but broke importing the service standalone (a trap for a future worker/script). Neither security.

**Dependency-in-gate-env lesson recurred and was handled**: T1 added pyotp; the orchestrator's gate run showed import errors until pyotp was installed in the gate env. When a run adds a dep, install it before trusting the gate (CI covers it via `pip install -e .[dev]`).

**Verifier**: check_models PASS (63t/49 money) · check_migration PASS (146==146) · openapi validate PASS · pytest 116 · TOTP secret ciphertext / step-up hash-only / revokeDevice step-up-gated / IDOR-404 · no money/ledger.

### Run 20260729-consents-devices — EP-1 consents + device-listing self-service (2026-07-29)

Added the memberOAuth2-only self-service endpoints (listMyConsents / upsertMyConsent / listDevices) on the auth foundation. 1 coder + 1 IDOR-focused review + verifier. All 4 gates PASS (98 tests). No schema change, no money/ledger.

**Deferred the step-up-gated op instead of half-building it**
- revokeDevice's contract security is `memberOAuth2 + stepUpAssertion`. Step-up isn't built, so revokeDevice was NOT mounted — and a route-allowlist test (`test_only_expected_feature_routes` asserts the mounted feature routes EXACTLY equal an explicit set) guardrails it: if anyone later mounts a step-up-gated op without enforcing step-up, the suite fails. Don't ship a security-gated operation without its gate; make the deferral enforceable, not just a comment.

**IDOR excluded structurally again (the pattern holds)**: identity only from get_current_member; repos take the owning member_id as a required arg; path params ({consent_type}) are resource names validated against an enum, never owner selectors. Non-vacuous A<->B tests (B seeded distinct, unchanged after A's hostile write).

**Audit-integrity micro-fix**: the default consent `channel` was `MOBILE_APP` — but stamping a SPECIFIC capture channel we don't actually know onto a legally-meaningful consent audit row asserts a possibly-false fact. Changed to a neutral `UNKNOWN` sentinel (explicit caller value still wins). For audit/compliance fields, a truthful 'unknown' beats a plausible fabrication — same honesty rule as the requirements work, now in code.

**Honestly-flagged assumption**: SERVICE_REQUIRED_CONSENTS = {TERMS_AND_BYLAWS, PRIVACY_POLICY, E_SIGN_DISCLOSURE} is an invented policy set (04 doesn't enumerate it) — kept as a replaceable frozenset with a comment saying so, not asserted as fact. The reviewer confirmed the honest framing.

**Verifier**: check_models PASS (61t) · check_migration PASS (142==142) · openapi validate PASS · pytest 98 · routes wired · revokeDevice deferred+guardrailed · no money/ledger.

### Run 20260728-auth-profile — member auth foundation + profile self-service (2026-07-28)

Added the member-authentication foundation (verify external-IdP RS256 Bearer JWTs -> get_current_member) and the first post-auth endpoints (getMyProfile/updateMyProfile), extending Member for the profile. 2 coders (serial) + 2 reviews (one a dedicated SECURITY review) + verifier. All 4 gates PASS on merged main (82 tests). No money/ledger. A member can now onboard -> KYC -> promote -> AUTHENTICATE -> manage their profile.

**Auth: verify, don't issue — behind a port + dev signer**
- The contract's memberOAuth2 is an EXTERNAL operator-chosen IdP (self-host/data-residency). So the backend VERIFIES RS256 Bearer JWTs; it does not run an authorization server. Built a verifier PORT + a DEV/TEST-ONLY RS signer (ephemeral, refuses production) so the suite can mint tokens without a real IdP — the same port+mock pattern used for ХУР KYC. This is how you build + test auth against an unavailable external IdP.

**The security review was an EXPLOIT ATTEMPT, not a read**
- JWT verification is attacker-facing; a permissive verifier is a full auth bypass. The reviewer independently FORGED 13 attack tokens and ran them against the verifier: alg:none, HS256 key-confusion (RSA public key as the HMAC secret, both PEM and DER), RS384/PS256/ES256 substitution, expired, no-exp, bad-sig, nbf, wrong/missing iss/aud, unconfigured-key. ALL rejected; only well-formed RS256 accepted. For security-critical code, the bar is 'the reviewer wrote a working exploit attempt and it failed', not 'tests exist'. Key controls confirmed: RS256 pinned as a non-configurable constant + passed explicitly to decode (header can't choose alg/key), signature actually verified (no unverified-decode trust path), fails closed, sub resolved to a DB row (no claim trusted as a member fact).

**IDOR excluded by construction, not by a check**
- getMyProfile/updateMyProfile take identity ONLY from get_current_member (the token sub); NO member id is read from path or body. So cross-member access is structurally impossible, not check-dependent. The reviewer confirmed with non-vacuous A<->B isolation tests (distinct seeded members; patch A, assert B unchanged). The right shape for a 'my resource' endpoint: the row is the caller's identity, never an addressable parameter.

**Contract-vs-non-negotiable adjudication**: the profile PATCH schema LISTS registration_number, but DEC-6(d) makes the KYC-verified national ID authoritative. Returning 422 (a casual profile edit must not overwrite the identity key; changing it is a future step-up re-KYC flow) is CORRECT enforcement, not a conformance violation — listing a field in an input schema doesn't obligate unconditional acceptance when the contract's own text conditions it on a capability (step-up) this slice doesn't ship. The reviewer adjudicated this rather than mechanically flagging it.

**Orchestration lesson (own it)**: the merged-main gate run initially showed '5 errors' — NOT a code defect: T1 added PyJWT[crypto] to pyproject, the worker/reviewer venvs had it, but the ORCHESTRATOR's gate-runner environment did not, so app.auth failed to import. Diagnosed, installed the dep, re-ran -> 82 passed. LESSON: when a new run adds a dependency, the orchestrator's own verification env must install it before trusting a gate run; a bare ModuleNotFoundError at collection is an env gap, not a regression. Confirmed CI installs it (`pip install -e .[dev]` reads pyproject).

**Verifier**: check_models PASS (61t/49 money) · check_migration PASS (142==142) · openapi validate PASS · pytest 82 · DEC-4/IDOR/auth-attack tests green · no money/ledger in auth+profile code.

### Run 20260728-onboarding-slice2 — eligibility + ХУР KYC + draft->Member promotion (2026-07-28)

Completed the EP-1 onboarding vertical up to the ledger boundary: common-bond eligibility (config-driven), ХУР/XYP KYC behind a port+mock, and draft->Member promotion on KYC approval (PENDING_PAYMENT). 2 coders (serial) + 2 reviews + verifier. All 4 code gates PASS on merged main (58 tests). Stops before share purchase (needs the ledger). No money/ledger.

**What worked**
- Config-driven eligibility with a BOND-NEUTRAL default rule set: narrowing to the chosen common bond (employer/association/aimag) is a config edit, not a code change — correct given the PO hasn't picked the specific bond. Don't hard-code a policy value the decision-owner hasn't decided.
- KYC-before-Member reconciliation: KycSubmission has a NOT-NULL member_id FK, but KYC runs pre-auth (DEC-4: no Member until approval). Resolved by carrying in-flight KYC state (kyc_inquiry_id unique + kyc_status) on the DRAFT and creating the member-linked KycSubmission only at promotion. The FK shape forced the design; the coder reasoned it out against 04+contract rather than jamming a Member in early.
- eKYC as a PORT + deterministic MOCK (no real ХУР API in dev): the mock's outcome is a construction-time toggle so tests drive every branch (APPROVED/REJECTED/PENDING_REVIEW/IN_PROGRESS) by overriding the provider dependency. This is how you build a feature that depends on an unavailable external integration — behind an interface, with a scripted double.

**The DEC-4 review (the crux, and how it was verified)**
- A non-negotiable invariant ('no member record ever in a rejected status') is only as good as the proof it holds. The reviewer traced EVERY Member-construction path (grep: Member( appears once, in MemberRepository.create; called once, in _promote; called once, under `if APPROVED`) and confirmed the mandatory test is NON-VACUOUS (it uses a COMPLETE identity that WOULD promote if the code wrongly fired on reject, so member_count()==0 genuinely proves it). Also checked idempotency (a re-polled getKycStatus can't double-promote — _RECORDED_FINAL short-circuits). For a safety invariant, 'trace every path + prove the test would fail if violated' is the bar, not 'a test exists'.
- Reviewer nits fixed as micro-fixes: getKycStatus could emit an UNDECLARED 502 (added to the contract); _promote could create a Member with a NULL registration_number (added a guard). Both small, both real.

**Foundation reuse held**: slice-2 added eligibility.py, kyc.py, adapters/ekyc/ on the slice-1 repo/service/router/Error/bootstrap-token pattern with no duplication. Repos flush-not-commit; routers commit on mutation. The pattern is proving reusable across features — the point of investing in it in slice 1.

**Verifier**: check_models PASS (61t/49 money) · check_migration PASS (142==142) · openapi validate PASS · pytest 58 · EP-1 routes wired · zero money/ledger in onboarding+kyc code.
**Backlog (slice 3+ / blocked)**: share purchase (US-2.1) — BLOCKED on the ledger; a concurrency row-lock on promotion (two concurrent getKycStatus polls, currently backstopped by DB uniqueness -> 500 not graceful); MFA/step-up, devices, profile, consents CRUD; the specific common-bond choice to pin the eligibility config.

### Run 20260724-onboarding-slice1 — first feature vertical (EP-1 onboarding draft) (2026-07-24)

Turned the scaffold into a running feature: the resumable onboarding-application draft (create/get/update) + the persistence->service->router FOUNDATION every future endpoint will follow. 2 coders (serial) + 2 reviews + verifier. All 4 code gates PASS on merged main (check_models 61t, check_migration 141==141, openapi validate 192 ops, pytest 30). Blocker-free: no money/ledger/ХУР/KYC/eligibility.

**Unblocked by PO direction, built to the blocker-free edge**
- This was buildable ONLY after the PO gave direction on the legal blockers (common bond=defined-SCC, eKYC=ХУР/XYP, self-host, e-votes count, tax=dividends). The slice deliberately stops at the two lines that still need humans: the share-purchase step (needs the LEDGER) and the KYC step (needs the ХУР integration + is a later slice). Build to the edge of the blockers, not past them.

**Data-model judgment (the coder reasoned, didn't just follow the suggestion)**
- Onboarding modelled as a DISTINCT pre-auth `onboarding_application` draft, not Member-in-PENDING_KYC — because the contract mints application_id+resume_token BEFORE any Member exists, and a Member-at-bootstrap would violate DEC-4 (no member record in a rejected status). Justified against 04 (which carries onboarding_state on Member only post-auth) AND the contract AND a ratified DEC. The reviewer verified there's no live column conflict yet and flagged the promotion-time concern for later.

**Reviewer caught a griefing vector a gate can't**
- The draft's registration_number had unique=True. On a PROVISIONAL, applicant-entered draft that's a DoS: a throwaway draft pre-claims a real applicant's national ID and blocks their onboarding. Authoritative uniqueness belongs on Member, not the draft. Gates all passed — this is a security/abuse property no gate checks. Fixed in-schema (model+migration lockstep) before building on it.

**Foundation patterns set for the whole app**
- BaseRepository = get/add/flush, NEVER commits (request is the transaction boundary; the router commits on successful mutation, get_session rolls back uncommitted work on close). Logic in the service, not the router. Bootstrap token = opaque secrets.token_urlsafe, only its SHA-256 hash stored, honestly documented as NOT full auth. registration_number = STRUCTURAL regex only (^[Cyrillic]{2}[0-9]{8}$), never an invented check-digit. Tests use in-memory SQLite + StaticPool with get_session overridden — no real DB; production stays Postgres.
- Contract-fidelity even on error codes: GET->404 vs PATCH->401 for a non-resolving token is NOT an inconsistency — it faithfully mirrors each operation's DECLARED error set (PATCH has no 404). Conform to the contract, don't 'tidy' it.

**Verifier**: check_models PASS (61t/49 money) · check_migration PASS (141==141) · openapi validate PASS · pytest 30 · router wired · zero money/ledger/ХУР code.
**Backlog (slice 2)**: checkOnboardingEligibility (config-driven common_bond_rules), ХУР/XYP KYC (createKycSession/getKycStatus behind a provider port + mock), the draft->Member promotion (+ reconcile onboarding_state duplication), the 409 REGISTRATION_NUMBER_MISMATCH code at the SUBMITTED transition, and the 2 untested error branches (PATCH non-resolving token, create CHANNEL_UNVERIFIED).

### Run 20260724-market-research-mn — rewrite 00 for Mongolia (2026-07-24)

Rewrote the last wholesale US/EU-framed document (00_market_research.md) to Mongolia. 1 analyst + 1 independent fabrication-focused review + verifier. APPROVED, docs gate 5/5, rails re-baselined 20->15 (00's US rails removed).

**What worked — fabrication control as the primary design constraint**
- Market research is THIS project's characteristic failure (an agent previously invented a Mongolian e-money licensee list and had to retract). The task made "do not fabricate" the #1 rule and gave CLAUDE.md as the ONLY fact source; the reviewer's crux was a claim-by-claim audit classifying every figure as (a) CLAUDE.md-traceable, (b) explicitly [UNVERIFIED]/qualitative, or (c) unmarked-specific = REJECT. Zero (c) found.
- The right honesty MOVE the writer made: §2.4 REFUSES to name e-money licensees, citing the prior retraction, rather than listing plausible ones. Naming a category qualitatively and marking specifics [UNVERIFIED] beats a confident invented roster. Secondary banks (Golomt/TDB/Xac/etc.) named as existing but with ALL specifics [UNVERIFIED] — class (b), acceptable.
- The rewrite surfaced the honest, uncomfortable thesis instead of preserving the US one: 98.3% banked = NO underbanked gap; Khan Bank's super-app = 'neobank parity is table stakes, not a differentiator'; SCC-not-insured = 'a genuine competitive disadvantage'; the 78,608-sector-vs-100,000-KPI contradiction surfaced. A market-research rewrite's value is telling the truth about the market, not re-skinning the old pitch.
- Cross-ref preservation: §2.5 (Aspiration/international analogues) retained BECAUSE 05 cross-references it — international cooperatives (Desjardins, Coop Pank) kept but explicitly RELABELLED as analogues, not local competitors. A reframe must keep the anchors other docs point at.

**Verifier**: HARD 5/5 · rails 20->15 (re-baselined; 00 contributes only ACH+ now; residual = 06 deferred + the 01 DEC-6 retirement note) · USD 131 / vendor 6 unchanged.

### Run 20260724-code-sync — adopt migrated requirements names into backend (2026-07-24)

Closed the doc<->code seam left by the currency/rails/vendor requirements runs: renamed backend ORM models + initial migration + OpenAPI source to the vendor-neutral / Mongolia-rail names. 2 coders + 2 reviews + verifier. ALL FOUR code gates PASS on merged main (check_models 60t/49 MoneyMinor, check_migration 139==139, openapi validate 192 ops, pytest 24). Backend residual old-names = 0; docs and code field names now AGREE.

**What worked**
- Splitting by GATE BOUNDARY, not by rename: ORM+migration together (they are check_migration-coupled — a rename in only one side fails the gate) as one agent; OpenAPI (its own validate gate, disjoint dir) as another. Parallel, no merge conflict.
- Reviewers RAN THE GATES THEMSELVES on the branch content (check_models/check_migration/pytest for the ORM branch; validate.py for OpenAPI) rather than trusting the handoff's pasted output. For code, re-running the gate is the review.

**The scoping-literalism catch (reviewer earned its keep)**
- The OpenAPI coder renamed everything in its explicit list but LEFT `plaid_item_ref` in the ExternalAccountLink schema, reasoning it was a 'column' owned by the ORM agent. But it is a live API-CONTRACT property; T1 had already renamed the ORM column to account_link_ref, so the contract now diverged from the model. The reviewer grepped, pinned all 4 occurrences with exact locations, and called MICRO-FIX. Orchestrator applied it (property key + 3 description notes), re-ran validate (PASS), residual=0. LESSON: a field rename spans model AND contract AND migration; 'that belongs to the other agent' is how a rename ends up half-applied across a boundary. The cross-cutting reviewer/orchestrator must own the seam.

**Verifier**: check_models PASS · check_migration PASS (139==139) · openapi validate PASS (172 paths/192 ops/304 schemas) · pytest 24 · backend old-name grep = 0. Docs (01-05) and code now use identical names (kyc_inquiry_id, account_link_ref, INSTANT_LINK, ACH_PLUS|RTGS, /webhooks/{kyc,account-link,payments,card}).

### Run 20260724-vendor-removal — US vendors -> role-neutral (2026-07-24)

Neutralized Stripe/Plaid/Lithic/Persona/Jumio across 01-05: prose -> role abstractions (payment processor / account-linking provider / eKYC provider / card issuer-processor), schema identifiers -> neutral names via a canonical rename table, DEC-5 amended. 5 applies + 5 reviews + verifier, all APPROVED. vendor DRIFT 83 -> 6 (residual entirely 06, deferred), re-baselined. Docs gate 5/5.

**What worked**
- A canonical IDENTIFIER-RENAME TABLE in the brief (persona_inquiry_id->kyc_inquiry_id, plaid_item_ref->account_link_ref, plaid_public_token->account_link_public_token, PLAID_INSTANT->INSTANT_LINK, 502 PLAID_UNAVAILABLE->502 ACCOUNT_LINK_PROVIDER_UNAVAILABLE, /webhooks/{persona,plaid,stripe,lithic}->{kyc,account-link,payments,card}) made a cross-doc rename CONSISTENT and reviewable. The 04 reviewer verified old-ids=0 AND new-ids-exact AND renamed-at-every-reference-site (field def + API + flow + traceability) — a rename is only correct if applied at EVERY reference, not just the definition.
- HONESTY: Mongolia vendors are not chosen, so every de-named provider became "procurement decision (TBD)", eKYC carrying the ХУР/XYP state-register compliant-alternative note (blocking-question 2). No Mongolian vendor invented.
- DEC-5 (normative) amended to remove the named vendor, define by role, and CORRECT its own false claim that "vendor substitution is an integration change, not a requirements change" — false precisely because vendor names had leaked into schema field names and error codes. The migration makes that true going forward.

**Disambiguation the reviews enforced**
- "Persona" the VENDOR vs "Persona(s)" the user-persona noun (P-1..P-5) vs "Personal" substring — every 02/01/05 reviewer grep-verified that only the vendor was neutralized and the noun/substring left. A naive find-replace would have corrupted the user-persona roster.
- Orchestrator caught a cross-doc INCONSISTENCY the per-doc reviews flagged: 05's R-2 still echoed the "integration change, not a requirements change" claim after DEC-5 (in 01) had corrected it. Fixed as a micro-fix aligning 05 to the corrected DEC-5. Cross-doc claims must be reconciled after all slices merge — a per-doc review can only flag it, the orchestrator resolves it.

**Backlog surfaced**
- CODE SYNC (high value, natural next): the backend carries the OLD vendor field names verbatim (models persona_inquiry_id/plaid_item_ref/PLAID_INSTANT enum, migration DDL, OpenAPI schemas — 124 hits) and explicitly flags them as awaiting this requirements change. A follow-up run should adopt THIS brief's rename table in the code and re-run the code gates (check_models, check_migration, openapi validate). Doc field names and code field names now diverge until then.
- Other-vendor abstraction: e-signature (DocuSign/Dropbox-Sign-class) and notification (SendGrid/Twilio-class) vendors are already framed as `-class` role abstractions and out of the five-vendor scope, but a completeness pass could give them the same TBD-provider treatment.
- 06 (ledger addendum) still carries 6 vendor refs — clears with the controller ledger rewrite.

**Verifier**: HARD 5/5 · vendor 83 -> 6 (re-baselined; residual entirely 06, deferred; 01-05 are vendor-clean) · USD 131 / rails 20 unchanged.

### Run 20260724-payment-rails — US rails -> Mongolia (2026-07-24)

Migrated US payment-rail concepts (ACH/FedNow/SEPA/wire) across 01-05 to Mongolia's system: ACH+ (<=₮5m, 24/7), Banksüljee/RTGS (>₮5m), NETC (cards). 5 applies + 5 reviews + verifier, all APPROVED. rails DRIFT 56 -> 20, re-baselined. Docs gate 5/5 (incl. the HARD 3m-threshold check — never introduced).

**What worked**
- A mapping brief that carried the THRESHOLD ROUTING MODEL (>₮5m -> RTGS; <= -> ACH+), not just a term dictionary. The rail choice is amount-dependent, so a term-only brief would have produced contradictions.
- The routing model exposed a latent defect: a scenario labelled a `2,500,000₮` transfer a "wire", but 2.5m is BELOW the ₮5m RTGS threshold, so under Mongolia's rules it is ACH+, not RTGS. The apply RE-DERIVED it to 6,500,000₮ (>5m) so the RTGS demo is genuine; the reviewer recomputed every US-4.2 amount against the threshold and confirmed no sub-5m amount is labelled RTGS. Same discipline as the currency ×1000 pass.
- HONESTY on return codes: US NACHA codes (R01) removed, the human reason kept, and the return-code CATALOGUE marked "settlement operator's config, TBD pending BoM settlement-agent selection" — NOT a fabricated Mongolian code scheme. The brief mandated this and reviews enforced it.

**Reviewer/judgment catches**
- The canonical 04 apply also remapped the Transaction `type` enum (WIRE_OUT->RTGS_OUT, RTP_*->EXTERNAL_ACH_PLUS_*) — a WIRE_OUT type is contradictory once WIRE leaves the rail enum. The reviewer grepped ALL docs for the old enum members and confirmed zero dangling references before blessing it. A consequential enum rename must be dangling-ref-checked across the whole corpus, not just the edited file.
- A doc correctly LEFT the DEC-6 "ACH/wire formats retired as market-invalid" sentence unchanged — migrating a sentence that EXPLAINS a retired rationale would resurrect it. Distinguish active references from historical/retirement notes.
- Orchestrator caught a MISS the per-task reviews couldn't: 03:574 ("an ACH payee" in US-4.4) sat just past the US-4.2 range the 03 apply worked, so it survived. Found by inspecting the gate's residual per-doc BEFORE re-baselining. LESSON: before re-baselining a drift metric downward, enumerate the residual and confirm each item is legitimately-held vs a miss — do not bake a miss into the new baseline.

**PO-flagged (backlog)**: (a) the Transaction `type` enum remap is [UNVERIFIED] pending PO/architecture confirm; (b) the enum has RTGS_OUT but no RTGS_IN (inbound large-value gap), faithfully carried from the baseline's WIRE_OUT-with-no-WIRE_IN — worth a PO decision, not a regression introduced here.

**Verifier**: HARD 5/5 (3m-threshold clean) · rails 56 -> 20 (re-baselined; residual = 06+00 deferred + the 01 DEC-6 retirement note) · USD 131 / vendor 83 unchanged.

### Run 20260724-dec18-amendment — currency TYPE flip USD->MNT (2026-07-24)

Amended DEC-18 (normative, 01 §6) and all doc-level "all amounts USD" declarations across 01-05 to MNT (ISO 4217 numeric 496), with a transitional-exceptions clause covering the bounded held-USD remainder. Also fixed minor-units par literals the amount pass had MISSED. 4 applies + 4 reviews + verifier, all APPROVED. Docs gate 5/5; zero currency-type USD declarations remain in 01-05.

**What worked**
- Executing an ALREADY-RATIFIED direction (CLAUDE.md fixes the market as Mongolia / MNT) as spec_writer tasks rather than re-litigating it as a user decision. A normative DEC amendment is fine to execute when the PO direction is already recorded; the transitional-exceptions clause kept it honest (DEC-18 now says MNT while 131 residual USD amounts remain, each enumerated as pending a named downstream decision — no false "all MNT" claim).
- A committed brief with VERBATIM canonical wording made 4 agents produce identical convention text.

**A worker caught a defect in MY brief (the value of honesty-over-guessing)**
- The brief told T5 to fix a par literal at "05:1084". That line does not exist (05 is 456 lines). The literal is at 04:1084. T5 did its real edit (05:14) and REFUSED to invent the phantom one, diagnosing the 04-vs-05 typo. The independent reviewer confirmed. Lesson: when an agent can't find an instructed target, "I could not find it, here's why" is the correct answer — do not fabricate a plausible edit. My brief's line-number provenance was the bug.

**Currency-apply MISS surfaced and fixed**
- Three minor-units par literals (04:776 amount+par_value, 04:781 redemption, 04:1084) read `2500` (=$25.00 in cents) with NO `$` sign, so the currency-apply regex never counted them and the amount pass skipped them. Fixed to 1000000 (=10,000₮×100), now matching the ORM/migration par (line 179). GENERAL LESSON: a `$`-anchored inventory misses bare minor-units literals in schema/API examples. A currency migration must ALSO sweep for unmarked numeric money literals (amount:/par_value:/N cents), not only `$` tokens.
- 04:1084 sat inside a Stripe vendor sentence; fixed ONLY the currency portion as an orchestrator micro-fix, leaving the vendor words for the vendor-removal run. Split a mixed line by concern.

**Verifier**: HARD 5/5 · USD drift 131 (unchanged — type declarations + non-$ literals aren't $-counted; coherence, not the drift number, was the goal) · rails/vendor unchanged.
**Backlog added**: minor-unit TERM cleanup — "cents" still appears as the minor-unit name (04:9 gloss, 04:657 *_cents config keys, and elsewhere); MNT's minor unit is möngö (obsolete), so the whole-tögrög convention means these should be reconciled/de-"cents"-ed together in one terminology pass.

### Run 20260724-currency-apply — USD->MNT re-denomination (DEC-18) (2026-07-24)

Applied the PO-confirmed re-derivation table to final_requirements 01-05, line-by-line by role. 7 applies + 7 independent opus reviews + verifier. USD drift 312 -> 131 (-181 applied); the residual 131 are the deliberately-HELD sets. Re-baselined usd=131. HARD gate 5/5. NO content lost despite a serious orchestration incident (below).

**What worked**
- A committed APPLY BRIEF (`.softhouse/currency-apply-brief.md`) as the single source of truth — confirmed anchors + full role table + explicit HELD list + notation — meant zero re-derivation and consistent values across 7 agents. Write the shared spec to main BEFORE spawning; worktrees fork from it.
- Splitting the 216-ref file (03) into 3 epic-boundary slices, SERIALIZED as a chain (same file), each following the ×1000 illustrative scale the first slice established. The convention propagated cleanly (T3a set ×1000; T3b/T3c matched it).
- Reviewers RECOMPUTED every worked example instead of trusting handoffs. They confirmed: coupled operands re-derived not digit-scaled; the reconciliation-defect residual preserved at scaled magnitude ($0.13 -> 130₮); the blocked $88.20 installment held WITH its coupled $40 operand (holding one without the other would have silently broken the shortfall scenario); the AML structuring amount re-derived to stay sub-threshold AND chosen to avoid colliding with the velocity limit.
- Polysemy handled per-line by role: same token string, different value — $25 par->10,000₮ vs $25 P2P-send->25,000₮; $10,000 DEC-73->11,400,000₮ vs $10,000 DEC-65 program-cap HELD; $1,000 DEC-36->550,000₮ vs $1,000 DEC-45 de-ratified HELD. A blind find-replace would have corrupted all of these.

**CRITICAL INCIDENT — worker mutated the shared checkout (own it)**
- T3a's FIRST command ran `git checkout -b <branch>` in the SHARED checkout `/Users/buv/digital_coop_bank` instead of its worktree, switching the ORCHESTRATOR's HEAD off main. I then merged FOUR reviewed docs (T1/T2/T6/T7) without checking `git branch --show-current`, so they landed on the misnamed branch, and my `push origin main` calls were no-ops against a frozen main. Discovered only when T3a's handoff reported it.
- Root causes: (1) a worktree worker ran git against the shared checkout; (2) I merged blind, never asserting HEAD==main.
- Recovery (no content lost): the misnamed branch held exactly what main should be, so fast-forwarded main to it, pushed the REAL main, re-pointed the T3a branch to its true deliverable commit. T3a itself did the right thing — it refused ref surgery under a live orchestrator and committed to its worktree branch.
- HARDENED, now standing rules: (a) every worker preamble must open with `pwd` + `git rev-parse --show-toplevel` self-check and "NEVER run git against the shared checkout"; (b) the ORCHESTRATOR asserts `git branch --show-current == main` before EVERY merge (applied for T3a/T3b/T3c and it held). A stale-fork three-dot diff (`main...branch`) is also required when reviewing a branch whose fork base drifted.

**Scope decisions (recorded)**
- DEFERRED whole docs: 06 (ledger addendum — do-not-implement, controller rewrite pending; re-denominating doomed content is waste) and 00 (no USD refs; needs its own Mongolia rewrite).
- HELD (residual USD, tracked, NOT oversights): KPI cluster (magnitude-truncated $M values), persona incomes, all round-ups (deferred), $88.20+coupled $40 (rate-model blocked), program-config caps (DEC-65/63, program-budget pending), superseded/de-ratified drafts.
- Every apply agent independently surfaced the DEC-18 currency-TYPE tension: docs now state amounts in ₮ while the DEC-18 declaration + doc-level "all amounts USD" conventions still say USD. That normative flip (01 §6 owns it) is a distinct amendment — backlogged, not done in an amount pass.

**Verifier**: HARD 5/5 · USD 312->131 (re-baselined DOWN, deliberate migration step) · rails=56/vendor=83 unchanged. **Residual 131 by doc**: 03=74, 05=16, 01=13, 04=9, 02=5, 06=14(deferred).

### Run 20260724-persistence-layer — persistence & service wiring + ORM hardening (2026-07-24)

Turned the completed contract+schema into a runnable persistence layer, WITHOUT overreaching into a feature endpoint. 4 tasks, all 4 independently reviewed and APPROVED. Final main: 60 tables, migration 139/139 in lockstep, 24 tests, all gates PASS.

- **T1** sync SQLAlchemy engine/session factory + `get_session` dependency (import never connects; `DatabaseNotConfigured`; async deliberately deferred).
- **T2** `/ready` now a real 3-state DB liveness probe (no DB -> 200 degraded; SELECT 1 -> 200 ready; failure -> 503, no leak).
- **T3** offline CI gate: renders `Base.metadata` DDL via mock engine and asserts it matches `0001_initial._UP` — drift caught with NO database, before the Postgres apply step.
- **T4** reconciled `RecipientIdentifierType` (was 1 real enum + 2 DeferredEnums) to a single shared Postgres enum.

**Scope discipline (the important decision):** the honest next step was NOT a feature slice. The identity contract exposes member data only as *my profile* (needs auth, unbuilt) or *onboarding* (needs the blocked eKYC decision) — so any feature endpoint now would collide with auth or a blocking question. Built the plumbing every future endpoint needs instead, against a contract-honest target (`/ready`'s docstring already promised a DB check). The ledger (backlog #0) remains untouched — still a human-controller task.

**What the independent reviewers caught / verified that a gate could not:**
- **T4 corrected a false planning premise of MINE**: I planned it saying `RecipientIdentifierType` lived in `identity.py`. It does not — the owner is `deposits.py:52` (E-11). The worker found this, retargeted, and the reviewer independently re-confirmed the owner location AND byte-level `name=` equality across all 3 Enum sites (a mismatch there would silently create two Postgres types). The planner is not a reliable source of repo facts; verification is.
- **T4 semantic check**: reviewer traced payments E-17 `debtor_identifier_type` and lending E-22 `addressed_via` to the SAME DEC-3 glossary enum before blessing the merge — guarding against a coincidental-name over-merge.
- **T2 dependency-resolution subtlety**: a generator dependency's `raise` fires during FastAPI resolution, BEFORE the handler body, so a handler try/except cannot catch `DatabaseNotConfigured`. Both worker and reviewer reasoned this correctly; the `ready_session`-yields-None pattern is the right fix. Reviewer also found the residual malformed-URL->500 edge (backlogged).
- **T3 normaliser scrutiny**: reviewer confirmed the drift-gate normaliser is minimal (whitespace + trailing semicolon only) and does NOT over-collapse — an over-normalising gate is security theatre. Added a multiset count guard (reviewer's LOW note) as an at-merge micro-fix.

**Process/infra note:** the FIRST T3 and T4 review agents BOTH died on infra errors (API connection closed; watchdog stall) mid-render — NOT verdicts. A failed review agent is NOT an approval; re-ran both, re-scoped to read-and-judge (no heavy offline DDL renders in the reviewer — the orchestrator runs those during verification). The leaner reviews finished fast and clean. Lesson: keep reviewers to reading+judgment; give the deterministic renders to the orchestrator's verification step.

**Verifier**: ORM gate PASS (60/677/49) · migration gate PASS (139/139) · 24 tests · docs gate HARD 5/5, DRIFT unchanged (usd=312/rails=56/vendor=83). No re-baseline.

### Run 20260722-orm-schema — ORM models + initial migration (2026-07-22)

Derived SQLAlchemy 2.0 models for all 59 entities of 04 §2 (60 tables incl. one child), plus the initial Alembic migration. Gate PASS (60 tables, 677 columns, 49 money columns, no float), 19 tests, migration renders 76 CREATE TYPE + 60 CREATE TABLE + 3 ALTER.

**What worked**
- 5 parallel domain slices + the shared-schema/pattern rules given up front: zero table/enum collisions across slices.
- The money non-negotiable is now enforced STRUCTURALLY: MoneyMinor (BIGINT minor units) rejects a float at the column-binding boundary. Money cannot enter a money column by accident.
- Two invariants preserved in the schema itself: secret ballot (VoteRecord has no member_id / no transitive member FK, omits timestamps for §5.1 coarsening) and the blocked rate model (zero APR/rate/computed-installment values in lending).
- Ledger core (account/ledger_entry/transaction) modelled as STRUCTURE ONLY: balances materialized-not-written, entry_type/transaction_type deferred to String (value sets HELD on the corrected ledger design, NOT 06's defects). The right handling of the do-not-implement dependency: tables exist, undecided design does not.

**Orchestrator catches (things per-slice review could not see)**
- Cross-slice FKs: every slice modelled FKs to other slices' tables as BARE UUID to keep its standalone gate self-contained. The assembly promoted 9 of them to real ForeignKeys once all tables coexisted. Same seam-closing role as the OpenAPI gap-fill.
- CIRCULAR FK cycles (proposal<->ballot, ballot<->eligibility_snapshot, loan_application<->loan_circle) surfaced only when rendering the full-schema DDL. Fixed with use_alter on one FK per cycle → tables create, cyclic FK added via ALTER. A per-slice gate never sees a cross-slice cycle.

**Process failure — own it**
- T6 (a review) was marked in_progress in tasks.json and REPORTED to the user as "running" for two turns, but the Agent was never spawned. Caught only when "proceed next" forced a worktree check. RULE: spawn the agent in the SAME action that flips status to in_progress; "marked in_progress" is NOT evidence a task runs — an agentId or a live worktree is. Verify before reporting a task as running.

**No-DB migration technique (reusable)**
- Local machine has no Postgres/Docker. `sqlalchemy.create_mock_engine("postgresql://", dump)` + `metadata.create_all(engine)` renders the COMPLETE Postgres DDL offline (CREATE TYPE once, tables in dependency order, use_alter FKs as ALTER) — no connection. That is the initial migration content. CI applies it to real Postgres for the canonical check.

**Verifier**: ORM gate PASS (60/677/49); 19 tests; docs gate untouched. **Backlog**: (a) canonical migration should also be autogenerate-consistency-checked in CI (empty diff vs models). (b) RecipientIdentifierType is a real enum in identity but DeferredEnum in payments/lending — reconcile to one shared enum. (c) THE LEDGER: account/ledger_entry/transaction are structure-only; the posting logic, chart of accounts, entry_type enum, and hold formula are STILL HELD on a controller-reviewed corrected ledger design — the standing 'needs a human controller' item.

### Run 20260722-openapi-rest — OpenAPI remaining epics, contract COMPLETE (2026-07-22)

Completed the OpenAPI 3.1 architecture-of-record: 192 operations across all EP-1..EP-13 + webhooks, 304 schemas, 38 entity-gated ops. Every 04 §3.1-§3.14 row is now an operation. Gate PASS; docs + backend gates untouched and green.

**What worked**
- 4-way parallel authoring (gov/div/fund, admin/compliance, entity-gated, webhooks) with the shared-schema-reuse rule given up-front: ZERO schema collisions this run (vs one Currency collision last run). Giving authors the existing-schema list preventively beats catching collisions after.
- The two-reviewer split (T5: T1+T4, T6: T2+T3) both APPROVED with real verification — T5 confirmed the secret-ballot privacy invariant (no member-to-choice join), T6 mechanically verified 38/38 entity-gated tags and zero rate-model fields.
- Discipline held in code: T1 kept ballot participation/choice separate; T3 encoded zero APR/bps fields (blocked rate model) and renamed LoanScheduleType to dodge EP-4; T2 Admin*-prefixed to dodge EP-8.

**The orchestrator catch — a gap no single reviewer could see**
- 9 admin ops (§3.7 dividend-runs, §3.9 grant-pools) fell BETWEEN T1 and T2: T1 (member-only) left them "to EP-12"; T2 (EP-12) left them "to EP-7". Each locally reasonable; the sum had a hole. Neither review was scoped across that T1/T2 boundary. The mechanical 192-vs-183 path reconciliation found it exactly. LESSON: with a parallel split, do a FULL-corpus coverage reconciliation at the orchestrator level — per-slice reviews check their slice, not the seams between slices. Filled by T8 (forked post-merge so the entity schemas resolved).

**Process gap to fix next time**
- T8 (the gap-fill spec_writer) got NO independent reviewer — my plan omitted its review pair, breaking the every-spec_writer-gets-a-reviewer rule. I verified it rigorously at orchestrator level (9 ops, staffSSO, idempotency-on-execute-only, no formula constants, $refs resolve) but that is a LOWER assurance bar than the reviewed slices. When adding a task mid-run, add its reviewer too.

**Verifier**: OpenAPI 172 paths / 192 ops / 304 schemas PASS. docs PASS, backend 14/14. No re-baseline.
**Backlog**: (a) EP-12 lending-admin ops carry a prose entity-gated note, not the x-entity-gated extension — consistency pass if the spec is ever filtered by that tag. (b) validate.py is lenient on $ref target types (missed IdempotencyKey mis-filing last run) — consider spectral/redocly as a stricter linter. (c) Next architecture task: ORM schema + first migration from 04's 59 entities (from the CORRECTED ledger, not 06's defects).

### Run 20260722-openapi-core — OpenAPI core (foundation + EP-1..EP-4) (2026-07-22)

First OpenAPI derivation. Produced a valid OpenAPI 3.1 architecture-of-record for the money-movement core: 54 paths / 64 operations / 95 schemas, covering every endpoint row in 04 §3.1-§3.4 (EP-1 14, EP-2 9, EP-3 21, EP-4 20). Gate = backend/openapi/validate.py (assembles root+paths+schemas+params, validates 3.1, checks all $refs). Multi-file layout let two authors work in parallel without file conflicts.

**What worked**
- The parallel split (T3 EP-1/2, T4 EP-3/4) into disjoint files worked; the only collision was one shared schema (Currency), a clean dedupe.
- Two honesty judgments under the same discipline the requirements work used, now in code:
  - T3 REFUSED to reproduce 04's `currency: USD` enum literal — it is an invalidated non-negotiable (currency is MNT). Modelled currency as a free ISO-4217 string, conflict flagged in-spec. Mirroring a source literal you know is wrong is encoding a defect, not fidelity.
  - T4 applied the Idempotency-Key non-negotiable even to 2 money-movement POSTs where 04 omits it, and marked the addition inferred rather than silently.

**What the reviewer caught that the gate could not**
- T5 found IdempotencyKey was a Parameter Object mis-filed under components.schemas (required:true as a boolean, non-schema keywords). It PASSED validate.py because openapi-spec-validator does NOT type-check $ref targets by position. Strict codegen would reject it. LESSON: the OpenAPI gate has blind spots exactly like verify-docs' prose blind spot — a valid-per-validator spec can still be structurally wrong. Independent review remains load-bearing.
- Fix: enhanced validate.py to merge params/*.yaml into components.parameters (like schemas); moved IdempotencyKey there; repointed all 9 refs across EP-3+EP-4. The params/ slice type is now part of the layout.

**New knowledge / for the follow-up slice**
- Shared schemas (Money, Currency, common enums like RecipientIdentifierType) will collide again if each parallel author redefines them. For the next slice, put shared component schemas in ONE foundation-owned file (or a _shared.yaml a single task owns) and have epic slices $ref them — don't let each slice define Money/Currency.
- The generated bundle backend/openapi/openapi.yaml is gitignored (regenerate via validate.py). Source of truth = root.yaml + paths/ + schemas/ + params/. If a committed browsable bundle is wanted, un-ignore it and have only the final assembly write it.
- validate.py's duplicate-schema/param and $ref-resolution checks are the real value; the 3.1 schema-validation alone is too lenient (see the IdempotencyKey miss).

**Verifier**: OpenAPI 54/64/95 PASS; docs gate PASS (untouched); backend 14/14 (untouched). No re-baseline.
**Backlog**: OpenAPI follow-up slice (EP-5..EP-13 + webhooks + admin; entity-gated tagged x-entity-gated; use a shared-schemas file). Then ORM schema from 04's 59 entities (from the CORRECTED ledger, not 06's defects).

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
