# Code-sync brief — adopt the migrated requirements into backend code

The requirements docs (01-05) were migrated (currency→MNT, rails→Mongolia,
vendors→role-neutral). The backend code still carries the OLD names verbatim and
explicitly flags them as awaiting this change. This run makes the CODE match the
DOCS. Source of truth for names: `.softhouse/vendor-removal-brief.md` and
`.softhouse/payment-rails-brief.md` rename tables. Do NOT invent new names beyond
those tables.

## Canonical renames (code)
| old | new | kind |
|---|---|---|
| `persona_inquiry_id` | `kyc_inquiry_id` | column / field / OpenAPI property |
| `plaid_item_ref` | `account_link_ref` | column |
| `plaid_public_token` | `account_link_public_token` | OpenAPI request property |
| `VerificationMethod.PLAID_INSTANT` (value `"PLAID_INSTANT"`) | `INSTANT_LINK` (value `"INSTANT_LINK"`) | enum member + value |
| error `PLAID_UNAVAILABLE` (502) | `ACCOUNT_LINK_PROVIDER_UNAVAILABLE` | OpenAPI error code |
| `PaymentRail` enum `ACH \| WIRE \| RTP` | `ACH_PLUS \| RTGS` (ACH→ACH_PLUS, WIRE→RTGS, RTP folds into ACH_PLUS — REMOVE RTP) | enum members + values. Keep `INTERNAL_P2P` if present. |
| webhook `/webhooks/persona` | `/webhooks/kyc` | OpenAPI path |
| webhook `/webhooks/plaid` | `/webhooks/account-link` | OpenAPI path |
| webhook `/webhooks/stripe` | `/webhooks/payments` | OpenAPI path |
| webhook `/webhooks/lithic` | `/webhooks/card` | OpenAPI path |
| `processor_token_ref`, `issuer_card_ref` | UNCHANGED (already neutral) | — |

## Vendor names in comments/docstrings
Neutralize Stripe/Plaid/Lithic/Persona/Jumio in code comments and docstrings to the
role abstractions (payment processor / account-linking provider / eKYC provider /
card issuer-processor); provider is procurement/TBD; eKYC has the ХУР/XYP note. The
existing "MARKET NOTE / kept verbatim from 04, awaiting the requirements change"
comments should be UPDATED to "migrated to match 04 (DEC-5 / rails run)". Do NOT
invent a Mongolian vendor.

## The gate coupling (critical)
- `app/db/check_migration.py` asserts the migration DDL EQUALS the ORM metadata DDL.
  So a column/enum rename MUST be applied in BOTH the model AND `migrations/versions/0001_initial.py`, or the gate FAILS. Change them together.
- `app/db/check_models.py` (ORM gate) must stay PASS.
- `openapi/validate.py` (OpenAPI assemble+validate+$ref-resolution) must stay PASS.
- `pytest` must stay green (update any test/fixture that references an old name).
- The generated bundle `openapi/openapi.yaml` is gitignored — edit the SOURCE files under `openapi/{paths,schemas,params}/`, never the bundle.

## Scope split
- **ORM + migration + tests** (one agent — they are gate-coupled): `app/models/*.py` (identity.py, payments.py, cards.py + any other), `migrations/versions/0001_initial.py`, `tests/`.
- **OpenAPI source** (separate agent — disjoint dir, own gate): `openapi/paths/*.yaml`, `openapi/schemas/*.yaml`, `openapi/params/*.yaml`.

## Rules
- Rename EXACTLY per the table; same old name → same new name everywhere.
- No money as float (non-negotiable) — untouched here anyway.
- Run the relevant gate(s) before finishing; report PASS with counts.
- Handoff: every rename (old→new+file), gate outputs, confirm no unrelated change.
