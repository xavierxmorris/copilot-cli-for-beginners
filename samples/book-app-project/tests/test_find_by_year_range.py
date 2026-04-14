"""Tests for BookCollection.find_by_year_range."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import BookCollection, InvalidBookDataError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def collection():
    return BookCollection()


@pytest.fixture
def populated(collection):
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Neuromancer", "William Gibson", 1984)
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    return collection


# --- Happy path ---


class TestHappyPath:

    def test_range_with_multiple_results(self, populated):
        results = populated.find_by_year_range(1940, 1970)
        titles = [b.title for b in results]
        assert "Dune" in titles
        assert "1984" in titles
        assert len(results) == 2

    def test_range_with_single_result(self, populated):
        results = populated.find_by_year_range(1980, 1990)
        assert len(results) == 1
        assert results[0].title == "Neuromancer"

    def test_exact_year_range(self, populated):
        results = populated.find_by_year_range(1965, 1965)
        assert len(results) == 1
        assert results[0].title == "Dune"

    def test_range_covering_all(self, populated):
        results = populated.find_by_year_range(1900, 2000)
        assert len(results) == 4

    def test_inclusive_boundaries(self, populated):
        results = populated.find_by_year_range(1937, 1984)
        assert len(results) == 4


# --- Edge cases ---


class TestEdgeCases:

    def test_no_match(self, populated):
        results = populated.find_by_year_range(2000, 2025)
        assert results == []

    def test_empty_collection(self, collection):
        results = collection.find_by_year_range(1900, 2000)
        assert results == []

    def test_boundary_just_below(self, populated):
        results = populated.find_by_year_range(1936, 1936)
        assert results == []

    def test_boundary_just_above(self, populated):
        results = populated.find_by_year_range(1985, 1985)
        assert results == []

    def test_same_year_no_match(self, populated):
        results = populated.find_by_year_range(1950, 1950)
        assert results == []

    def test_year_one(self, populated):
        results = populated.find_by_year_range(1, 1936)
        assert results == []


# --- Error cases ---


class TestErrorCases:

    def test_start_after_end_raises(self, populated):
        with pytest.raises(InvalidBookDataError, match="cannot be after"):
            populated.find_by_year_range(2000, 1900)

    def test_reversed_single_year_raises(self, populated):
        with pytest.raises(InvalidBookDataError):
            populated.find_by_year_range(1966, 1965)

    def test_error_message_includes_years(self, populated):
        with pytest.raises(InvalidBookDataError, match="2000.*1900"):
            populated.find_by_year_range(2000, 1900)


# --- Parametrized ---


class TestParametrized:

    @pytest.mark.parametrize("start,end,expected_count", [
        (1937, 1937, 1),
        (1937, 1949, 2),
        (1937, 1965, 3),
        (1937, 1984, 4),
        (1950, 1984, 2),
        (1966, 1984, 1),
        (1985, 2000, 0),
    ])
    def test_various_ranges(self, populated, start, end, expected_count):
        assert len(populated.find_by_year_range(start, end)) == expected_count
