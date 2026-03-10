"""Comprehensive pytest tests for get_book_details.

Covers: valid input, empty strings, invalid year formats,
very long titles, and special characters in author names.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from utils import get_book_details


def _simulate_input(monkeypatch, inputs: list[str]):
    """Helper: mock sequential input() calls."""
    responses = iter(inputs)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(responses))


# --- Valid input ---


class TestValidInput:

    def test_basic_input(self, monkeypatch):
        _simulate_input(monkeypatch, ["Dune", "Frank Herbert", "1965"])
        title, author, year = get_book_details()
        assert title == "Dune"
        assert author == "Frank Herbert"
        assert year == 1965

    def test_strips_whitespace(self, monkeypatch):
        _simulate_input(monkeypatch, ["  Dune  ", "  Frank Herbert  ", "  1965  "])
        title, author, year = get_book_details()
        assert title == "Dune"
        assert author == "Frank Herbert"
        assert year == 1965

    def test_year_zero(self, monkeypatch):
        _simulate_input(monkeypatch, ["Title", "Author", "0"])
        _, _, year = get_book_details()
        assert year == 0

    def test_negative_year(self, monkeypatch):
        _simulate_input(monkeypatch, ["Ancient Text", "Unknown", "-500"])
        _, _, year = get_book_details()
        assert year == -500

    def test_returns_tuple(self, monkeypatch):
        _simulate_input(monkeypatch, ["T", "A", "2000"])
        result = get_book_details()
        assert isinstance(result, tuple)
        assert len(result) == 3


# --- Empty strings ---


class TestEmptyStrings:

    def test_empty_title(self, monkeypatch):
        _simulate_input(monkeypatch, ["", "Author", "2000"])
        title, author, year = get_book_details()
        assert title == ""
        assert author == "Author"
        assert year == 2000

    def test_empty_author(self, monkeypatch):
        _simulate_input(monkeypatch, ["Title", "", "2000"])
        title, author, year = get_book_details()
        assert title == "Title"
        assert author == ""

    def test_empty_year_defaults_to_zero(self, monkeypatch, capsys):
        _simulate_input(monkeypatch, ["Title", "Author", ""])
        _, _, year = get_book_details()
        assert year == 0
        output = capsys.readouterr().out
        assert "Invalid year" in output

    def test_all_empty(self, monkeypatch, capsys):
        _simulate_input(monkeypatch, ["", "", ""])
        title, author, year = get_book_details()
        assert title == ""
        assert author == ""
        assert year == 0

    def test_whitespace_only_title(self, monkeypatch):
        _simulate_input(monkeypatch, ["   ", "Author", "2000"])
        title, _, _ = get_book_details()
        assert title == ""

    def test_whitespace_only_year(self, monkeypatch, capsys):
        _simulate_input(monkeypatch, ["Title", "Author", "   "])
        _, _, year = get_book_details()
        assert year == 0
        assert "Invalid year" in capsys.readouterr().out


# --- Invalid year formats ---


class TestInvalidYearFormats:

    @pytest.mark.parametrize("bad_year", [
        "abc",
        "nineteen",
        "20.5",
        "2000AD",
        "!@#$",
        "1 9 6 5",
        "1,965",
    ])
    def test_non_numeric_year_defaults_to_zero(self, monkeypatch, capsys, bad_year):
        _simulate_input(monkeypatch, ["Title", "Author", bad_year])
        _, _, year = get_book_details()
        assert year == 0
        assert "Invalid year" in capsys.readouterr().out

    def test_float_year_rejected(self, monkeypatch, capsys):
        _simulate_input(monkeypatch, ["Title", "Author", "1965.5"])
        _, _, year = get_book_details()
        assert year == 0

    def test_very_large_year_accepted(self, monkeypatch):
        _simulate_input(monkeypatch, ["Title", "Author", "99999"])
        _, _, year = get_book_details()
        assert year == 99999

    def test_error_message_printed(self, monkeypatch, capsys):
        _simulate_input(monkeypatch, ["Title", "Author", "nope"])
        get_book_details()
        output = capsys.readouterr().out
        assert "Invalid year. Defaulting to 0." in output


# --- Very long titles ---


class TestLongTitles:

    def test_very_long_title(self, monkeypatch):
        long_title = "A" * 10_000
        _simulate_input(monkeypatch, [long_title, "Author", "2000"])
        title, _, _ = get_book_details()
        assert title == long_title
        assert len(title) == 10_000

    def test_long_author(self, monkeypatch):
        long_author = "B" * 5_000
        _simulate_input(monkeypatch, ["Title", long_author, "2000"])
        _, author, _ = get_book_details()
        assert author == long_author

    def test_multiword_long_title(self, monkeypatch):
        long_title = " ".join(["word"] * 500)
        _simulate_input(monkeypatch, [long_title, "Author", "2000"])
        title, _, _ = get_book_details()
        assert title == long_title


# --- Special characters in author names ---


class TestSpecialCharacters:

    @pytest.mark.parametrize("author", [
        "J.R.R. Tolkien",
        "Ursula K. Le Guin",
        "Gabriel García Márquez",
        "Ngũgĩ wa Thiong'o",
        "Stanisław Lem",
        "José Saramago",
        "大江健三郎",
        "مصطفى صادقی",
    ])
    def test_unicode_and_accented_authors(self, monkeypatch, author):
        _simulate_input(monkeypatch, ["Title", author, "2000"])
        _, result_author, _ = get_book_details()
        assert result_author == author

    def test_author_with_hyphens(self, monkeypatch):
        _simulate_input(monkeypatch, ["Title", "Mary-Anne O'Brien", "2000"])
        _, author, _ = get_book_details()
        assert author == "Mary-Anne O'Brien"

    def test_author_with_quotes(self, monkeypatch):
        _simulate_input(monkeypatch, ["Title", 'Author "Nick" Name', "2000"])
        _, author, _ = get_book_details()
        assert author == 'Author "Nick" Name'

    def test_title_with_special_chars(self, monkeypatch):
        _simulate_input(monkeypatch, ["Hitchhiker's Guide & More!", "Author", "2000"])
        title, _, _ = get_book_details()
        assert title == "Hitchhiker's Guide & More!"

    def test_emoji_in_title(self, monkeypatch):
        _simulate_input(monkeypatch, ["📚 My Book", "Author", "2000"])
        title, _, _ = get_book_details()
        assert title == "📚 My Book"
