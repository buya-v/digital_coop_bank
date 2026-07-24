"""Migration <-> ORM drift gate — offline, no database required.

Renders the FULL DDL implied by `Base.metadata` (importing every model first,
via the same `app.db.check_models._load_all_models` used by the ORM gate)
using SQLAlchemy's `create_mock_engine`: a fake engine that compiles every DDL
statement `MetaData.create_all` would send to a Postgres connection, without
ever opening a socket. This yields the model-derived CREATE TYPE / CREATE
TABLE / ALTER TABLE (use_alter FK) statements as SQLAlchemy would emit them.

That set is compared against the hand-authored `_UP` list of DDL strings in
`migrations/versions/0001_initial.py` — the migration's INTENDED DDL. (`0001`
was itself produced by this same mock-engine technique; see its docstring.)

Both sides are normalised for INCIDENTAL formatting only — leading/trailing
whitespace, runs of internal whitespace (tabs vs single-line rendering), and
a trailing semicolon — never for content. A real structural drift (a column,
table, type, or constraint added or removed on either side) still produces a
distinct normalised string, so the sets compare UNEQUAL and the gate fails.

Exit 0 = PASS (statement sets match), 1 = drift found, 2 = could not run.

Usage: python -m app.db.check_migration   (from backend/)
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from typing import Any

from app.db.base import Base
from app.db.check_models import _load_all_models

# backend/app/db/check_migration.py -> parents[2] == backend/
_MIGRATION_PATH = (
    Path(__file__).resolve().parents[2] / "migrations" / "versions" / "0001_initial.py"
)

_WHITESPACE_RE = re.compile(r"\s+")


def render_model_ddl() -> list[str]:
    """Render Base.metadata's full DDL offline via a mock engine. No DB opened.

    `create_mock_engine` never connects anywhere: the URL is used only to
    select the Postgres dialect, and `_dump` receives each compiled DDL
    statement in place of it being executed.
    """
    from sqlalchemy import create_mock_engine

    statements: list[str] = []

    def _dump(sql: Any, *multiparams: Any, **params: Any) -> None:
        statements.append(str(sql.compile(dialect=engine.dialect)))

    engine = create_mock_engine("postgresql://", _dump)
    _load_all_models()  # import side effect: populates Base.metadata
    Base.metadata.create_all(engine, checkfirst=False)
    return statements


def read_migration_ddl(path: Path = _MIGRATION_PATH) -> list[str]:
    """Import migrations/versions/0001_initial.py and read its `_UP` DDL list.

    Imported by file path (it lives outside any package Alembic puts on
    sys.path by default) so this works standalone, offline, from `backend/`.
    """
    spec = importlib.util.spec_from_file_location("_migration_0001_initial", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load migration module at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    up = getattr(module, "_UP", None)
    if not isinstance(up, list):
        raise TypeError(f"{path} has no `_UP` list of DDL statements")
    return list(up)


def normalize_statement(stmt: str) -> str:
    """Collapse incidental formatting so structurally-identical DDL compares
    equal regardless of how it was rendered.

    Collapsed (safe — never changes meaning): leading/trailing whitespace;
    every run of internal whitespace (spaces, tabs, newlines — e.g. the
    mock engine's pretty-printed, tab-indented `CREATE TABLE` vs a
    hand-formatted one) down to a single space; one trailing semicolon.

    NOT touched: keyword/identifier case, identifier names, column or
    constraint order within a statement, or any other SQL token. A real
    drift (an added/removed/renamed column, table, type, or constraint)
    still yields a distinct string after normalisation.
    """
    s = stmt.strip()
    s = _WHITESPACE_RE.sub(" ", s)
    s = s.rstrip(";").strip()
    return s


def compare(
    model_stmts: list[str], migration_stmts: list[str]
) -> tuple[bool, set[str], set[str]]:
    """Normalise both statement lists into sets and compare.

    Returns (matches, only_in_model, only_in_migration).
    """
    model_set = {normalize_statement(s) for s in model_stmts}
    migration_set = {normalize_statement(s) for s in migration_stmts}
    return model_set == migration_set, model_set - migration_set, migration_set - model_set


def main() -> int:
    try:
        model_stmts = render_model_ddl()
        migration_stmts = read_migration_ddl()
    except Exception as e:  # noqa: BLE001 — CLI entrypoint boundary, report and exit 2
        print(f"could not run migration gate: {e}", file=sys.stderr)
        return 2

    matches, only_model, only_migration = compare(model_stmts, migration_stmts)
    # Multiset guard: set comparison alone would pass a migration that DUPLICATES
    # a statement (140 lines collapsing to the same 139-member set). Require the
    # raw counts to agree so an accidental duplicate is caught offline, not only
    # by the downstream Postgres apply.
    counts_match = len(model_stmts) == len(migration_stmts)

    print(
        f"models: {len(model_stmts)} DDL statements · "
        f"migration: {len(migration_stmts)} DDL statements"
    )

    if not counts_match:
        print(
            f"  statement COUNT mismatch: {len(model_stmts)} model vs "
            f"{len(migration_stmts)} migration (duplicate or missing statement)"
        )
        print("VERDICT: FAIL")
        return 1

    if not matches:
        if only_model:
            print(f"  only in ORM metadata, missing from migration ({len(only_model)}):")
            for s in sorted(only_model):
                print(f"    - {s}")
        if only_migration:
            print(f"  only in migration, not derivable from current models ({len(only_migration)}):")
            for s in sorted(only_migration):
                print(f"    + {s}")
        print("VERDICT: FAIL")
        return 1

    print(f"{len(model_stmts)} statements match — migration is in lockstep with the models")
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
