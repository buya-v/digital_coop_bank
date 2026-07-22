# T6 — Independent review: ORM schema (T1 identity+deposits, T2 payments+cards+dividends+roundups, T3 lending)

Reviewer role: Independent reviewer (T6). Branches reviewed on merged main (foundation present):
`softhouse/T1-orm-identity-deposits`, `softhouse/T2-orm-payments-cards`, `softhouse/T3-orm-lending`.
Source of truth: `idea-lab/final_requirements/04_technical_architecture.md` §2; pattern
`backend/app/models/membership.py` + `ledger.py`; `backend/app/db/base.py` + `types.py`; CLAUDE.md.

## VERDICT: APPROVED

All three slices, assembled together on the foundation, pass the objective gate and every
substantive check. No float money, no unresolved FK, no duplicate table/enum name, complete
coverage, honest enums, the flagged score-scaling is sound, and the lending rate model is
correctly blocked. Remaining items are merge-time wiring (explicitly not standalone-branch
defects) and two trivial nullability nits — none blocking.

## MUST-DO gate — merged run of all three slices + foundation

Copied all seven new model files into the worktree and ran the gate:

```
$ cd backend && python3 -m app.db.check_models
ORM: 36 tables · 418 columns · 37 money columns (MoneyMinor)
VERDICT: PASS   (exit 0)
```

- **Float-money columns:** NONE. `Float`/`Numeric`/`Decimal`/`REAL`/`DOUBLE` appear in the
  seven files only inside dividends.py comments/docstring describing the 04 `Decimal(5,4)`
  spec type — never as an actual column type. Every amount/balance/target/principal/
  outstanding/accrued/pledged/due is `MoneyMinor`.
- **Unresolved FKs:** NONE. Every real `ForeignKey` resolves in the merged metadata.
- **Duplicate table names:** NONE (36 distinct tables load).
- **Duplicate enum type names:** NONE cross-slice. `name="loan_status"` and
  `name="schedule_type"` each occur twice but both times **within lending.py**, reusing the
  same enum class on two columns (LoanStatus on E-20 & E-24; ScheduleType on E-19 & E-25) —
  one Postgres type, intended. `recipient_identifier_type` is defined once (T1 deposits);
  T2/T3 use DeferredEnum for the same concept, so no collision.

## Check-by-check

1. **Coverage — PASS.** Every entity E-2,3,4, E-9..E-30, E-31..33, E-47,48 is a table (36 =
   5 foundation + 31 across the three slices). Dense-entity column spot-checks vs 04 §2 all
   faithful: Loan (E-24), LoanApplication (E-20), RepaymentInstallment/ScheduledPayment
   (E-26/E-16), Card (E-18), DividendDeclaration (E-32) — no dropped columns. Only
   intentionally-omitted 04 field is `circle_rate_discount_tiers` (the blocked rate curve,
   see check 4) — documented, not silent.

2. **Money — PASS.** All money is `MoneyMinor`. Card (E-18) correctly has zero money columns
   (04 defines none). Non-money integers (multiplier, sequence, days_past_due, term months)
   are plain Integer, correctly.

3. **E-31 score types (the flagged item) — CORRECT / APPROVED.** `loan_repayment_
   performance_score` and `governance_participation_score` (04 `Decimal(5,4)`, 0..1) are
   stored as scaled Integer = value ×`SCORE_SCALE` (10_000). This is lossless and exact for a
   4-decimal 0..1 score (range 0..10_000, trivially within int). The scale constant is a named
   module-level `SCORE_SCALE = 10_000` with a clear docstring/inline comment. It is
   type-distinguishable from money (plain `Integer`, not `MoneyMinor`) and is **not** money.
   No Float/Numeric used. Sound decision; accept as-is.

4. **RATE MODEL BLOCK (T3, DEC-48/49) — PASS.** Zero interest-rate/APR/installment VALUES.
   `base_rate_apr_bps` (E-19) and `apr_bps` (E-24) are bare nullable `Integer` placeholders
   with NO `default`/`server_default` and nothing written. The DEC-49 discount-tier curve
   (`circle_rate_discount_tiers`) is OMITTED with a comment saying re-add only when unblocked.
   grep confirms no `default=`, no rate literal (1200/1745/800/600/400/0.12) anywhere in
   lending.py. `offer`/`decision` JSON note apr_bps as runtime-only fields — no schema value.

5. **Honesty / enums — PASS.** Real Enum only where 04 lists values (verbatim). `LoanStatus`
   is DEC-20 verbatim (9 values); the terminal `DECLINED_CLOSED` application outcome is
   correctly NOT in the enum (recorded in `decision.outcome` JSON per DEC-20 / 06 §8.8) — no
   invented value. `RecipientIdentifierType`/`addressed_via`/`debtor_identifier_type` →
   DeferredEnum in T2/T3 (owned elsewhere) — correct. Ledger's `entry_type`/`type` remain
   DeferredEnum (untouched). No invented enum values found anywhere.

6. **Cross-slice bare-UUID FKs to PROMOTE at merge/assembly** (not standalone-branch defects):
   - T2 dividends E-32 `factor_weights_config_ref` → ConfigurationParameter (T5)
   - T2 roundups E-47 `savings_goal_id` → SavingsGoal (T1) — **already resolvable now**
     (savings_goal coexists in the merge); promote to real FK at assembly.
   - T2 roundups E-47 `project_id` → CommunityProject (T4)
   - T3 lending E-19 `config_version_ref` → ConfigurationParameter (T5)
   - T3 lending E-20 `referral_case_id` → ComplianceCase (T4/T5)
   - T3 lending E-25 `approved_via` → MakerCheckerApproval (T4/T5)
   - T3 lending E-29 `assigned_staff_id` → StaffUser (T5)
   - (ARRAY columns E-26 `payment_transaction_ids` → transaction, E-30 `signer_member_ids`
     → member stay logical refs — arrays can't carry per-element FKs.)

7. **Ledger core untouched — PASS.** None of the slices redefines Account/LedgerEntry/
   Transaction. They FK to `account`/`transaction`/`ledger_entry` (foundation) only.

8. **Cards/lending gating — PASS.** `cards.py`, `lending.py`, and also `roundups.py` each
   carry a module docstring stating the epic is entity-gated (EP-5/EP-6/EP-10 unlawful-until-
   the-entity-decision) — schema modelled, feature not built.

## Minor observations (non-blocking, no fix required to approve)

- **E-14 nullability liberty (trivial):** T2 marks `institution_name`, `account_mask`,
  `account_subtype` Optional though 04 does not mark them `?` (04 marks only `plaid_item_ref?`
  / `processor_token_ref?`). Defensible (micro-deposit links lack institution metadata) and
  immaterial to the gate. Similar minor liberty on E-16 `next_run_at`/`retry_policy`.
- **RecipientIdentifierType ownership:** T1 (deposits) defines it as a real enum
  (`recipient_identifier_type`, PHONE|EMAIL|MEMBER_ID, which 04 §2 does enumerate); T2/T3
  defer it as String. At assembly, T2 `debtor_identifier_type` and T3 `addressed_via` may
  adopt T1's real enum for consistency. Cross-slice consistency, handled at merge — not a
  branch defect.

no application logic written
