"""Money as integer minor units — the project's core money non-negotiable, in code.

Encodes the rules that CLAUDE.md and 06_ledger_addendum.md §5.1 make non-negotiable:

  - Money is a signed integer count of MINOR UNITS. Never a float, never a
    binary/decimal fraction that can drift.
  - Currency is MNT (ISO 4217 numeric 496, 2 minor units) — the product-owner
    decision recorded in ADR 0001. Transacted as whole tugrik (the möngö
    subunit is obsolete in circulation) but stored to the ISO minor unit so the
    ledger reconciles exactly.
  - Constructing Money from a float is forbidden at the type level: there is no
    from-float path, because that is exactly how rounding drift enters a ledger.

This module deliberately has NO dependency on the web framework or the database
so it can be unit-tested with nothing installed (see backend/tests/test_money.py).
It runs on Python 3.9+ so it is verifiable on the current dev machine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ISO 4217 for the tugrik. See ADR 0001 and DEC-18 (post currency decision).
CURRENCY_CODE: Final[str] = "MNT"
CURRENCY_NUMERIC: Final[int] = 496
MINOR_UNITS: Final[int] = 2  # ISO retains 2; circulation is whole tugrik.
_MINOR_PER_MAJOR: Final[int] = 10 ** MINOR_UNITS


class MoneyError(ValueError):
    """Raised on any attempt to build or combine Money unsafely."""


@dataclass(frozen=True)
class Money:
    """A signed amount in MNT minor units. Immutable; arithmetic is exact.

    Always construct from an integer number of minor units, or via the explicit
    `from_tugrik` / `from_str` constructors. There is intentionally no
    `from_float` — floats do not belong in a money path.
    """

    minor_units: int
    currency: str = CURRENCY_CODE

    def __post_init__(self) -> None:
        if isinstance(self.minor_units, bool) or not isinstance(self.minor_units, int):
            # bool is an int subclass; reject it so True/False can't become money.
            raise MoneyError(
                f"minor_units must be an int (got {type(self.minor_units).__name__})"
            )
        if self.currency != CURRENCY_CODE:
            raise MoneyError(
                f"only {CURRENCY_CODE} is supported; got {self.currency!r}"
            )

    # --- constructors -----------------------------------------------------
    @classmethod
    def zero(cls) -> "Money":
        return cls(0)

    @classmethod
    def from_tugrik(cls, tugrik: int) -> "Money":
        """Build from a whole-tugrik integer (the everyday unit). 5 -> 500 minor."""
        if isinstance(tugrik, bool) or not isinstance(tugrik, int):
            raise MoneyError("from_tugrik requires a whole-tugrik int")
        return cls(tugrik * _MINOR_PER_MAJOR)

    @classmethod
    def from_str(cls, text: str) -> "Money":
        """Parse an exact decimal string like '1250000.00' or '1250000'.

        Rejects anything a float would silently accept (scientific notation,
        more than the ISO minor-unit precision). Exact string -> exact integer.
        """
        if not isinstance(text, str):
            raise MoneyError("from_str requires a string")
        s = text.strip().replace(",", "")
        neg = s.startswith("-")
        if neg:
            s = s[1:]
        if "." in s:
            major, minor = s.split(".", 1)
        else:
            major, minor = s, ""
        if not major.isdigit() or (minor and not minor.isdigit()):
            raise MoneyError(f"not an exact decimal amount: {text!r}")
        if len(minor) > MINOR_UNITS:
            raise MoneyError(
                f"more precision than {MINOR_UNITS} minor units: {text!r}"
            )
        minor = minor.ljust(MINOR_UNITS, "0")
        value = int(major) * _MINOR_PER_MAJOR + (int(minor) if minor else 0)
        return cls(-value if neg else value)

    # --- exact arithmetic -------------------------------------------------
    def __add__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.minor_units + other.minor_units)

    def __sub__(self, other: "Money") -> "Money":
        self._check(other)
        return Money(self.minor_units - other.minor_units)

    def __neg__(self) -> "Money":
        return Money(-self.minor_units)

    def _check(self, other: object) -> None:
        if not isinstance(other, Money):
            raise MoneyError("Money can only combine with Money")
        if other.currency != self.currency:
            raise MoneyError("currency mismatch")

    # --- rendering --------------------------------------------------------
    @property
    def tugrik(self) -> int:
        """Whole tugrik, truncated toward zero. For display only — not for math."""
        return abs(self.minor_units) // _MINOR_PER_MAJOR * (
            -1 if self.minor_units < 0 else 1
        )

    def format(self) -> str:
        """Local display: whole-tugrik, thousands-separated, postfix ₮.

        e.g. Money.from_tugrik(1_250_000).format() -> '1,250,000₮'
        Follows the Mongolian convention (postfix symbol, zero decimals shown)
        while the stored value keeps ISO minor-unit precision.
        """
        whole = self.minor_units // _MINOR_PER_MAJOR
        return f"{whole:,}₮"

    def __str__(self) -> str:
        return self.format()
