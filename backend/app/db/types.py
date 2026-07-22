"""Custom SQLAlchemy column types that enforce the project's non-negotiables.

`MoneyMinor` is the only correct way to store money in the schema. It stores a
BIGINT count of minor units (never a float, never NUMERIC-as-float) and binds to
the `Money` value object from `app.money`, so a float can never reach a money
column even by accident — the non-negotiable is enforced at the ORM boundary.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import BigInteger, Dialect
from sqlalchemy.types import TypeDecorator

from app.money import Money, MoneyError


class MoneyMinor(TypeDecorator):
    """A money column: BIGINT minor units in the DB, `Money` in Python.

    - DB side: BIGINT (integer minor units). No float, no NUMERIC.
    - Python side: `Money`. Binding anything that is not `Money` (a float, a
      bare int, a Decimal) raises — you must construct `Money` explicitly.
    """

    impl = BigInteger
    cache_ok = True

    def process_bind_param(self, value: Optional[Money], dialect: Dialect) -> Optional[int]:
        if value is None:
            return None
        if not isinstance(value, Money):
            raise MoneyError(
                f"money columns take a Money value, not {type(value).__name__} "
                f"({value!r}) — construct Money explicitly, never from a float"
            )
        return value.minor_units

    def process_result_value(self, value: Optional[int], dialect: Dialect) -> Optional[Money]:
        if value is None:
            return None
        return Money(int(value))
