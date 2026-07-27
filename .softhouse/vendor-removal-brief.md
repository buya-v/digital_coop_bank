# Vendor-removal brief — Stripe / Plaid / Lithic / Persona / Jumio → role-neutral

Single source of truth for the vendor-removal run. CLAUDE.md: these US vendors are
assumed and are NOT the Mongolian market, and they leaked into schema field names
and error codes — so removal is a REQUIREMENTS change, not "an integration change"
(the docs' claim to the contrary is FALSE and must be corrected). Mongolia vendors
are NOT chosen — do NOT invent one; use role-neutral abstractions and mark the
concrete provider a procurement/TBD decision. Honesty rule applies.

Scope this run = REQUIREMENTS DOCS 01-05 only. (The backend code carries the same
vendor field names verbatim and will be synced in a SEPARATE follow-up run — this
brief's rename table is the canonical target for both.)

## Vendor → role abstraction (prose)
| vendor | role-neutral replacement |
|---|---|
| Stripe | the payment/card processor (card & wallet share-purchase collection) |
| Plaid | the account-linking provider (external bank-account linking/verification, open-banking) |
| Persona / Jumio | the eKYC / identity-verification provider (document OCR, liveness, screening) |
| Lithic | the card issuer-processor (cards — EP-5 remains entity-gated / not-buildable) |

For each, where a concrete vendor was named, say the provider is a **procurement
decision (TBD)**. For eKYC specifically, add that **ХУР/XYP state-register lookup is
the compliant-alternative candidate** (CLAUDE.md blocking-question 2 — biometric
eKYC is legally unresolved). Do NOT name a Mongolian vendor.

## Canonical IDENTIFIER renames (use these EXACT new names everywhere — docs now, code later)
| old (vendor-named) | new (neutral) | where |
|---|---|---|
| `persona_inquiry_id` | `kyc_inquiry_id` | 04:149, 04:763, 04:1063 (E-2 field, API, flow) |
| `plaid_item_ref` | `account_link_ref` | 04:273 (E-14 field) |
| `plaid_public_token` | `account_link_public_token` | 04:812 (API request) |
| `processor_token_ref` | `processor_token_ref` (UNCHANGED — already neutral) | 04:273 |
| enum `PLAID_INSTANT` (verification_method) | `INSTANT_LINK` | 04:275 |
| error `502 PLAID_UNAVAILABLE` | `502 ACCOUNT_LINK_PROVIDER_UNAVAILABLE` | 04:812 |
| `issuer_card_ref` | `issuer_card_ref` (UNCHANGED — neutral; Lithic name is only in prose) | cards |
| webhook `/webhooks/persona` | `/webhooks/kyc` | 04:976, 04:991 |
| webhook `/webhooks/plaid` | `/webhooks/account-link` | 04:981, 04:1005 |
| webhook `/webhooks/stripe` | `/webhooks/payments` | 04:977, 04:995 |
| webhook `/webhooks/lithic` | `/webhooks/card` | 04:978, 04:979, 04:1010 |

## Prose / diagram replacements
- "via Persona" → "via the eKYC provider"; "Persona inquiry" → "KYC inquiry"; "Persona webhook" → "KYC webhook"; "Persona integration" → "eKYC-provider integration"; "Persona evidence pack" → "KYC evidence pack".
- "via Stripe" → "via the payment processor"; "Stripe (card/wallet)" → "the payment processor (card/wallet)"; "Stripe webhook/integration/clearing" → "payment-processor webhook/integration/clearing".
- "via Plaid" / "linked via Plaid" → "via the account-linking provider"; "Plaid webhook" → "account-link webhook".
- Mermaid nodes: `PERSONA[Persona eKYC]` → `KYC[eKYC provider]`; `PLAID[Plaid]` → `LINK[Account-linking provider]`; any Stripe/Lithic node likewise role-named.
- Lithic references → "the card issuer-processor".

## DEC-5 amendment (01:361 — normative; and its references)
DEC-5 currently NAMES Persona as the KYC vendor and claims Jumio substitution is
"an integration change, not a requirements change." AMEND DEC-5 to:
- name the **eKYC provider as a procurement decision (TBD)**, role-defined (document
  OCR, liveness, screening), with **ХУР/XYP state-register lookup the compliant-
  alternative candidate** (blocking-question 2, biometric eKYC unresolved);
- **CORRECT the false claim**: because vendor names leaked into schema field names and
  error codes, vendor substitution IS a requirements change (this run makes the
  fields vendor-neutral so that going forward it can be an integration change).
- Keep DEC-5's ID and meaning (KYC provider selection); only remove the named vendor.
- DEC-5 REFERENCES elsewhere stay as "DEC-5" (the ID); only the definition changes.

## OUT OF SCOPE
- **06** (ledger addendum — controller rewrite pending) and **00** — leave their vendor refs (residual).
- Backend CODE (models/migration/OpenAPI) — a SEPARATE follow-up run adopts this
  rename table (the code already flags these fields as awaiting the requirements change).
- Do NOT change payment-rail terms (already migrated) or monetary amounts.

## Rules
- Apply by role/context. Preserve headers, DEC-n/US-n/EP-n/E-n IDs, table structure,
  and every NON-vendor field name.
- Rename a field name identically everywhere it appears (cross-doc consistency).
- Do NOT invent a Mongolian vendor; unknown provider = "procurement/TBD".
- Run `.softhouse/verify-docs.sh`: HARD stays 0; vendor DRIFT should DROP sharply.
- Handoff: list every vendor prose ref changed (old→new), every IDENTIFIER renamed
  (old→new+location), the DEC-5 amendment, and confirm no rail term / amount / non-
  vendor field was touched.
