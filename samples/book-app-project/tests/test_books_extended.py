"""Extended tests for books.py — covers edge cases, error paths, and integration."""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, get_book_statistics


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))


# ── Book dataclass validation ────────────────────────────────────────────


class TestBookValidation:
    """Tests for Book.__post_init__ validation."""

    def test_valid_book(self):
        book = Book("Dune", "Frank Herbert", 1965)
        assert book.title == "Dune"
        assert book.read is False

    def test_valid_book_marked_read(self):
        book = Book("Dune", "Frank Herbert", 1965, read=True)
        assert book.read is True

    @pytest.mark.parametrize("title", ["", "   ", "\t", "\n"])
    def test_empty_title_raises(self, title):
        with pytest.raises(ValueError, match="Title cannot be empty"):
            Book(title, "Author", 2000)

    @pytest.mark.parametrize("author", ["", "   ", "\t"])
    def test_empty_author_raises(self, author):
        with pytest.raises(ValueError, match="Author cannot be empty"):
            Book("Title", author, 2000)

    def test_negative_year_raises(self):
        with pytest.raises(ValueError, match="Year cannot be negative"):
            Book("Title", "Author", -1)

    def test_zero_year_is_valid(self):
        book = Book("Ancient Text", "Unknown", 0)
        assert book.year == 0


# ── BookCollection CRUD ──────────────────────────────────────────────────


class TestBookCollectionAdd:
    """Tests for BookCollection.add_book."""

    def test_add_returns_book(self):
        collection = BookCollection()
        result = collection.add_book("1984", "George Orwell", 1949)
        assert isinstance(result, Book)
        assert result.title == "1984"

    def test_add_invalid_book_raises(self):
        collection = BookCollection()
        with pytest.raises(ValueError):
            collection.add_book("", "Author", 2000)

    def test_add_multiple_books(self):
        collection = BookCollection()
        collection.add_book("Book A", "Author A", 2000)
        collection.add_book("Book B", "Author B", 2001)
        assert len(collection.list_books()) == 2


class TestBookCollectionFind:
    """Tests for find_book_by_title and find_by_author."""

    def test_find_by_title_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_book_by_title("dune") is not None
        assert collection.find_book_by_title("DUNE") is not None

    def test_find_by_title_not_found(self):
        collection = BookCollection()
        assert collection.find_book_by_title("Nonexistent") is None

    def test_find_by_author_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Children of Dune", "Frank Herbert", 1976)
        results = collection.find_by_author("frank herbert")
        assert len(results) == 2

    def test_find_by_author_no_match(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_by_author("Isaac Asimov") == []


class TestBookCollectionRemove:
    """Tests for BookCollection.remove_book."""

    def test_remove_reduces_count(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.remove_book("Dune")
        assert len(collection.list_books()) == 0

    def test_remove_nonexistent_returns_false(self):
        collection = BookCollection()
        assert collection.remove_book("Ghost Book") is False


class TestBookCollectionMarkAsRead:
    """Tests for BookCollection.mark_as_read."""

    def test_mark_as_read_persists(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.mark_as_read("Dune")
        # Reload from disk
        reloaded = BookCollection()
        assert reloaded.find_book_by_title("Dune").read is True

    def test_mark_nonexistent_returns_false(self):
        collection = BookCollection()
        assert collection.mark_as_read("No Such Book") is False


# ── list_by_year ─────────────────────────────────────────────────────────


class TestListByYear:
    """Tests for BookCollection.list_by_year."""

    def test_inclusive_boundaries(self):
        collection = BookCollection()
        collection.add_book("Book", "Author", 2000)
        assert len(collection.list_by_year(2000, 2000)) == 1

    def test_empty_collection(self):
        collection = BookCollection()
        assert collection.list_by_year(1900, 2100) == []

    def test_invalid_range_raises(self):
        collection = BookCollection()
        with pytest.raises(ValueError):
            collection.list_by_year(2025, 2000)


# ── get_book_statistics ──────────────────────────────────────────────────


class TestGetBookStatistics:
    """Tests for get_book_statistics."""

    def test_all_read(self):
        books_list = [
            Book("A", "Auth", 2000, read=True),
            Book("B", "Auth", 2001, read=True),
        ]
        stats = get_book_statistics(books_list)
        assert stats["read_count"] == 2
        assert stats["unread_count"] == 0

    def test_all_unread(self):
        books_list = [
            Book("A", "Auth", 2000),
            Book("B", "Auth", 2001),
        ]
        stats = get_book_statistics(books_list)
        assert stats["read_count"] == 0
        assert stats["unread_count"] == 2

    def test_oldest_newest(self):
        books_list = [
            Book("Old", "Auth", 1900),
            Book("New", "Auth", 2025),
        ]
        stats = get_book_statistics(books_list)
        assert stats["oldest_book"].title == "Old"
        assert stats["newest_book"].title == "New"


# ── Persistence & error handling ─────────────────────────────────────────


class TestPersistence:
    """Tests for load/save round-trip and corrupted data."""

    def test_save_and_reload(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        reloaded = BookCollection()
        assert len(reloaded.list_books()) == 1
        assert reloaded.list_books()[0].title == "Dune"

    def test_load_missing_file(self, tmp_path, monkeypatch):
        missing = tmp_path / "nonexistent.json"
        monkeypatch.setattr(books, "DATA_FILE", str(missing))
        collection = BookCollection()
        assert collection.list_books() == []

    def test_load_corrupted_json(self, tmp_path, monkeypatch):
        bad_file = tmp_path / "data.json"
        bad_file.write_text("{not valid json!!!")
        monkeypatch.setattr(books, "DATA_FILE", str(bad_file))
        collection = BookCollection()
        assert collection.list_books() == []
        assert collection._is_corrupted is True

    def test_corrupted_blocks_save(self, tmp_path, monkeypatch, capsys):
        bad_file = tmp_path / "data.json"
        bad_file.write_text("NOT JSON")
        monkeypatch.setattr(books, "DATA_FILE", str(bad_file))
        collection = BookCollection()
        collection.save_books()
        output = capsys.readouterr().out
        assert "Saving disabled" in output

    def test_load_invalid_book_data(self, tmp_path, monkeypatch):
        bad_file = tmp_path / "data.json"
        bad_file.write_text(json.dumps([{"title": "", "author": "A", "year": 1}]))
        monkeypatch.setattr(books, "DATA_FILE", str(bad_file))
        collection = BookCollection()
        assert collection._is_corrupted is True


# ── Integration ──────────────────────────────────────────────────────────


class TestIntegration:
    """End-to-end workflows."""

    def test_full_lifecycle(self):
        c = BookCollection()
        c.add_book("Dune", "Frank Herbert", 1965)
        c.add_book("1984", "George Orwell", 1949)
        c.mark_as_read("Dune")
        c.remove_book("1984")

        reloaded = BookCollection()
        assert len(reloaded.list_books()) == 1
        assert reloaded.find_book_by_title("Dune").read is True
        assert reloaded.find_book_by_title("1984") is None

    def test_statistics_after_modifications(self):
        c = BookCollection()
        c.add_book("A", "Auth", 2000)
        c.add_book("B", "Auth", 2010)
        c.mark_as_read("A")

        stats = get_book_statistics(c.list_books())
        assert stats["total_count"] == 2
        assert stats["read_count"] == 1
        assert stats["oldest_book"].title == "A"
