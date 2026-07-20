#!/usr/bin/env bash
# Digital Coop Bank — requirements invariant checker.
#
# This project has no application code, so "UAT" means: do the requirements
# documents still satisfy the non-negotiables in CLAUDE.md?
#
# Two kinds of check:
#   HARD  — must be zero. Any hit is a failure.
#   DRIFT — migration-in-progress counts. Must not INCREASE against the
#           baseline in .softhouse/baseline.txt. Decreasing is progress.
#
# Usage:
#   .softhouse/verify-docs.sh              # check
#   .softhouse/verify-docs.sh --baseline   # rewrite baseline from current state
#
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 2

DOCS="idea-lab/final_requirements"
BASELINE=".softhouse/baseline.txt"
fail=0

c() { # c <pattern> [extra-grep-args...] -> count of matching lines
  local pat="$1"; shift
  grep -rEoh "$pat" "$DOCS"/*.md "$@" 2>/dev/null | wc -l | tr -d ' '
}

hard() { # hard <label> <count> — must be 0
  local label="$1" n="$2"
  if [ "$n" -eq 0 ]; then
    printf "  PASS  %-42s %s\n" "$label" "0"
  else
    printf "  FAIL  %-42s %s\n" "$label" "$n"
    fail=1
  fi
}

drift() { # drift <key> <label> <count> — must not exceed baseline
  local key="$1" label="$2" n="$3" base
  base=$(grep -E "^${key}=" "$BASELINE" 2>/dev/null | cut -d= -f2)
  if [ -z "${base:-}" ]; then
    printf "  NEW   %-42s %s (no baseline)\n" "$label" "$n"
    return
  fi
  if [ "$n" -le "$base" ]; then
    local delta=$((base - n))
    if [ "$delta" -gt 0 ]; then
      printf "  PASS  %-42s %s  (-%s from %s)\n" "$label" "$n" "$delta" "$base"
    else
      printf "  PASS  %-42s %s  (= baseline)\n" "$label" "$n"
    fi
  else
    printf "  FAIL  %-42s %s  (+%s over baseline %s)\n" "$label" "$n" "$((n - base))" "$base"
    fail=1
  fi
}

# --- gather ----------------------------------------------------------------
# Vendor names: exclude "Persona" used as the user-persona noun (P-1..P-5,
# "Persona A", "target persona", etc). Only vendor-context hits count.
n_vendor=$(grep -rEoih '\b(stripe|plaid|lithic)\b|persona (inquiry|webhook|api|returns|watchlist)|via persona' "$DOCS"/*.md 2>/dev/null | wc -l | tr -d ' ')
# Insurance claims about member money — exclude peer-guarantee language.
n_insured=$(grep -rEoih 'deposit[s]? (are |is )?insured|savings (are |is )?insured|fdic|ncua|deposit insurance corporation' "$DOCS"/*.md 2>/dev/null | wc -l | tr -d ' ')
n_stale_thresh=$(c 'MNT ?3(,000,000|m\b| ?million)')
n_snake_name=$(c 'first_name|last_name')
# Money types: match float/double-precision/DECIMAL(p,s) as a TYPE, but not the
# English word "double" (double-entry, double-vote, double-count), and not the
# migration table line that records DECIMAL as the *rejected* representation.
n_float=$(grep -rEn 'DECIMAL\([0-9]+,[0-9]+\)|\bfloat\b|double precision' "$DOCS"/*.md 2>/dev/null \
          | grep -viE 'minor units|rejected|superseded' | wc -l | tr -d ' ')
n_usd=$(c '\$[0-9][0-9,]*')
n_rails=$(c '\b(ACH|FedNow|SEPA)\b')
n_tz=$(c 'UTC\+8\b|UTC\+08:00 only')

echo "Digital Coop Bank — requirements invariants"
echo
echo "HARD (must be zero):"
hard  "US deposit-insurance regime (FDIC/NCUA)"  "$n_insured"
hard  "stale MNT 3m RTGS threshold"            "$n_stale_thresh"
hard  "first_name / last_name"                 "$n_snake_name"
hard  "float / double / DECIMAL money types"   "$n_float"
hard  "hardcoded UTC+8"                        "$n_tz"
echo
echo "DRIFT (must not increase — Mongolia migration in progress):"
drift usd    "USD amounts"                     "$n_usd"
drift rails  "US payment rails"                "$n_rails"
drift vendor "US vendor references"            "$n_vendor"
echo

# --- baseline mode ---------------------------------------------------------
if [ "${1:-}" = "--baseline" ]; then
  {
    echo "# Regenerated $(git log -1 --format=%h 2>/dev/null || echo nogit)"
    echo "usd=$n_usd"
    echo "rails=$n_rails"
    echo "vendor=$n_vendor"
  } > "$BASELINE"
  echo "Baseline written to $BASELINE"
  exit 0
fi

if [ "$fail" -eq 0 ]; then
  echo "VERDICT: PASS"
  exit 0
else
  echo "VERDICT: FAIL"
  exit 1
fi
