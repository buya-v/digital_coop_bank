"""Migration <-> ORM drift gate test — no DB needed (mock-engine DDL diff only).

Calls the comparison function directly (not the `python -m` process) so a
failure reports through normal pytest assertion output.
"""
import pytest

pytest.importorskip("sqlalchemy", reason="sqlalchemy installed in CI")
pytest.importorskip("alembic", reason="alembic installed in CI")

from app.db.check_migration import compare, read_migration_ddl, render_model_ddl


def test_migration_matches_models():
    model_stmts = render_model_ddl()
    migration_stmts = read_migration_ddl()

    matches, only_model, only_migration = compare(model_stmts, migration_stmts)

    assert matches, (
        f"migrations/versions/0001_initial.py has drifted from the ORM metadata\n"
        f"only in ORM metadata (missing from migration): {sorted(only_model)}\n"
        f"only in migration (not derivable from current models): {sorted(only_migration)}"
    )


def test_migration_ddl_is_nonempty():
    # Guards against a vacuous pass (e.g. both sides accidentally empty).
    assert len(render_model_ddl()) > 0
    assert len(read_migration_ddl()) > 0
