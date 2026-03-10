"""Comprehensive tests for BookCollection behavior.

Generated before the context-manager refactor so we can verify
that all existing behavior is preserved.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, BookNotFoundError, StorageError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Use a temporary data file for each test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    return temp_file


# --- Book dataclass ---

class TestBook:
    def test_defaults(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965)
        assert book.read is False

    def test_all_fields(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965, read=True)
        assert book.title == "Dune"
        assert book.author == "Frank Herbert"
        assert book.year == 1965
        assert book.read is True


# --- Initialization & persistence ---

class TestLoadSave:
    def test_empty_file(self):
        collection = BookCollection()
        assert collection.list_books() == []

    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(books, "DATA_FILE", str(tmp_path / "nonexistent.json"))
        collection = BookCollection()
        assert collection.list_books() == []

    def test_corrupted_file(self, tmp_path, monkeypatch):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{not valid json!!")
        monkeypatch.setattr(books, "DATA_FILE", str(bad_file))
        collection = BookCollection()
        assert collection.list_books() == []

    def test_persists_across_instances(self):
        c1 = BookCollection()
        c1.add_book("Dune", "Frank Herbert", 1965)

        c2 = BookCollection()
        assert len(c2.list_books()) == 1
        assert c2.list_books()[0].title == "Dune"

    def test_save_overwrites_file(self, use_temp_data_file):
        collection = BookCollection()
        collection.add_book("A", "Author A", 2000)
        collection.add_book("B", "Author B", 2001)

        raw = json.loads(use_temp_data_file.read_text())
        assert len(raw) == 2


# --- add_book ---

class TestAddBook:
    def test_returns_book(self):
        collection = BookCollection()
        book = collection.add_book("1984", "George Orwell", 1949)
        assert isinstance(book, Book)
        assert book.title == "1984"

    def test_increments_count(self):
        collection = BookCollection()
        collection.add_book("A", "A", 2000)
        collection.add_book("B", "B", 2001)
        assert len(collection.list_books()) == 2

    def test_new_book_unread(self):
        collection = BookCollection()
        book = collection.add_book("Dune", "Frank Herbert", 1965)
        assert book.read is False


# --- find_book_by_title ---

class TestFindByTitle:
    def test_exact_match(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_book_by_title("Dune") is not None

    def test_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_book_by_title("dune") is not None
        assert collection.find_book_by_title("DUNE") is not None

    def test_not_found(self):
        collection = BookCollection()
        assert collection.find_book_by_title("Nonexistent") is None


# --- mark_as_read ---

class TestMarkAsRead:
    def test_marks_and_returns_true(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.mark_as_read("Dune") is True
        assert collection.find_book_by_title("Dune").read is True

    def test_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.mark_as_read("dune")
        assert collection.find_book_by_title("Dune").read is True

    def test_not_found_raises(self):
        collection = BookCollection()
        with pytest.raises(BookNotFoundError):
            collection.mark_as_read("Nonexistent")

    def test_persists_read_status(self):
        c1 = BookCollection()
        c1.add_book("Dune", "Frank Herbert", 1965)
        c1.mark_as_read("Dune")

        c2 = BookCollection()
        assert c2.find_book_by_title("Dune").read is True


# --- remove_book ---

class TestRemoveBook:
    def test_removes_and_returns_true(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.remove_book("Dune") is True
        assert collection.find_book_by_title("Dune") is None

    def test_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.remove_book("dune")
        assert len(collection.list_books()) == 0

    def test_not_found_raises(self):
        collection = BookCollection()
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Nonexistent")

    def test_persists_removal(self):
        c1 = BookCollection()
        c1.add_book("Dune", "Frank Herbert", 1965)
        c1.remove_book("Dune")

        c2 = BookCollection()
        assert len(c2.list_books()) == 0


# --- find_by_author ---

class TestFindByAuthor:
    def test_finds_matching(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("1984", "George Orwell", 1949)
        results = collection.find_by_author("Frank Herbert")
        assert len(results) == 1
        assert results[0].title == "Dune"

    def test_case_insensitive(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert len(collection.find_by_author("frank herbert")) == 1

    def test_multiple_matches(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Children of Dune", "Frank Herbert", 1976)
        assert len(collection.find_by_author("Frank Herbert")) == 2

    def test_no_matches(self):
        collection = BookCollection()
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_by_author("Nobody") == []
