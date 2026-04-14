"""Generated pytest coverage for books.py."""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import books
from books import BookCollection, BookNotFoundError


@pytest.fixture
def temp_data_file(tmp_path, monkeypatch):
    """Point the books module at a temporary JSON file."""
    temp_file = tmp_path / "data.json"
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    return temp_file


@pytest.fixture
def collection(temp_data_file):
    """Create an empty collection backed by a temporary data file."""
    temp_data_file.write_text("[]")
    return BookCollection()


class TestAddBook:
    """Tests for BookCollection.add_book."""

    def test_add_book_returns_book_and_updates_collection(self, collection):
        book = collection.add_book("1984", "George Orwell", 1949)

        assert book.title == "1984"
        assert book.author == "George Orwell"
        assert book.year == 1949
        assert book.read is False
        assert collection.list_books() == [book]

    def test_add_multiple_books_preserves_insertion_order(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("The Hobbit", "J.R.R. Tolkien", 1937)

        assert [book.title for book in collection.list_books()] == ["Dune", "The Hobbit"]

    def test_add_book_persists_to_json(self, collection, temp_data_file):
        collection.add_book("Neuromancer", "William Gibson", 1984)

        saved_data = json.loads(temp_data_file.read_text())
        assert saved_data == [
            {
                "title": "Neuromancer",
                "author": "William Gibson",
                "year": 1984,
                "read": False,
            }
        ]


class TestFindBookByTitle:
    """Tests for BookCollection.find_book_by_title."""

    @pytest.mark.parametrize("lookup_title", ["Dune", "dune", "DUNE"])
    def test_find_by_title_is_case_insensitive(self, collection, lookup_title):
        collection.add_book("Dune", "Frank Herbert", 1965)

        book = collection.find_book_by_title(lookup_title)

        assert book is not None
        assert book.author == "Frank Herbert"

    def test_find_by_title_returns_none_when_missing(self, collection):
        assert collection.find_book_by_title("Missing Title") is None

    def test_find_by_title_returns_none_for_empty_collection(self, collection):
        assert collection.find_book_by_title("Anything") is None


class TestFindByAuthor:
    """Tests for BookCollection.find_by_author."""

    @pytest.mark.parametrize("lookup_author", ["Frank Herbert", "frank herbert", "FRANK HERBERT"])
    def test_find_by_author_is_case_insensitive(self, collection, lookup_author):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Children of Dune", "Frank Herbert", 1976)

        books_by_author = collection.find_by_author(lookup_author)

        assert [book.title for book in books_by_author] == ["Dune", "Children of Dune"]

    def test_find_by_author_returns_empty_list_when_no_match(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        assert collection.find_by_author("Isaac Asimov") == []

    def test_find_by_author_returns_empty_list_for_empty_collection(self, collection):
        assert collection.find_by_author("Any Author") == []


class TestMarkAsRead:
    """Tests for BookCollection.mark_as_read."""

    def test_mark_as_read_updates_book_and_persists(self, collection, temp_data_file):
        collection.add_book("Dune", "Frank Herbert", 1965)

        result = collection.mark_as_read("Dune")
        reloaded = BookCollection()

        assert result is True
        assert collection.find_book_by_title("Dune").read is True
        assert reloaded.find_book_by_title("Dune").read is True

        saved_data = json.loads(temp_data_file.read_text())
        assert saved_data[0]["read"] is True

    def test_mark_as_read_raises_for_missing_book(self, collection):
        with pytest.raises(BookNotFoundError, match="Book 'Missing Title' not found."):
            collection.mark_as_read("Missing Title")

    def test_mark_as_read_raises_for_empty_collection(self, collection):
        with pytest.raises(BookNotFoundError, match="Book 'Dune' not found."):
            collection.mark_as_read("Dune")


class TestRemoveBook:
    """Tests for BookCollection.remove_book."""

    def test_remove_book_deletes_existing_book_and_persists(self, collection, temp_data_file):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("1984", "George Orwell", 1949)

        result = collection.remove_book("Dune")
        reloaded = BookCollection()

        assert result is True
        assert collection.find_book_by_title("Dune") is None
        assert [book.title for book in collection.list_books()] == ["1984"]
        assert [book.title for book in reloaded.list_books()] == ["1984"]

        saved_data = json.loads(temp_data_file.read_text())
        assert [book["title"] for book in saved_data] == ["1984"]

    def test_remove_book_is_case_insensitive(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)

        result = collection.remove_book("dune")

        assert result is True
        assert collection.list_books() == []

    def test_remove_book_raises_for_missing_book(self, collection):
        with pytest.raises(BookNotFoundError, match="Book 'Missing Title' not found."):
            collection.remove_book("Missing Title")

    def test_remove_book_raises_for_empty_collection(self, collection):
        with pytest.raises(BookNotFoundError, match="Book 'Dune' not found."):
            collection.remove_book("Dune")


class TestEmptyDataEdgeCases:
    """Tests for empty-data scenarios."""

    def test_missing_data_file_starts_with_empty_collection(self, temp_data_file):
        if temp_data_file.exists():
            temp_data_file.unlink()

        collection = BookCollection()

        assert collection.list_books() == []

    def test_empty_json_array_loads_as_empty_collection(self, temp_data_file):
        temp_data_file.write_text("[]")

        collection = BookCollection()

        assert collection.list_books() == []
