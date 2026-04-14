"""Edge-case pytest tests for BookCollection.

Covers: duplicate books, partial title removal, empty collection
searches, file permission errors during save, and concurrent access.
"""

import json
import sys
import os
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import books
from books import Book, BookCollection, BookNotFoundError, StorageError


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Redirect DATA_FILE to a temp directory for every test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    return temp_file


@pytest.fixture
def collection():
    return BookCollection()


# --- Duplicate books (same title and author) ---


class TestDuplicateBooks:

    def test_can_add_exact_duplicate(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert len(collection.list_books()) == 2

    def test_find_returns_first_duplicate(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 2020)
        book = collection.find_book_by_title("Dune")
        assert book.year == 1965

    def test_remove_only_removes_first_duplicate(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 2020)
        collection.remove_book("Dune")
        remaining = collection.list_books()
        assert len(remaining) == 1
        assert remaining[0].year == 2020

    def test_mark_as_read_only_marks_first_duplicate(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 2020)
        collection.mark_as_read("Dune")
        assert collection.list_books()[0].read is True
        assert collection.list_books()[1].read is False

    def test_same_title_different_author(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Other Author", 2000)
        assert len(collection.list_books()) == 2
        book = collection.find_book_by_title("Dune")
        assert book.author == "Frank Herbert"


# --- Removing a book by partial title match ---


class TestPartialTitleRemoval:

    def test_partial_title_does_not_match(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dun")

    def test_partial_title_with_extra_chars(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dune Messiah")

    def test_substring_does_not_match(self, collection):
        collection.add_book("Dune Messiah", "Frank Herbert", 1969)
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dune")

    def test_exact_title_required(self, collection):
        collection.add_book("The Lord of the Rings", "J.R.R. Tolkien", 1954)
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Lord of the Rings")

    def test_exact_match_works(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert collection.remove_book("Dune") is True
        assert len(collection.list_books()) == 0


# --- Finding books when collection is empty ---


class TestEmptyCollectionSearches:

    def test_find_by_title_returns_none(self, collection):
        assert collection.find_book_by_title("Dune") is None

    def test_find_by_author_returns_empty_list(self, collection):
        assert collection.find_by_author("Frank Herbert") == []

    def test_list_books_returns_empty_list(self, collection):
        assert collection.list_books() == []

    def test_remove_from_empty_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dune")

    def test_mark_as_read_from_empty_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.mark_as_read("Dune")

    def test_empty_after_removing_all(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.remove_book("Dune")
        assert collection.list_books() == []
        assert collection.find_book_by_title("Dune") is None


# --- File permission errors during save ---


class TestFilePermissionErrors:

    def test_save_to_readonly_file_raises_storage_error(
        self, collection, use_temp_data_file
    ):
        collection.add_book("Dune", "Frank Herbert", 1965)
        os.chmod(str(use_temp_data_file), 0o444)

        try:
            with pytest.raises(StorageError, match="Could not access"):
                collection.add_book("1984", "George Orwell", 1949)
        finally:
            os.chmod(str(use_temp_data_file), 0o644)

    def test_save_to_nonexistent_dir_raises(self, tmp_path, monkeypatch):
        bad_path = str(tmp_path / "no" / "such" / "dir" / "data.json")
        monkeypatch.setattr(books, "DATA_FILE", bad_path)
        collection = BookCollection()
        with pytest.raises((StorageError, FileNotFoundError)):
            collection.add_book("Dune", "Frank Herbert", 1965)

    def test_load_from_corrupted_json_starts_empty(
        self, use_temp_data_file
    ):
        """Corrupted JSON is caught in __init__, resulting in an empty collection."""
        use_temp_data_file.write_text("{bad json!!")
        c = BookCollection()
        assert c.list_books() == []


# --- Concurrent access to the book collection ---


class TestConcurrentAccess:

    def test_concurrent_adds_no_crash(self, collection):
        """Multiple threads adding books should not raise exceptions."""
        errors = []

        def add_book(i):
            try:
                collection.add_book(f"Book {i}", f"Author {i}", 2000 + i)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_book, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent adds raised: {errors}"

    def test_concurrent_reads_no_crash(self, collection):
        """Multiple threads reading should not raise exceptions."""
        collection.add_book("Dune", "Frank Herbert", 1965)
        errors = []

        def read_books():
            try:
                collection.list_books()
                collection.find_book_by_title("Dune")
                collection.find_by_author("Frank Herbert")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_books) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent reads raised: {errors}"

    def test_concurrent_add_and_read(self, collection):
        """Mixed reads and writes should not crash."""
        errors = []

        def writer(i):
            try:
                collection.add_book(f"Book {i}", f"Author {i}", 2000 + i)
            except Exception as e:
                errors.append(e)

        def reader():
            try:
                collection.list_books()
                collection.find_by_author("Author 0")
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            threads.append(threading.Thread(target=writer, args=(i,)))
            threads.append(threading.Thread(target=reader))

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Concurrent access raised: {errors}"
