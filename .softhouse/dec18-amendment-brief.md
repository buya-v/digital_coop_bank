# DEC-18 amendment brief — currency TYPE flip USD → MNT

Single source of truth for the DEC-18 amendment run. The market is Mongolia
(CLAUDE.md); the individual amounts were already migrated to ₮ in run
20260724-currency-apply. This run flips the currency **type declarations** and
fixes a few minor-units literals the amount pass missed. It does NOT re-migrate
amounts and does NOT touch vendor names (a later run).

## Canonical amended text (use verbatim for consistency across docs)

**DEC-18 normative statement (01 §6, the row) — replace the USD wording with:**
> All monetary amounts are denominated in Mongolian tögrög (MNT; ISO 4217 alpha `MNT`, numeric `496`; 2 minor units). Stored as integer minor units; displayed as whole tögrög with postfix `₮` and thousands separators (e.g. `1,250,000₮`). Supersedes the original USD denomination (market is Mongolia — see project context). **Transitional exceptions:** a bounded, individually-marked set of values remains in USD pending downstream decisions — KPI/AUM targets (KPI re-baselining), round-up amounts (round-up denomination), the loan-installment example (rate model), and community-funding program caps (program budget).

**01 canonical-term row (01:406) `| \`USD\`, integer minor units |` →**
> `| MNT (496), integer minor units | Money representation (DEC-18). | floats, unstated currency |`

**Doc-level convention lines (01:98, 02:11, 02:182, 03:473, 05:14) — replace the USD clause with:**
> All amounts MNT (₮, integer minor units, ISO 4217 numeric 496), displayed whole tögrög (DEC-18). A bounded set of values remains in USD pending downstream decisions, each explicitly marked.
- 02:182 / 03:473 phrase "FX/multi-currency out of scope (USD only, DEC-18)" → "FX/multi-currency out of scope (MNT only, DEC-18)".
- 05:14 "regulated, USD, fiat banking" → "regulated, MNT, fiat banking".

## 04 schema / API surface (currency code + missed minor-units literals)
- Currency-type prose (04:9, 110, 209, 221, 750): every `USD` currency code → `MNT`. At 04:9 the `Money` note "implicit currency `USD`" → "implicit currency `MNT`"; the fixed `currency` column "fixed to `USD`" → "fixed to `MNT`".
- Schema/API JSON examples `"currency":"USD"` (04:776, 04:781) → `"currency":"MNT"`.
- **MISSED minor-units par literals (currency-apply miss — no `$`, regex skipped them). The par is 10,000₮ = 1,000,000 minor units (MNT has 2 minor digits):**
  - 04:776 `amount:2500` → `amount:1000000`; `par_value:2500` → `par_value:1000000`.
  - 04:781 `redemption:{amount:2500}` → `redemption:{amount:1000000}`.
  - 05:1084 "configured par value (2500 cents, DEC-11)" → "configured par value (1,000,000 minor units = 10,000₮, DEC-11)".
  Flag these in the handoff as a corrected currency-apply miss.

## OUT OF SCOPE for this run (do NOT touch)
- Vendor names: `Stripe`, `Stripe Elements`, `payment_token (Stripe)`, "debit Stripe clearing" (04:776, 05:1084) — a later vendor-removal run.
- The residual HELD USD amounts (KPIs, round-ups, $88.20, program caps) — they STAY USD; the DEC-18 transitional-exceptions clause now explicitly covers them. Do not convert them.
- 06 (ledger addendum) — deferred (controller rewrite pending). Its 06:330 "USD minor units" stays until that rewrite.
- 00 — separate Mongolia rewrite.

## Rules
- Whole-tögrög notation `1,250,000₮`; integer minor units in schema literals (no float/decimal).
- Preserve document headers, DEC-n / US-n.n / E-n IDs, table structure.
- DEC-18 is normative in 01 §6; other docs REFERENCE it, they do not redefine it — keep wording consistent with the canonical text above.
- Run `.softhouse/verify-docs.sh`; HARD must stay 0. USD DRIFT should DROP slightly (the three 2500 literals were not `$`-counted, so drift moves little; the point is type-coherence, not the drift number).
- Handoff: list every declaration flipped, every literal fixed, and confirm no vendor name or held amount was touched.
