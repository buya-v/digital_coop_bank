"""Common-bond eligibility engine (US-1.3) — config-driven rule evaluation.

WHY config-driven (not a hard-coded bond): an SCC is lawful only for a defined
common bond (CLAUDE.md blocking question #1, PO provisional direction), but the
product has NOT yet chosen WHICH bond — employer, professional association, or
aimag/district. So this module is a small generic ENGINE that evaluates an
applicant's `eligibility_answers` against a rule set held in configuration
(`eligibility.common_bond_rules`, see `app.config.get_common_bond_rules`). The
eventual narrowing to one bond is a CONFIG edit, not a code change here.

Two layers live in this file:

- The PURE engine — `evaluate(answers, ruleset) -> EligibilityOutcome` plus its
  operators. No I/O, no session; deterministic and unit-testable in isolation.
- `EligibilityService` — orchestration that reuses the slice-1 foundation
  (`OnboardingApplicationRepository`, the bootstrap-token hash) to resolve the
  draft, guard the already-passed case, record the outcome on the draft's
  `onboarding_state`, and hand the outcome back to the router. It NEVER commits
  (the router owns the transaction boundary, slice-1 convention).

No money, no float, no KYC, no promotion — those are T2. `age` is compared as an
integer; a float or non-integer age is a malformed answer, not a low number.
"""
from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping

from sqlalchemy.orm import Session

from app.config import get_common_bond_rules
from app.models.identity import OnboardingApplication
from app.repositories.onboarding import OnboardingApplicationRepository

# Reuse the slice-1 bootstrap-token hash and timestamp helpers — one source of
# truth for how a raw resume token maps to the stored hash (a divergent copy here
# would silently break token resolution) and for the UTC instant format.
from app.services.onboarding import _hash_token, _now_iso


class EligibilityError(Exception):
    """Base for eligibility domain errors (mapped to HTTP by the router)."""


class EligibilityAnswersInvalid(EligibilityError):
    """An answer is present but the wrong TYPE for its rule (maps to 422).

    Distinct from a MISSING answer (which simply fails its criterion -> the
    applicant is ineligible, not malformed). Carries the offending field so the
    router can surface a per-field `details` entry in the uniform Error envelope.
    """

    def __init__(self, field: str, message: str) -> None:
        super().__init__(message)
        self.field = field
        self.message = message


class EligibilityAlreadyPassed(EligibilityError):
    """Eligibility already passed for this applicant (maps to 409).

    A PASSED check is terminal (409 ALREADY_CHECKED_PASSED per the contract); a
    previously FAILED check may be retried.
    """


class EligibilityConfigError(EligibilityError):
    """The rule set itself is malformed — a programmer/config defect, not user
    input. Never raised for the shipped default; guards a bad ConfigurationParameter
    once that loader exists."""


# --- Parsed rule shape -------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class _Rule:
    id: str
    field: str
    operator: str
    expected: object
    remediation: str


@dataclasses.dataclass(frozen=True)
class EligibilityOutcome:
    """Result of evaluating answers against a rule set (backs the response)."""

    eligible: bool
    failed_criteria: list[str]
    remediation: list[str]
    ruleset_version: str


# --- Operators ---------------------------------------------------------------
#
# Each operator is `(answer, expected, field) -> bool`. A type incompatibility
# between the answer and the operator raises `EligibilityAnswersInvalid` (a
# malformed answer, 422); a legitimate comparison that is simply false returns
# False (an unmet criterion -> ineligible).


def _require_int(answer: object, field: str) -> int:
    # `bool` is a subclass of `int`; a True/False supplied where a number is
    # expected is malformed, not the integer 1/0. `float` is rejected too — the
    # no-float non-negotiable applies even to an age comparison.
    if isinstance(answer, bool) or not isinstance(answer, int):
        raise EligibilityAnswersInvalid(
            field, f"answer for '{field}' must be an integer"
        )
    return answer


def _op_equals(answer: object, expected: object, field: str) -> bool:
    return bool(answer == expected)


def _op_in(answer: object, expected: object, field: str) -> bool:
    if not isinstance(expected, (list, tuple)):
        raise EligibilityConfigError(
            f"rule for '{field}' uses operator 'in' but its value is not a list"
        )
    return answer in expected


def _op_gte(answer: object, expected: object, field: str) -> bool:
    return _require_int(answer, field) >= _require_int(expected, field)


def _op_lte(answer: object, expected: object, field: str) -> bool:
    return _require_int(answer, field) <= _require_int(expected, field)


_OPERATORS: dict[str, Callable[[object, object, str], bool]] = {
    "equals": _op_equals,
    "in": _op_in,
    "gte": _op_gte,
    "lte": _op_lte,
}


# --- Pure engine -------------------------------------------------------------


def _parse_rules(ruleset: Mapping[str, object]) -> list[_Rule]:
    raw_rules = ruleset.get("rules")
    if not isinstance(raw_rules, (list, tuple)):
        raise EligibilityConfigError("rule set 'rules' must be a list")
    parsed: list[_Rule] = []
    for item in raw_rules:
        if not isinstance(item, Mapping):
            raise EligibilityConfigError("each rule must be an object")
        for key in ("id", "field", "operator"):
            if key not in item:
                raise EligibilityConfigError(f"rule is missing required key '{key}'")
        operator = str(item["operator"])
        if operator not in _OPERATORS:
            raise EligibilityConfigError(f"unknown operator '{operator}'")
        parsed.append(
            _Rule(
                id=str(item["id"]),
                field=str(item["field"]),
                operator=operator,
                expected=item.get("value"),
                remediation=str(item.get("remediation", "")),
            )
        )
    return parsed


def _rule_passes(rule: _Rule, answers: Mapping[str, object]) -> bool:
    # A missing answer fails the criterion (ineligible) — it is NOT malformed.
    if rule.field not in answers:
        return False
    operator = _OPERATORS[rule.operator]
    return operator(answers[rule.field], rule.expected, rule.field)


def evaluate(
    answers: Mapping[str, object], ruleset: Mapping[str, object]
) -> EligibilityOutcome:
    """Evaluate `answers` against `ruleset`; pure and deterministic.

    Raises `EligibilityAnswersInvalid` if an answer is the wrong type for its
    operator (malformed -> 422). Missing answers simply fail their criterion.
    `match == "ANY"` passes when at least one rule passes; the default `"ALL"`
    requires every rule to pass.
    """
    rules = _parse_rules(ruleset)
    version = str(ruleset.get("version", "unversioned"))
    match_mode = str(ruleset.get("match", "ALL")).upper()

    failed_criteria: list[str] = []
    remediation: list[str] = []
    passed_count = 0
    for rule in rules:
        if _rule_passes(rule, answers):
            passed_count += 1
        else:
            failed_criteria.append(rule.id)
            if rule.remediation:
                remediation.append(rule.remediation)

    if match_mode == "ANY":
        eligible = passed_count > 0
    elif match_mode == "ALL":
        eligible = not failed_criteria
    else:
        raise EligibilityConfigError(f"unknown match mode '{match_mode}'")

    return EligibilityOutcome(
        eligible=eligible,
        failed_criteria=failed_criteria,
        remediation=remediation,
        ruleset_version=version,
    )


# --- Orchestration service ---------------------------------------------------


class EligibilityService:
    """Runs the eligibility check for the applicant behind a bootstrap token and
    records the outcome on the draft. Reuses the slice-1 onboarding repository;
    never commits (the router does)."""

    def __init__(self, session: Session) -> None:
        self._repo = OnboardingApplicationRepository(session)

    def check_eligibility(
        self, resume_token: str, answers: Mapping[str, object]
    ) -> tuple[OnboardingApplication | None, EligibilityOutcome | None]:
        """Resolve the draft, evaluate, and record the outcome.

        Returns (None, None) if the token matches no draft (router -> 401).
        Raises `EligibilityAlreadyPassed` if a passed check already exists, or
        `EligibilityAnswersInvalid` on a malformed answer.
        """
        application = self._repo.get_by_resume_token_hash(_hash_token(resume_token))
        if application is None:
            return None, None

        state = dict(application.onboarding_state or {})
        existing = state.get("eligibility")
        if isinstance(existing, dict) and existing.get("eligible") is True:
            raise EligibilityAlreadyPassed()

        # Config-driven: the rule set is loaded from configuration, never inlined.
        outcome = evaluate(answers, get_common_bond_rules())

        checked_at = _now_iso()
        state["eligibility"] = {
            "eligible": outcome.eligible,
            "failed_criteria": list(outcome.failed_criteria),
            "ruleset_version": outcome.ruleset_version,
            "checked_at": checked_at,
        }
        kpi: dict[str, object] = dict(state.get("kpi_timestamps") or {})
        kpi["eligibility_checked_at"] = checked_at
        state["kpi_timestamps"] = kpi
        application.onboarding_state = state
        self._repo.update(application)
        return application, outcome
