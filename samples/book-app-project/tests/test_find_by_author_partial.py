"""Tests for find_by_author with partial name matching.

Covers: full name, partial name, case-insensitive, and not found scenarios.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def collection():
    c = BookCollection()
    c.add_book("Dune", "Frank Herbert", 1965)
    c.add_book("Dune Messiah", "Frank Herbert", 1969)
    c.add_book("1984", "George Orwell", 1949)
    c.add_book("Nausea", "Jean-Paul Sartre", 1938)
    return c


# --- Full author name match ---


class TestFullNameMatch:

    def test_exact_full_name(self, collection):
        results = collection.find_by_author("Frank Herbert")
        assert len(results) == 2

    def test_full_name_single_result(self, collection):
        results = collection.find_by_author("George Orwell")
        assert len(results) == 1
        assert results[0].title == "1984"

    def test_full_name_returns_all_books(self, collection):
        results = collection.find_by_author("Frank Herbert")
        titles = [b.title for b in results]
        assert "Dune" in titles
        assert "Dune Messiah" in titles


# --- Partial author name match ---


class TestPartialNameMatch:

    def test_last_name_only(self, collection):
        results = collection.find_by_author("Herbert")
        assert len(results) == 2

    def test_first_name_only(self, collection):
        results = collection.find_by_author("Frank")
        assert len(results) == 2

    def test_partial_last_name(self, collection):
        results = collection.find_by_author("Orwell")
        assert len(results) == 1

    def test_single_character(self, collection):
        # "r" appears in Herbert, Orwell, Sartre
        results = collection.find_by_author("r")
        assert len(results) >= 3

    def test_hyphenated_partial(self, collection):
        results = collection.find_by_author("Jean-Paul")
        assert len(results) == 1
        assert results[0].author == "Jean-Paul Sartre"


# --- Case-insensitive matching ---


class TestCaseInsensitive:

    @pytest.mark.parametrize("query,expected_count", [
        ("frank herbert", 2),
        ("FRANK HERBERT", 2),
        ("Frank HERBERT", 2),
        ("herbert", 2),
        ("HERBERT", 2),
        ("orwell", 1),
        ("ORWELL", 1),
    ])
    def test_case_variations(self, collection, query, expected_count):
        results = collection.find_by_author(query)
        assert len(results) == expected_count

    def test_mixed_case_partial(self, collection):
        results = collection.find_by_author("hErBeRt")
        assert len(results) == 2


# --- Author name not found ---


class TestNotFound:

    def test_nonexistent_author(self, collection):
        assert collection.find_by_author("Isaac Asimov") == []

    def test_misspelled_author(self, collection):
        assert collection.find_by_author("Herbet") == []

    def test_empty_string_matches_all(self, collection):
        # "" is a substring of every string
        results = collection.find_by_author("")
        assert len(results) == 4

    def test_empty_collection(self):
        c = BookCollection()
        assert c.find_by_author("Anyone") == []

    def test_whitespace_only(self, collection):
        # " " may or may not match depending on author names
        results = collection.find_by_author(" ")
        # All authors contain spaces, so all match
        assert len(results) == 4
