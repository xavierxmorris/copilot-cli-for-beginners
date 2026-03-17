"""Advanced scenario tests for books.py.

Covers: duplicate books, partial title removal, empty collection searches,
file permission errors during save, and concurrent access.
"""

import json
import os
import sys
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


@pytest.fixture
def populated(collection):
    collection.add_book("Dune", "Frank Herbert", 1965)
    collection.add_book("Dune Messiah", "Frank Herbert", 1969)
    collection.add_book("1984", "George Orwell", 1949)
    return collection


# --- Duplicate books (same title and author) ---


class TestDuplicateBooks:
    """Verify behavior when adding books with identical title/author."""

    def test_duplicate_allowed(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert len(collection.books) == 2

    def test_duplicates_are_independent(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.mark_as_read("Dune")
        # mark_as_read finds the first match — only one should be read
        read_count = sum(1 for b in collection.books if b.read)
        assert read_count == 1

    def test_remove_duplicate_removes_first_only(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.remove_book("Dune")
        assert len(collection.books) == 1
        assert collection.books[0].title == "Dune"

    def test_same_title_different_author(self, collection):
        collection.add_book("Genesis", "Author A", 2000)
        collection.add_book("Genesis", "Author B", 2001)
        assert len(collection.books) == 2

    def test_find_returns_first_duplicate(self, collection):
        b1 = collection.add_book("Dune", "Frank Herbert", 1965)
        collection.add_book("Dune", "Frank Herbert", 1965)
        found = collection.find_book_by_title("Dune")
        assert found is b1


# --- Removing a book by partial title match ---


class TestPartialTitleRemoval:
    """Verify that remove_book uses exact (case-insensitive) match, not partial."""

    def test_partial_title_not_matched(self, populated):
        with pytest.raises(BookNotFoundError):
            populated.remove_book("Dune M")

    def test_substring_not_matched(self, populated):
        with pytest.raises(BookNotFoundError):
            populated.remove_book("une")

    def test_exact_match_works(self, populated):
        populated.remove_book("Dune")
        titles = [b.title for b in populated.books]
        assert "Dune" not in titles
        assert "Dune Messiah" in titles

    def test_case_insensitive_exact(self, populated):
        populated.remove_book("dune messiah")
        titles = [b.title for b in populated.books]
        assert "Dune Messiah" not in titles
        assert "Dune" in titles

    def test_extra_whitespace_not_matched(self, populated):
        with pytest.raises(BookNotFoundError):
            populated.remove_book("Dune ")


# --- Finding books when collection is empty ---


class TestEmptyCollectionSearches:
    """All search/find operations on an empty collection."""

    def test_list_books_empty(self, collection):
        assert collection.list_books() == []

    def test_find_by_title_empty(self, collection):
        assert collection.find_book_by_title("Anything") is None

    def test_find_by_author_empty(self, collection):
        assert collection.find_by_author("Anyone") == []

    def test_mark_as_read_empty_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.mark_as_read("Dune")

    def test_remove_from_empty_raises(self, collection):
        with pytest.raises(BookNotFoundError):
            collection.remove_book("Dune")

    def test_empty_after_removing_all(self, collection):
        collection.add_book("Dune", "Frank Herbert", 1965)
        collection.remove_book("Dune")
        assert collection.list_books() == []
        assert collection.find_book_by_title("Dune") is None
        assert collection.find_by_author("Frank Herbert") == []


# --- File permission errors during save ---


class TestFilePermissionErrors:
    """Verify StorageError is raised when the data file is not writable."""

    def test_save_to_readonly_file(self, collection, use_temp_data_file):
        collection.add_book("Dune", "Frank Herbert", 1965)
        # Make file read-only
        os.chmod(str(use_temp_data_file), 0o444)
        try:
            with pytest.raises(StorageError, match="Could not access"):
                collection.add_book("1984", "George Orwell", 1949)
        finally:
            os.chmod(str(use_temp_data_file), 0o644)

    def test_save_to_nonexistent_directory(self, collection, monkeypatch):
        monkeypatch.setattr(books, "DATA_FILE", "/nonexistent/path/data.json")
        with pytest.raises((StorageError, FileNotFoundError)):
            collection.add_book("Dune", "Frank Herbert", 1965)

    def test_load_from_corrupted_json(self, use_temp_data_file):
        use_temp_data_file.write_text("{broken json!!")
        collection = BookCollection()
        assert collection.books == []

    def test_init_survives_storage_error(self, use_temp_data_file):
        use_temp_data_file.write_text("not json")
        collection = BookCollection()
        assert collection.books == []
        # Can still add books after recovery
        collection.add_book("Dune", "Frank Herbert", 1965)
        assert len(collection.books) == 1


# --- Concurrent access to the book collection ---


class TestConcurrentAccess:
    """Basic thread-safety checks for the in-memory collection."""

    def test_concurrent_adds(self, collection):
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

        assert len(errors) == 0
        assert len(collection.books) == 10

    def test_concurrent_reads(self, populated):
        results = []

        def read_books():
            results.append(len(populated.list_books()))

        threads = [threading.Thread(target=read_books) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(r == 3 for r in results)

    def test_concurrent_find_by_title(self, populated):
        results = []

        def find():
            book = populated.find_book_by_title("Dune")
            results.append(book is not None)

        threads = [threading.Thread(target=find) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert all(results)

    def test_add_and_read_interleaved(self, collection):
        """Add books while other threads read — no crashes expected."""
        errors = []

        def add_books():
            for i in range(5):
                try:
                    collection.add_book(f"Book {i}", f"Author {i}", 2000 + i)
                except Exception as e:
                    errors.append(e)

        def read_books():
            for _ in range(10):
                try:
                    collection.list_books()
                except Exception as e:
                    errors.append(e)

        t1 = threading.Thread(target=add_books)
        t2 = threading.Thread(target=read_books)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(errors) == 0
