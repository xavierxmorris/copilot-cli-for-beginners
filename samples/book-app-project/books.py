import json
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Generator, List, Optional

DATA_FILE = "data.json"


class BookError(Exception):
    """Base exception for book operations."""


class BookNotFoundError(BookError):
    """Raised when a book title doesn't match any book."""


class InvalidBookDataError(BookError):
    """Raised when book input is invalid (e.g., bad year)."""


class StorageError(BookError):
    """Raised when loading/saving fails."""


@contextmanager
def open_data_file(mode: str = "r") -> Generator:
    """Context manager for safe data file access.

    Args:
        mode: File open mode ("r" for reading, "w" for writing).

    Yields:
        The opened file handle.

    Raises:
        StorageError: If the file cannot be read or written.
        FileNotFoundError: Re-raised when reading a missing file
            so callers can handle it.
    """
    try:
        with open(DATA_FILE, mode) as f:
            yield f
    except FileNotFoundError:
        raise
    except (IOError, OSError) as e:
        raise StorageError(f"Could not access {DATA_FILE}: {e}") from e


@dataclass
class Book:
    """A single book in the collection.

    Attributes:
        title: The book's title.
        author: The book's author.
        year: The publication year.
        read: Whether the book has been read. Defaults to False.

    Example::

        >>> book = Book(title="Dune", author="Frank Herbert", year=1965)
        >>> book.read
        False
    """

    title: str
    author: str
    year: int
    read: bool = False


class BookCollection:
    """Manages a collection of books persisted to a JSON file.

    On initialization, books are loaded from ``data.json`` in the
    current directory. If the file is missing, the collection starts
    empty. If the file is corrupted, a warning is printed and the
    collection starts empty.

    Example::

        >>> collection = BookCollection()
        >>> collection.add_book("Dune", "Frank Herbert", 1965)
        Book(title='Dune', author='Frank Herbert', year=1965, read=False)
    """

    def __init__(self):
        self.books: List[Book] = []
        try:
            self.load_books()
        except StorageError as e:
            print(f"Warning: {e}")
            self.books = []

    def load_books(self) -> None:
        """Load books from the JSON data file.

        Reads ``data.json`` and populates ``self.books``. If the file
        does not exist, the book list is set to empty.

        Raises:
            StorageError: If ``data.json`` exists but contains invalid JSON,
                or if the file cannot be read.
        """
        try:
            with open_data_file("r") as f:
                data = json.load(f)
                self.books = [Book(**b) for b in data]
        except FileNotFoundError:
            self.books = []
        except json.JSONDecodeError:
            raise StorageError("data.json is corrupted. Starting with empty collection.")

    def save_books(self) -> None:
        """Save the current book collection to the JSON data file.

        Writes all books in ``self.books`` to ``data.json``, overwriting
        any existing content.

        Raises:
            StorageError: If the file cannot be written.
        """
        with open_data_file("w") as f:
            json.dump([asdict(b) for b in self.books], f, indent=2)

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection and save to disk.

        Args:
            title: The book's title.
            author: The book's author.
            year: The publication year (must be between 1 and next year).

        Returns:
            The newly created Book instance.

        Raises:
            InvalidBookDataError: If year is out of valid range.

        Example::

            >>> collection = BookCollection()
            >>> book = collection.add_book("1984", "George Orwell", 1949)
            >>> book.title
            '1984'
        """
        max_year = datetime.now().year + 1
        if year < 1 or year > max_year:
            raise InvalidBookDataError(
                f"Year must be between 1 and {max_year}."
            )
        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        """Return all books in the collection.

        Returns:
            A list of all Book instances. May be empty.

        Example::

            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> len(collection.list_books())
            1
        """
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        """Find a single book by its title (case-insensitive).

        Args:
            title: The title to search for.

        Returns:
            The matching Book, or None if no book matches.

        Example::

            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.find_book_by_title("dune").author
            'Frank Herbert'
        """
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        """Mark a book as read by its title (case-insensitive).

        Args:
            title: The title of the book to mark as read.

        Returns:
            True if the book was found and marked.

        Raises:
            BookNotFoundError: If no book matches the given title.

        Example::

            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.mark_as_read("Dune")
            True
        """
        book = self.find_book_by_title(title)
        if not book:
            raise BookNotFoundError(f"Book '{title}' not found.")
        book.read = True
        self.save_books()
        return True

    def remove_book(self, title: str) -> bool:
        """Remove a book from the collection by title (case-insensitive).

        Args:
            title: The title of the book to remove.

        Returns:
            True if the book was found and removed.

        Raises:
            BookNotFoundError: If no book matches the given title.

        Example::

            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.remove_book("Dune")
            True
            >>> len(collection.list_books())
            0
        """
        book = self.find_book_by_title(title)
        if not book:
            raise BookNotFoundError(f"Book '{title}' not found.")
        self.books.remove(book)
        self.save_books()
        return True

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by a given author (case-insensitive).

        Args:
            author: The author name to search for.

        Returns:
            A list of matching Book instances. May be empty.

        Example::

            >>> collection = BookCollection()
            >>> collection.add_book("Dune", "Frank Herbert", 1965)
            Book(title='Dune', author='Frank Herbert', year=1965, read=False)
            >>> collection.find_by_author("frank herbert")
            [Book(title='Dune', author='Frank Herbert', year=1965, read=False)]
        """
        return [b for b in self.books if author.lower() in b.author.lower()]
