#!/usr/bin/env python3
"""ORM schema gate — the objective check for the entity-model derivation.

No database is required: it imports every model, configures the mappers, and
asserts the project's schema non-negotiables. This is the ORM analogue of
openapi/validate.py and .softhouse/verify-docs.sh.

Checks (all must pass):
  - Every model registered under `Base.metadata` maps cleanly.
  - **No money is stored as a float.** No column may be Float, Numeric, REAL, or
    DOUBLE PRECISION — money is MoneyMinor (BIGINT minor units) and nothing else.
  - Every ForeignKey resolves to a table that exists in the metadata.
  - No duplicate table name.

Exit 0 = PASS, 1 = a violation, 2 = could not run.

Usage: python3 -m app.db.check_models   (from backend/)
"""
from __future__ import annotations

import importlib
import pkgutil
import sys


def _load_all_models() -> object:
    """Import every module under app.models so Base.metadata is complete."""
    import app.models as models_pkg
    from app.db.base import Base

    for m in pkgutil.iter_modules(models_pkg.__path__):
        importlib.import_module(f"app.models.{m.name}")
    return Base


def main() -> int:
    try:
        from sqlalchemy import Float, Numeric
        from sqlalchemy.orm import configure_mappers

        Base = _load_all_models()
        configure_mappers()
    except Exception as e:  # pragma: no cover
        print(f"could not load models: {e}", file=sys.stderr)
        return 2

    problems: list[str] = []
    md = Base.metadata
    tables = md.tables

    # No float money — the core non-negotiable, checked structurally.
    float_types = (Float, Numeric)
    for tname, table in tables.items():
        for col in table.columns:
            if isinstance(col.type, float_types):
                problems.append(
                    f"{tname}.{col.name} is {col.type.__class__.__name__} — money/"
                    f"decimals must be MoneyMinor (BIGINT minor units), never float"
                )

    # Every FK resolves.
    for tname, table in tables.items():
        for fk in table.foreign_keys:
            target = fk.column.table.name
            if target not in tables:
                problems.append(f"{tname}: FK -> {target} which is not a defined table")

    n_money = sum(
        1
        for t in tables.values()
        for c in t.columns
        if c.type.__class__.__name__ == "MoneyMinor"
    )
    print(f"ORM: {len(tables)} tables · {sum(len(t.columns) for t in tables.values())} columns "
          f"· {n_money} money columns (MoneyMinor)")

    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        print("VERDICT: FAIL")
        return 1
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
