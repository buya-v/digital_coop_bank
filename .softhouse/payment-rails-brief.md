# Payment-rails migration brief — US rails → Mongolia

Single source of truth for the payment-rails run. Migrate US rail concepts to
Mongolia's actual payment system. Source: CLAUDE.md. Honesty rule applies — where
a Mongolian specific (e.g. a return-code catalogue) is NOT publicly known, say so
and mark it config/TBD; do NOT invent one.

## The Mongolian payment system (facts)
- **Банксүлжээ / Banksuljee = RTGS** (real-time gross settlement) for **large-value**
  transfers **above the threshold**.
- **ACH+** = domestic automated clearing for amounts **at or below the threshold**,
  **24/7** (so it also covers the "instant / real-time" retail case — there is no
  separate FedNow/RTP rail).
- **NETC** (National Electronic Transaction Center, a Bank of Mongolia entity) =
  **card** settlement/clearing.
- **Threshold = ₮5,000,000**, set by **Governor's order → treat as CONFIGURATION,
  never a hard-coded literal**. NEVER write "MNT 3m" / "₮3,000,000" as the RTGS
  threshold — the English Mongolbank page says 3m but the authoritative Mongolian
  page says 5m, and verify-docs.sh HARD-FAILS on the 3m value.
- **No SEPA, no Fedwire, no cross-border euro/USD rail.** FX/multi-currency is out
  of scope (MNT only). Cross-border is NOT in scope — do not invent a rail for it.

## Canonical mapping (apply BY CONTEXT, not blind replace)
| US term | Mongolia replacement |
|---|---|
| ACH (inbound/outbound, low-value, batch, same-day) | **ACH+** |
| wire / Fedwire (large-value) | **Banksüljee (RTGS)** — for amounts **> ₮5,000,000** |
| FedNow / RTP / "real-time rail" / "instant (external)" | **ACH+** (24/7); there is no separate real-time rail |
| SEPA / SEPA Instant | **remove** — not applicable; if the sentence needs a domestic instant rail, it is ACH+ |
| card network (Visa/Mastercard/Lithic settlement) | **NETC** |

## Canonical `rail` ENUM (04 owns it; other docs reference it)
`rail Enum INTERNAL_P2P | ACH | WIRE | RTP` → **`INTERNAL_P2P | ACH_PLUS | RTGS`**
- INTERNAL_P2P unchanged (internal ledger settlement).
- ACH → **ACH_PLUS**; WIRE → **RTGS**; RTP folds into ACH_PLUS (24/7), so the enum
  drops from 4 to 3 members. Update every `(ACH|WIRE|RTP)` occurrence to
  `(ACH_PLUS|RTGS)` and any prose enum list to match.

## Routing rule (state it wherever rail choice is described)
> External transfers route by amount against a **configurable threshold (₮5,000,000,
> set by Governor's order)**: **> threshold → Banksüljee (RTGS)**; **≤ threshold →
> ACH+ (24/7)**. The threshold is configuration (US-12.5), never hard-coded.

## Return codes — HONESTY (do not invent)
- US NACHA codes like **`R01`** are US-specific. Keep the human REASON
  ("insufficient-funds return") but REMOVE the `R01` literal. Add: "the specific
  return-code catalogue is the settlement operator's, carried as configuration —
  TBD pending the Bank-of-Mongolia settlement-agent selection." Do NOT fabricate a
  Mongolian return-code scheme.

## Scenario amounts where the rail distinction depends on amount (03 esp.)
Some scenarios pick "ACH vs wire" to show two rails. Under the ₮5m threshold a
sub-5m "wire" is actually ACH+, which would collapse the distinction. Where a
scenario needs to demonstrate the **RTGS** rail, **re-derive the large amount to
exceed ₮5,000,000** (e.g. a `2,500,000₮ wire` → `6,500,000₮ via Banksüljee (RTGS)`)
so the routing rule holds; keep the small one as ACH+. Flag each such amount change
as a rail-driven re-derivation (PO-confirmable). Do NOT leave a sub-threshold amount
labelled RTGS/Banksüljee — that is internally contradictory.

## Cards note
NETC/card references: migrate the terminology for record completeness, but EP-5
(Cards) remains **entity-gated / not-buildable** for an SCC (CLAUDE.md) — do not
imply it is buildable.

## OUT OF SCOPE this run
- **06** (ledger addendum — controller rewrite pending) and **00** (Mongolia rewrite)
  — leave their rail terms; they are the residual the gate still counts.
- Vendor names (Stripe/Plaid/Lithic/Persona) — the NEXT run. Do NOT remove them here.
- Do NOT change monetary amounts except the rail-driven re-derivation above.

## Rules
- Apply by context/role. Preserve headers, DEC-n/US-n/EP-n/F-n/E-n IDs, tables.
- The already-present `<!-- TODO(rails) -->` comment at 04:29 should be RESOLVED
  (apply the RTGS/ACH+/NETC change it describes, then remove the TODO).
- Whole-tögrög notation for any re-derived amount; no float.
- Run `.softhouse/verify-docs.sh`: HARD must stay 0 (esp. the 3m-threshold check —
  never introduce "3m"); rails DRIFT should DROP (ACH/FedNow/SEPA → ACH+/RTGS/NETC;
  note `ACH+` is explicitly NOT counted by the gate).
- Handoff: list every rail term changed (old→new + context), every amount re-derived
  for routing, every place you marked something TBD/config rather than inventing it.
