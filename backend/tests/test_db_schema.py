"""ORM schema tests — no DB needed (metadata + type enforcement only)."""
import pytest

pytest.importorskip("sqlalchemy", reason="sqlalchemy installed in CI")

from sqlalchemy import Float, Numeric  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.check_models import _load_all_models  # noqa: E402
from app.db.types import MoneyMinor  # noqa: E402
from app.money import Money, MoneyError  # noqa: E402


def test_all_models_map():
    from sqlalchemy.orm import configure_mappers

    _load_all_models()
    configure_mappers()  # raises if any mapping is broken
    assert Base.metadata.tables  # at least some tables registered


def test_no_float_money_columns():
    """The core non-negotiable, checked structurally: no money as float/numeric."""
    _load_all_models()
    offenders = [
        f"{t}.{c.name}"
        for t, table in Base.metadata.tables.items()
        for c in table.columns
        if isinstance(c.type, (Float, Numeric))
    ]
    assert offenders == [], f"money must be MoneyMinor, not float: {offenders}"


def test_every_fk_resolves():
    _load_all_models()
    tables = Base.metadata.tables
    for tname, table in tables.items():
        for fk in table.foreign_keys:
            assert fk.column.table.name in tables, f"{tname}: dangling FK -> {fk.column.table.name}"


def test_money_type_rejects_float():
    t = MoneyMinor()
    with pytest.raises(MoneyError):
        t.process_bind_param(5.0, None)  # a float must never become money
    assert t.process_bind_param(Money.from_tugrik(10_000), None) == 1_000_000
    assert t.process_result_value(1_000_000, None) == Money.from_tugrik(10_000)


def test_ledger_core_defers_undecided_enums():
    """LedgerEntry.entry_type and Transaction.type must be String (deferred),
    NOT an invented enum — their value sets await the corrected ledger design."""
    from app.models.ledger import LedgerEntry, Transaction

    assert LedgerEntry.__table__.c.entry_type.type.__class__.__name__ == "String"
    assert Transaction.__table__.c.type.type.__class__.__name__ == "String"
