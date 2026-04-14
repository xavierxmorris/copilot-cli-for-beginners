import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pytest
import books
from books import Book, BookCollection, get_book_statistics


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


# ── Original tests (preserved) ──────────────────────────────────────────

def test_add_book():
    collection = BookCollection()
    initial_count = len(collection.books)
    collection.add_book("1984", "George Orwell", 1949)
    assert len(collection.books) == initial_count + 1
    book = collection.find_book_by_title("1984")
    assert book is not None
    assert book.author == "George Orwell"
    assert book.year == 1949
    assert book.read is False

def test_mark_book_as_read():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    result = collection.mark_as_read("Dune")
    assert result is True
    book = collection.find_book_by_title("Dune")
    assert book.read is True

def test_mark_book_as_read_invalid():
    collection = BookCollection()
    result = collection.mark_as_read("Nonexistent Book")
    assert result is False

def test_remove_book():
    collection = BookCollection()
    collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)
    result = collection.remove_book("The Hobbit")
    assert result is True
    book = collection.find_book_by_title("The Hobbit")
    assert book is None

def test_remove_book_invalid():
    collection = BookCollection()
    result = collection.remove_book("Nonexistent Book")
    assert result is False


def test_get_book_statistics_mixed_books():
    book_list = [
        Book("Dune", "Frank Herbert", 1965, read=True),
        Book("The Hobbit", "J.R.R. Tolkien", 1937, read=False),
        Book("Neuromancer", "William Gibson", 1984, read=True),
    ]
    stats = get_book_statistics(book_list)
    assert stats["total_count"] == 3
    assert stats["read_count"] == 2
    assert stats["unread_count"] == 1
    assert stats["oldest_book"] is book_list[1]
    assert stats["newest_book"] is book_list[2]


def test_get_book_statistics_single_book():
    book_list = [Book("1984", "George Orwell", 1949, read=False)]
    stats = get_book_statistics(book_list)
    assert stats["total_count"] == 1
    assert stats["read_count"] == 0
    assert stats["unread_count"] == 1
    assert stats["oldest_book"] is book_list[0]
    assert stats["newest_book"] is book_list[0]


def test_get_book_statistics_empty_list():
    stats = get_book_statistics([])
    assert stats["total_count"] == 0
    assert stats["read_count"] == 0
    assert stats["unread_count"] == 0
    assert stats["oldest_book"] is None
    assert stats["newest_book"] is None


def test_get_book_statistics_tie_year_uses_first_match():
    book_list = [
        Book("Book A", "Author A", 2001, read=True),
        Book("Book B", "Author B", 2001, read=False),
    ]
    stats = get_book_statistics(book_list)
    assert stats["oldest_book"] is book_list[0]
    assert stats["newest_book"] is book_list[0]


def test_list_by_year_matching_range():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Neuromancer", "William Gibson", 1984)
    results = collection.list_by_year(1950, 1984)
    assert len(results) == 2
    titles = {b.title for b in results}
    assert titles == {"Dune", "Neuromancer"}


def test_list_by_year_no_matches():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    results = collection.list_by_year(2000, 2025)
    assert results == []


def test_list_by_year_single_year():
    collection = BookCollection()
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    results = collection.list_by_year(1965, 1965)
    assert len(results) == 1
    assert results[0].title == "Dune"


def test_list_by_year_invalid_range():
    collection = BookCollection()
    with pytest.raises(ValueError, match="Start year.*cannot be greater"):
        collection.list_by_year(2000, 1900)


# ── New: onError callback tests ──────────────────────────────────────────

def test_on_error_callback_called_on_corrupted_json(tmp_path, monkeypatch):
    """The on_error callback is invoked when data.json contains invalid JSON."""
    bad_file = tmp_path / "data.json"
    bad_file.write_text("{not valid json!!!")
    monkeypatch.setattr(books, "DATA_FILE", str(bad_file))

    errors: list = []

    def capture_error(err: Exception, context: str) -> None:
        errors.append((err, context))

    collection = BookCollection(on_error=capture_error)

    assert len(errors) == 1
    assert "corrupted or invalid" in errors[0][1]
    assert collection._is_corrupted is True
    assert collection.books == []


def test_on_error_callback_called_on_save_failure(tmp_path, monkeypatch):
    """The on_error callback is invoked when save_books encounters an IOError."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))

    errors: list = []

    def capture_error(err: Exception, context: str) -> None:
        errors.append((err, context))

    collection = BookCollection(on_error=capture_error)

    # Point DATA_FILE to a read-only directory to force an IOError on save
    readonly_dir = tmp_path / "readonly"
    readonly_dir.mkdir()
    monkeypatch.setattr(books, "DATA_FILE", str(readonly_dir / "sub" / "data.json"))

    collection.books.append(Book("Test", "Author", 2000))
    collection.save_books()

    assert len(errors) == 1
    assert "Could not save books" in errors[0][1]


def test_default_error_handler_prints(tmp_path, monkeypatch, capsys):
    """When no callback is given, errors are printed to stdout (default behaviour)."""
    bad_file = tmp_path / "data.json"
    bad_file.write_text("{bad json")
    monkeypatch.setattr(books, "DATA_FILE", str(bad_file))

    # No on_error — uses the default print-based handler
    collection = BookCollection()

    captured = capsys.readouterr()
    assert "corrupted or invalid" in captured.out
    assert collection._is_corrupted is True


def test_on_error_callback_not_called_on_success():
    """The callback is never invoked when there are no errors."""
    errors: list = []

    def capture_error(err: Exception, context: str) -> None:
        errors.append((err, context))

    collection = BookCollection(on_error=capture_error)
    collection.add_book("Dune", "Frank Herbert", 1965)

    assert len(errors) == 0
    assert len(collection.books) == 1
