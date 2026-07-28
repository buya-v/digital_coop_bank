"""Application configuration.

Deliberately minimal for the scaffold. Real settings (DB URL, secrets) come from
the environment — never hard-coded, never committed. Data-residency constraints
(CLAUDE.md blocking question #3) mean the deployment target is operator-chosen,
so nothing here assumes a cloud or region.
"""
from __future__ import annotations

import copy
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Digital Coop Bank API"
    # Semantic version of the running service, not of the requirements baseline.
    version: str = "0.0.1"
    environment: str = os.environ.get("DCB_ENV", "development")
    # DB URL is read at runtime by the (not-yet-present) persistence layer.
    database_url: str = os.environ.get("DATABASE_URL", "")


def get_settings() -> Settings:
    return Settings()


# --- Common-bond eligibility rules (config path `eligibility.common_bond_rules`) --
#
# The US-1.3 common-bond eligibility check is CONFIG-DRIVEN by mandate: an SCC is
# lawful only for a defined common bond (CLAUDE.md blocking question #1), but the
# PRODUCT has NOT chosen WHICH bond — employer, professional association, or
# aimag/district. So the engine (`app/services/eligibility.py`) evaluates the
# applicant's answers against THIS rule set rather than a hard-coded bond, and the
# eventual narrowing (once the PO picks a bond) is a CONFIG change here, not code.
#
# Shape (read by the engine; deliberately data, not Python objects, so it can later
# be sourced verbatim from a ConfigurationParameter row — US-12.5, NOT built now):
#   version: str            identifies the rule set recorded on the draft outcome
#   match:   "ALL" | "ANY"  ALL = every rule must pass (the sensible default)
#   rules:   list of        { id, field, operator, value, remediation }
#     - id          criterion identifier surfaced in `failed_criteria`
#     - field       key looked up in the applicant's `eligibility_answers`
#     - operator    one of: equals | in | gte | lte
#     - value       the expected value / bound / allowed set for the operator
#     - remediation applicant-facing guidance surfaced in `remediation` on failure
#
# The DEFAULT set is bond-NEUTRAL on purpose: it asks the applicant to DECLARE
# which of the three lawful bond categories they claim and to AFFIRM membership in
# it, plus the age-of-capacity floor — it does NOT name a specific employer or
# aimag. Narrowing `bond_type`'s allowed set (or pinning a single value) later is
# the config edit that scopes the product to the chosen bond.
ELIGIBILITY_COMMON_BOND_RULES: dict[str, object] = {
    "version": "common-bond-default-v1",
    "match": "ALL",
    "rules": [
        {
            "id": "AGE_OF_CAPACITY",
            "field": "age",
            "operator": "gte",
            "value": 18,
            "remediation": (
                "Members must be at least 18 years old to join the cooperative."
            ),
        },
        {
            "id": "BOND_TYPE_DECLARED",
            "field": "bond_type",
            "operator": "in",
            "value": ["EMPLOYER", "ASSOCIATION", "AIMAG_DISTRICT"],
            "remediation": (
                "Select the common bond you share with the cooperative: a shared "
                "employer, a professional association, or an aimag/district."
            ),
        },
        {
            "id": "COMMON_BOND_AFFIRMED",
            "field": "bond_affirmation",
            "operator": "equals",
            "value": True,
            "remediation": (
                "Confirm that you belong to the cooperative's common-bond group."
            ),
        },
    ],
}


def get_common_bond_rules() -> dict[str, object]:
    """Return the active common-bond rule set (`eligibility.common_bond_rules`).

    A deep copy is returned so callers (the engine) cannot mutate the shared
    default in place. This is the single seam a later ConfigurationParameter-backed
    loader (US-12.5) would replace — the engine only ever sees a plain data shape.
    """
    return copy.deepcopy(ELIGIBILITY_COMMON_BOND_RULES)
