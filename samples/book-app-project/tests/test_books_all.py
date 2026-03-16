"""Comprehensive pytest tests for books.py — all functions with edge cases."""

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
    """Provide a collection pre-loaded with three books."""
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("1984", "George Orwell", 1949)
    collection.add_book("Neuromancer", "William Gibson", 1984)
    return collection


# --- Book dataclass ---


class TestBook:
    """Tests for the Book dataclass."""

    def test_creation_defaults(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965)
        assert book.title == "Dune"
        assert book.author == "Frank Herbert"
        assert book.year == 1965
        assert book.read is False

    def test_creation_read_true(self):
        book = Book(title="Dune", author="Frank Herbert", year=1965, read=True)
        assert book.read is True

    def test_equality(self):
        a = Book("Dune", "Frank Herbert", 1965)
        b = Book("Dune", "Frank Herbert", 1965)
        assert a == b

    def test_inequality(self):
        a = Book("Dune", "Frank Herbert", 1965)
        b = Book("1984", "George Orwell", 1949)
        assert a != b


# --- load_books ---


class TestLoadBooks:
    """Tests for BookCollection.load_books."""

    def test_load_empty_file(self, collection):
        assert collection.books == []

    def test_load_missing_file(self, use_temp_data_file):
        os.remove(str(use_temp_data_file))
        collection = BookCollection()
        assert collection.books == []

    def test_load_corrupted_json(self, use_temp_data_file):
        use_temp_data_file.write_text("{not valid json!!!")
        collection = BookCollection()
        assert collection.books == []

    def test_load_persisted_books(self, use_temp_data_file):
        data = [{"title": "Dune", "author": "Frank Herbert", "year": 1965, "read": False}]
        use_temp_data_file.write_text(json.dumps(data))
        collection = BookCollection()
        assert len(collection.books) == 1
        assert collection.books[0].title == "Dune"


# --- save_books ---


class TestSaveBooks:
    """Tests for BookCollection.save_books."""

    def test_save_and_reload(self, collection, use_temp_data_file):
        collection.add_book("Dune", "Frank Herbert", 1965)
        reloaded = BookCollection()
        assert len(reloaded.books) == 1
        assert reloaded.books[0].title == "Dune"

    def test_save_empty_collection(self, collection, use_temp_data_file):
        collection.save_books()
        data = json.loads(use_temp_data_file.read_text())
        assert data == []


# --- add_book ---


class TestAddBook:
    """Tests for BookCollection.add_book."""

    def test_happy_path(self, collection):
        book = collection.add_book("Dune", "Frank Herbert", 1965)
        assert book.title == "Dune"
        assert book.author == "Frank Herbert"
        assert book.year == 1965
        assert book.read is False
        assert len(collection.books) == 1

    def test_add_multiple(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("1984", "George Orwell", 1949)
        assert len(collection.books) == 2

    def test_add_returns_book_instance(self, collection):
        result = collection.add_book("Dune", "Frank Herbert", 1965)
        assert isinstance(result, Book)

    @pytest.mark.parametrize(
        "title,author,year",
        [
            ("", "Author", 2000),
            ("Title", "", 2000),
            ("Title", "Author", 0),
            ("Title", "Author", -1),
        ],
    )
    def test_add_boundary_inputs(self, collection, title, author, year):
        book = collection.add_book(title, author, year)
        assert book.title == title
        assert book.author == author
        assert book.year == year


# --- list_books ---


class TestListBooks:
    """Tests for BookCollection.list_books."""

    def test_empty_collection(self, collection):
        assert collection.list_books() == []

    def test_returns_all_books(self, populated_collection):
        result = populated_collection.list_books()
        assert len(result) == 3

    def test_returns_same_list_reference(self, collection):
        assert collection.list_books() is collection.books


# --- find_book_by_title ---


class TestFindBookByTitle:
    """Tests for BookCollection.find_book_by_title."""

    def test_exact_match(self, populated_collection):
        book = populated_collection.find_book_by_title("Dune")
        assert book is not None
        assert book.author == "Frank Herbert"

    def test_case_insensitive(self, populated_collection):
        book = populated_collection.find_book_by_title("dUNe")
        assert book is not None
        assert book.title == "Dune"

    def test_not_found(self, populated_collection):
        assert populated_collection.find_book_by_title("Nonexistent") is None

    def test_empty_string(self, populated_collection):
        assert populated_collection.find_book_by_title("") is None

    def test_empty_collection(self, collection):
        assert collection.find_book_by_title("Dune") is None

    @pytest.mark.parametrize(
        "search",
        ["DUNE", "dune", "Dune", "dUnE"],
    )
    def test_various_cases(self, populated_collection, search):
        assert populated_collection.find_book_by_title(search) is not None


# --- mark_as_read ---


class TestMarkAsRead:
    """Tests for BookCollection.mark_as_read."""

    def test_happy_path(self, populated_collection):
        result = populated_collection.mark_as_read("Dune")
        assert result is True
        assert populated_collection.find_book_by_title("Dune").read is True

    def test_case_insensitive(self, populated_collection):
        populated_collection.mark_as_read("dune")
        assert populated_collection.find_book_by_title("Dune").read is True

    def test_only_marks_target(self, populated_collection):
        populated_collection.mark_as_read("Dune")
        assert populated_collection.find_book_by_title("1984").read is False
        assert populated_collection.find_book_by_title("Neuromancer").read is False

    def test_not_found_raises(self, populated_collection):
        with pytest.raises(BookNotFoundError, match="not found"):
            populated_collection.mark_as_read("Nonexistent")

    def test_empty_collection_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.mark_as_read("Dune")

    def test_persists_after_reload(self, populated_collection):
        populated_collection.mark_as_read("Dune")
        reloaded = BookCollection()
        assert reloaded.find_book_by_title("Dune").read is True


# --- remove_book ---


class TestRemoveBook:
    """Tests for BookCollection.remove_book."""

    def test_happy_path(self, populated_collection):
        result = populated_collection.remove_book("Dune")
        assert result is True
        assert populated_collection.find_book_by_title("Dune") is None
        assert len(populated_collection.books) == 2

    def test_case_insensitive(self, populated_collection):
        populated_collection.remove_book("dune")
        assert populated_collection.find_book_by_title("Dune") is None

    def test_not_found_raises(self, populated_collection):
        with pytest.raises(BookNotFoundError, match="not found"):
            populated_collection.remove_book("Nonexistent")

    def test_empty_collection_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dune")

    def test_persists_after_reload(self, populated_collection):
        populated_collection.remove_book("Dune")
        reloaded = BookCollection()
        assert reloaded.find_book_by_title("Dune") is None
        assert len(reloaded.books) == 2

    def test_remove_only_target(self, populated_collection):
        populated_collection.remove_book("1984")
        assert populated_collection.find_book_by_title("Dune") is not None
        assert populated_collection.find_book_by_title("Neuromancer") is not None


# --- find_by_author ---


class TestFindByAuthor:
    """Tests for BookCollection.find_by_author."""

    def test_happy_path(self, populated_collection):
        results = populated_collection.find_by_author("Frank Herbert")
        assert len(results) == 1
        assert results[0].title == "Dune"

    def test_case_insensitive(self, populated_collection):
        results = populated_collection.find_by_author("frank herbert")
        assert len(results) == 1

    def test_multiple_books_same_author(self, populated_collection):
        populated_collection.add_book("Dune Messiah", "Frank Herbert", 1969)
        results = populated_collection.find_by_author("Frank Herbert")
        assert len(results) == 2

    def test_no_match(self, populated_collection):
        results = populated_collection.find_by_author("Unknown Author")
        assert results == []

    def test_empty_string(self, populated_collection):
        results = populated_collection.find_by_author("")
        assert results == []

    def test_empty_collection(self, collection):
        results = collection.find_by_author("Frank Herbert")
        assert results == []


# --- Integration ---


class TestIntegration:
    """End-to-end workflows across multiple methods."""

    def test_add_find_mark_remove(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.find_book_by_title("Dune") is not None
        collection.mark_as_read("Dune")
        assert collection.find_book_by_title("Dune").read is True
        collection.remove_book("Dune")
        assert collection.find_book_by_title("Dune") is None
        assert collection.list_books() == []

    def test_persistence_round_trip(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.mark_as_read("Dune")
        reloaded = BookCollection()
        book = reloaded.find_book_by_title("Dune")
        assert book is not None
        assert book.read is True
