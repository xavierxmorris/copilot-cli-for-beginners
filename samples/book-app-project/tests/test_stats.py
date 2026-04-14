"""Tests for the stats module — collection statistics functions."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import books
from books import Book

import stats
from stats import (
    average_year,
    books_per_author,
    format_stats_report,
    read_count,
    read_percentage,
    total_books,
    unread_count,
    year_range,
)


# ── Fixtures ────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


@pytest.fixture
def sample_books():
    return [
        Book("Dune", "Frank Herbert", 1965, read=True),
        Book("1984", "George Orwell", 1949, read=True),
        Book("Neuromancer", "William Gibson", 1984, read=False),
        Book("Children of Dune", "Frank Herbert", 1976, read=False),
    ]


@pytest.fixture
def single_book():
    return [Book("Dune", "Frank Herbert", 1965, read=True)]


@pytest.fixture
def all_read():
    return [
        Book("Dune", "Frank Herbert", 1965, read=True),
        Book("1984", "George Orwell", 1949, read=True),
    ]


@pytest.fixture
def none_read():
    return [
        Book("Dune", "Frank Herbert", 1965, read=False),
        Book("1984", "George Orwell", 1949, read=False),
    ]


# ── Tests ───────────────────────────────────────────────────────────


class TestTotalBooks:
    def test_returns_count(self, sample_books):
        assert total_books(sample_books) == 4

    def test_single_book(self, single_book):
        assert total_books(single_book) == 1

    def test_empty_list(self):
        assert total_books([]) == 0


class TestReadCount:
    def test_mixed_collection(self, sample_books):
        assert read_count(sample_books) == 2

    def test_all_read(self, all_read):
        assert read_count(all_read) == 2

    def test_none_read(self, none_read):
        assert read_count(none_read) == 0

    def test_single_read_book(self, single_book):
        assert read_count(single_book) == 1

    def test_empty_list(self):
        assert read_count([]) == 0


class TestUnreadCount:
    def test_mixed_collection(self, sample_books):
        assert unread_count(sample_books) == 2

    def test_all_read(self, all_read):
        assert unread_count(all_read) == 0

    def test_none_read(self, none_read):
        assert unread_count(none_read) == 2

    def test_single_read_book(self, single_book):
        assert unread_count(single_book) == 0

    def test_empty_list(self):
        assert unread_count([]) == 0


class TestReadPercentage:
    def test_mixed_collection(self, sample_books):
        assert read_percentage(sample_books) == 50.0

    def test_all_read(self, all_read):
        assert read_percentage(all_read) == 100.0

    def test_none_read(self, none_read):
        assert read_percentage(none_read) == 0.0

    def test_single_read_book(self, single_book):
        assert read_percentage(single_book) == 100.0

    def test_empty_list_returns_zero(self):
        assert read_percentage([]) == 0.0

    @pytest.mark.parametrize(
        "read_flags, expected",
        [
            ([True], 100.0),
            ([False], 0.0),
            ([True, False], 50.0),
            ([True, True, False], pytest.approx(66.6666667, rel=1e-4)),
        ],
    )
    def test_various_ratios(self, read_flags, expected):
        book_list = [
            Book(f"Book {i}", "Author", 2000, read=flag)
            for i, flag in enumerate(read_flags)
        ]
        assert read_percentage(book_list) == expected


class TestYearRange:
    def test_multiple_books(self, sample_books):
        assert year_range(sample_books) == (1949, 1984)

    def test_single_book_min_equals_max(self, single_book):
        assert year_range(single_book) == (1965, 1965)

    def test_empty_list_returns_none(self):
        assert year_range([]) is None

    def test_two_books(self):
        pair = [
            Book("A", "Author", 2000),
            Book("B", "Author", 1900),
        ]
        assert year_range(pair) == (1900, 2000)


class TestBooksPerAuthor:
    def test_multiple_authors(self, sample_books):
        result = books_per_author(sample_books)
        assert result == {
            "Frank Herbert": 2,
            "George Orwell": 1,
            "William Gibson": 1,
        }

    def test_single_author_multiple_books(self):
        book_list = [
            Book("Dune", "Frank Herbert", 1965),
            Book("Children of Dune", "Frank Herbert", 1976),
            Book("God Emperor of Dune", "Frank Herbert", 1981),
        ]
        assert books_per_author(book_list) == {"Frank Herbert": 3}

    def test_single_book(self, single_book):
        assert books_per_author(single_book) == {"Frank Herbert": 1}

    def test_empty_list(self):
        assert books_per_author([]) == {}


class TestAverageYear:
    def test_multiple_books(self, sample_books):
        expected = (1965 + 1949 + 1984 + 1976) / 4
        assert average_year(sample_books) == pytest.approx(expected)

    def test_single_book(self, single_book):
        assert average_year(single_book) == 1965.0

    def test_empty_list_returns_none(self):
        assert average_year([]) is None

    def test_precision(self):
        book_list = [
            Book("A", "Author", 2001),
            Book("B", "Author", 2002),
            Book("C", "Author", 2003),
        ]
        assert average_year(book_list) == pytest.approx(2002.0)


class TestFormatStatsReport:
    def test_contains_header(self, sample_books):
        report = format_stats_report(sample_books)
        assert "=== Book Collection Stats ===" in report

    def test_contains_total(self, sample_books):
        report = format_stats_report(sample_books)
        assert "Total books:" in report
        assert "4" in report

    def test_contains_read_unread(self, sample_books):
        report = format_stats_report(sample_books)
        assert "Read:" in report
        assert "Unread:" in report

    def test_contains_read_progress(self, sample_books):
        report = format_stats_report(sample_books)
        assert "50.0%" in report

    def test_contains_year_range(self, sample_books):
        report = format_stats_report(sample_books)
        assert "1949" in report
        assert "1984" in report

    def test_contains_average_year(self, sample_books):
        report = format_stats_report(sample_books)
        assert "Average year:" in report

    def test_contains_books_per_author(self, sample_books):
        report = format_stats_report(sample_books)
        assert "Frank Herbert: 2" in report
        assert "George Orwell: 1" in report

    def test_empty_list_shows_na(self):
        report = format_stats_report([])
        assert "Total books:" in report
        assert "0" in report
        assert "N/A" in report

    def test_single_book_report(self, single_book):
        report = format_stats_report(single_book)
        assert "Total books:" in report
        assert "1" in report
        assert "100.0%" in report
