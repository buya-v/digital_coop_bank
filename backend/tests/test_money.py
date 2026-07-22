"""Unit tests for the money non-negotiable. No DB, no framework — runs anywhere."""
import pytest

from app.money import Money, MoneyError


def test_integer_minor_units_only():
    assert Money(500).minor_units == 500
    assert Money.zero().minor_units == 0


def test_from_tugrik_scales_to_minor_units():
    assert Money.from_tugrik(5).minor_units == 500
    assert Money.from_tugrik(1_250_000).minor_units == 125_000_000


def test_no_float_construction():
    # The whole point: a float must never become money.
    with pytest.raises(MoneyError):
        Money(5.0)  # type: ignore[arg-type]
    with pytest.raises(MoneyError):
        Money.from_tugrik(5.5)  # type: ignore[arg-type]


def test_bool_is_not_money():
    # bool is an int subclass; guard against True/False silently becoming amounts.
    with pytest.raises(MoneyError):
        Money(True)  # type: ignore[arg-type]


def test_from_str_is_exact():
    assert Money.from_str("1250000.00").minor_units == 125_000_000
    assert Money.from_str("1,250,000").minor_units == 125_000_000
    assert Money.from_str("-5.50").minor_units == -550


def test_from_str_rejects_excess_precision():
    with pytest.raises(MoneyError):
        Money.from_str("1.005")  # 3 dp > ISO 2 minor units


def test_from_str_rejects_scientific_notation():
    with pytest.raises(MoneyError):
        Money.from_str("1e6")


def test_exact_arithmetic():
    assert (Money(500) + Money(250)).minor_units == 750
    assert (Money(500) - Money(750)).minor_units == -250
    assert (-Money(500)).minor_units == -500


def test_arithmetic_requires_money():
    with pytest.raises(MoneyError):
        Money(500) + 250  # type: ignore[operator]


def test_display_is_whole_tugrik_postfix():
    assert Money.from_tugrik(1_250_000).format() == "1,250,000₮"
    assert str(Money.from_tugrik(8_000)) == "8,000₮"


def test_confirmed_anchor_values_render():
    # The product-owner-confirmed limits from the currency policy run.
    assert Money.from_tugrik(550_000).format() == "550,000₮"      # AML step-up
    assert Money.from_tugrik(1_150_000).format() == "1,150,000₮"  # P2P velocity
    assert Money.from_tugrik(10_000).format() == "10,000₮"        # share par (provisional)
