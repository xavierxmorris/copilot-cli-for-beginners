"""Tests for year input validation in books.py and utils.py."""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection, InvalidBookDataError
from utils import parse_year

CURRENT_YEAR = datetime.now().year


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def collection():
    return BookCollection()


# --- add_book year validation ---


class TestAddBookYearValidation:
    """Year validation at the domain layer (books.py)."""

    def test_valid_year(self, collection):
        book = collection.add_book("Dune", "Frank Herbert", 1965)
        assert book.year == 1965

    def test_year_one(self, collection):
        book = collection.add_book("Ancient Text", "Unknown", 1)
        assert book.year == 1

    def test_current_year(self, collection):
        book = collection.add_book("New Book", "Author", CURRENT_YEAR)
        assert book.year == CURRENT_YEAR

    def test_next_year_allowed(self, collection):
        book = collection.add_book("Forthcoming", "Author", CURRENT_YEAR + 1)
        assert book.year == CURRENT_YEAR + 1

    def test_year_zero_rejected(self, collection):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            collection.add_book("Book", "Author", 0)

    def test_negative_year_rejected(self, collection):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            collection.add_book("Book", "Author", -500)

    def test_far_future_rejected(self, collection):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            collection.add_book("Book", "Author", CURRENT_YEAR + 2)

    def test_very_large_year_rejected(self, collection):
        with pytest.raises(InvalidBookDataError):
            collection.add_book("Book", "Author", 99999)

    def test_rejected_book_not_added(self, collection):
        with pytest.raises(InvalidBookDataError):
            collection.add_book("Book", "Author", -1)
        assert len(collection.books) == 0


# --- parse_year validation ---


class TestParseYearValidation:
    """Year validation at the UI layer (utils.py)."""

    def test_valid_year_string(self):
        assert parse_year("1965") == 1965

    def test_current_year_string(self):
        assert parse_year(str(CURRENT_YEAR)) == CURRENT_YEAR

    def test_next_year_string(self):
        assert parse_year(str(CURRENT_YEAR + 1)) == CURRENT_YEAR + 1

    def test_non_numeric_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Invalid year"):
            parse_year("abc")

    def test_empty_string_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Invalid year"):
            parse_year("")

    def test_zero_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            parse_year("0")

    def test_negative_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            parse_year("-1")

    def test_far_future_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Year must be between"):
            parse_year(str(CURRENT_YEAR + 2))

    def test_float_rejected(self):
        with pytest.raises(InvalidBookDataError, match="Invalid year"):
            parse_year("1965.5")
