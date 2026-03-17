"""Comprehensive pytest tests for BookCollection.

Covers: adding, removing, finding by title, finding by author,
marking as read, persistence, and edge cases with empty/corrupt data.
"""

import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, BookNotFoundError, InvalidBookDataError, StorageError


# --- Fixtures ---


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Redirect DATA_FILE to a temp directory for every test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    return temp_file


@pytest.fixture
def collection():
    """Provide a fresh, empty BookCollection."""
    return BookCollection()


@pytest.fixture
def populated_collection(collection):
    """Provide a collection pre-loaded with sample books."""
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Children of Dune", "Frank Herbert", 1976)
    return collection


# --- Book dataclass ---


class TestBook:
    """Tests for the Book dataclass."""

    def test_defaults_to_unread(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965)
        assert book.read is False

    def test_all_fields(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965, read=True)
        assert book.title == "Dune"
        assert book.author == "Frank Herbert"
        assert book.year == 1965
        assert book.read is True


# --- Adding books ---


class TestAddBook:
    """Tests for BookCollection.add_book."""

    def test_returns_book_instance(self, collection):
        result = collection.add_book("Dune", "Frank Herbert", 1965)
        assert isinstance(result, Book)
        assert result.title == "Dune"
        assert result.author == "Frank Herbert"
        assert result.year == 1965

    def test_new_book_is_unread(self, collection):
        book = collection.add_book("Dune", "Frank Herbert", 1965)
        assert book.read is False

    def test_increments_count(self, collection):
        collection.add_book("A", "Author A", 2000)
        collection.add_book("B", "Author B", 2001)
        assert len(collection.list_books()) == 2

    def test_persists_to_disk(self, collection, use_temp_data_file):
        collection.add_book("Dune", "Frank Herbert", 1965)
        raw = json.loads(use_temp_data_file.read_text())
        assert len(raw) == 1
        assert raw[0]["title"] == "Dune"

    @pytest.mark.parametrize("title,author,year", [
        ("", "Author", 2000),
        ("Title", "", 2000),
    ])
    def test_accepts_edge_case_inputs(self, collection, title, author, year):
        book = collection.add_book(title, author, year)
        assert book.title == title
        assert book.author == author
        assert book.year == year

    @pytest.mark.parametrize("year", [0, -1])
    def test_rejects_invalid_year(self, collection, year):
        with pytest.raises(InvalidBookDataError):
            collection.add_book("Title", "Author", year)


# --- Removing books ---


class TestRemoveBook:
    """Tests for BookCollection.remove_book."""

    def test_removes_and_returns_true(self, populated_collection):
        assert populated_collection.remove_book("Dune") is True
        assert populated_collection.find_book_by_title("Dune") is None

    def test_case_insensitive(self, populated_collection):
        populated_collection.remove_book("dune")
        assert populated_collection.find_book_by_title("Dune") is None

    def test_not_found_raises(self, collection):
        with pytest.raises(BookNotFoundError, match="not found"):
            collection.remove_book("Nonexistent")

    def test_only_removes_exact_match(self, populated_collection):
        """Removing 'Dune' should not remove 'Children of Dune'."""
        populated_collection.remove_book("Dune")
        assert populated_collection.find_book_by_title("Children of Dune") is not None

    def test_persists_removal(self, populated_collection):
        populated_collection.remove_book("1984")
        reloaded = BookCollection()
        assert reloaded.find_book_by_title("1984") is None
        assert len(reloaded.list_books()) == 2

    def test_remove_from_empty_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Anything")


# --- Finding by title ---


class TestFindByTitle:
    """Tests for BookCollection.find_book_by_title."""

    def test_exact_match(self, populated_collection):
        book = populated_collection.find_book_by_title("Dune")
        assert book is not None
        assert book.author == "Frank Herbert"

    @pytest.mark.parametrize("query", ["dune", "DUNE", "DuNe"])
    def test_case_insensitive(self, populated_collection, query):
        assert populated_collection.find_book_by_title(query) is not None

    def test_not_found_returns_none(self, populated_collection):
        assert populated_collection.find_book_by_title("Nonexistent") is None

    def test_empty_collection(self, collection):
        assert collection.find_book_by_title("Dune") is None

    def test_empty_string(self, populated_collection):
        assert populated_collection.find_book_by_title("") is None

    def test_partial_match_not_returned(self, populated_collection):
        """Searching 'Dun' should NOT match 'Dune'."""
        assert populated_collection.find_book_by_title("Dun") is None


# --- Finding by author ---


class TestFindByAuthor:
    """Tests for BookCollection.find_by_author."""

    def test_single_match(self, populated_collection):
        results = populated_collection.find_by_author("George Orwell")
        assert len(results) == 1
        assert results[0].title == "1984"

    def test_multiple_matches(self, populated_collection):
        results = populated_collection.find_by_author("Frank Herbert")
        assert len(results) == 2
        titles = {b.title for b in results}
        assert titles == {"Dune", "Children of Dune"}

    @pytest.mark.parametrize("query", ["frank herbert", "FRANK HERBERT", "Frank Herbert"])
    def test_case_insensitive(self, populated_collection, query):
        assert len(populated_collection.find_by_author(query)) == 2

    def test_no_matches(self, populated_collection):
        assert populated_collection.find_by_author("Nobody") == []

    def test_empty_collection(self, collection):
        assert collection.find_by_author("Anyone") == []

    def test_empty_string(self, populated_collection):
        # Empty string is a substring of every author name
        assert len(populated_collection.find_by_author("")) == 3


# --- Marking as read ---


class TestMarkAsRead:
    """Tests for BookCollection.mark_as_read."""

    def test_marks_and_returns_true(self, populated_collection):
        assert populated_collection.mark_as_read("Dune") is True
        assert populated_collection.find_book_by_title("Dune").read is True

    def test_case_insensitive(self, populated_collection):
        populated_collection.mark_as_read("dune")
        assert populated_collection.find_book_by_title("Dune").read is True

    def test_not_found_raises(self, collection):
        with pytest.raises(BookNotFoundError, match="not found"):
            collection.mark_as_read("Nonexistent")

    def test_only_marks_target_book(self, populated_collection):
        """Marking 'Dune' should not affect other books."""
        populated_collection.mark_as_read("Dune")
        assert populated_collection.find_book_by_title("1984").read is False

    def test_persists_read_status(self, populated_collection):
        populated_collection.mark_as_read("Dune")
        reloaded = BookCollection()
        assert reloaded.find_book_by_title("Dune").read is True

    def test_marking_already_read_is_idempotent(self, populated_collection):
        populated_collection.mark_as_read("Dune")
        populated_collection.mark_as_read("Dune")
        assert populated_collection.find_book_by_title("Dune").read is True


# --- Edge cases with empty/corrupt data ---


class TestEdgeCases:
    """Tests for empty data, missing files, and corrupt JSON."""

    def test_empty_json_array(self, collection):
        assert collection.list_books() == []

    def test_missing_data_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(books, "DATA_FILE", str(tmp_path / "nonexistent.json"))
        c = BookCollection()
        assert c.list_books() == []

    def test_corrupted_json_falls_back_to_empty(self, tmp_path, monkeypatch):
        bad_file = tmp_path / "data.json"
        bad_file.write_text("{not valid json!!")
        monkeypatch.setattr(books, "DATA_FILE", str(bad_file))
        c = BookCollection()
        assert c.list_books() == []

    def test_list_books_returns_same_reference(self, populated_collection):
        assert populated_collection.list_books() is populated_collection.books

    def test_persistence_round_trip(self, collection):
        """Add books, reload from disk, verify identical data."""
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("1984", "George Orwell", 1949)

        reloaded = BookCollection()
        assert len(reloaded.list_books()) == 2
        assert reloaded.find_book_by_title("Dune").year == 1965
        assert reloaded.find_book_by_title("1984").author == "George Orwell"
