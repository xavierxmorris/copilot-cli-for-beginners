"""Generated pytest coverage for utils.get_book_details."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils


@pytest.fixture
def mock_inputs(monkeypatch):
    """Patch input() to return a sequence of responses."""

    def _mock(*responses):
        values = iter(responses)
        monkeypatch.setattr("builtins.input", lambda _prompt: next(values))

    return _mock


class TestGetBookDetails:
    """Tests for get_book_details."""

    @pytest.mark.parametrize(
        ("title_input", "author_input", "year_input", "expected"),
        [
            ("Dune", "Frank Herbert", "1965", ("Dune", "Frank Herbert", 1965)),
            (" 1984 ", " George Orwell ", " 1949 ", ("1984", "George Orwell", 1949)),
        ],
    )
    def test_returns_trimmed_valid_input(self, mock_inputs, title_input, author_input, year_input, expected):
        mock_inputs(title_input, author_input, year_input)

        result = utils.get_book_details()

        assert result == expected

    @pytest.mark.parametrize(
        ("title_input", "author_input", "year_input", "expected"),
        [
            ("", "", "", ("", "", 0)),
            ("   ", "\t", "   ", ("", "", 0)),
        ],
    )
    def test_allows_empty_strings_and_defaults_invalid_year_to_zero(
        self, mock_inputs, capsys, title_input, author_input, year_input, expected
    ):
        mock_inputs(title_input, author_input, year_input)

        result = utils.get_book_details()

        captured = capsys.readouterr()
        assert result == expected
        assert "Invalid year. Defaulting to 0." in captured.out

    @pytest.mark.parametrize("year_input", ["abc", "19.84", "2O24", "nineteen ninety-nine"])
    def test_invalid_year_formats_print_message_and_return_zero(self, mock_inputs, capsys, year_input):
        mock_inputs("Dune", "Frank Herbert", year_input)

        result = utils.get_book_details()

        captured = capsys.readouterr()
        assert result == ("Dune", "Frank Herbert", 0)
        assert "Invalid year. Defaulting to 0." in captured.out

    def test_preserves_very_long_titles(self, mock_inputs):
        long_title = "A" * 500
        mock_inputs(long_title, "Longform Author", "2024")

        result = utils.get_book_details()

        assert result == (long_title, "Longform Author", 2024)

    @pytest.mark.parametrize(
        "author_name",
        [
            "Gabriel García Márquez",
            "Flannery O'Connor",
            "Anne-Marie O'Brien",
            "Terry Pratchett & Neil Gaiman",
        ],
    )
    def test_preserves_special_characters_in_author_names(self, mock_inputs, author_name):
        mock_inputs("Good Omens", author_name, "1990")

        result = utils.get_book_details()

        assert result == ("Good Omens", author_name, 1990)
