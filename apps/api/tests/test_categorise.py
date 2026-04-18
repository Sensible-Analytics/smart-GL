import os
import pytest

os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-dummy")
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")

from services.categorise import clean_description


def test_clean_description_strips_date():
    assert "BUNNINGS SYDNEY" == clean_description("BUNNINGS 00435 SYDNEY 15/04")


def test_clean_description_strips_long_numbers():
    result = clean_description("AMPOL FUEL 12345678 BROOKVALE")
    assert "12345678" not in result


def test_clean_description_strips_card_ref():
    result = clean_description("VISA GOOGLE WORKSPACE CARD 9234")
    assert "9234" not in result
    assert "GOOGLE WORKSPACE" in result


def test_clean_description_uppercase():
    result = clean_description("bunnings 00435")
    assert result == result.upper()


def test_clean_description_strips_direct_debit():
    result = clean_description("NETFLIX DIRECT DEBIT")
    assert "DIRECT DEBIT" not in result


def test_clean_description_strips_eftpos():
    result = clean_description("COLES EFTPOS 1234")
    assert "EFTPOS" not in result


def test_clean_description_strips_multiple_spaces():
    result = clean_description("BUNNINGS    WAREHOUSE")
    assert "  " not in result
