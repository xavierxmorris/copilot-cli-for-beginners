import json
import os
import tempfile
from dataclasses import dataclass, asdict
from typing import Callable, List, Optional

DATA_FILE = "data.json"

# Type alias for the error callback.
# Receives the exception and a human-readable context string.
ErrorCallback = Callable[[Exception, str], None]


def _default_error_handler(error: Exception, context: str) -> None:
    """Fallback handler that prints errors to stdout (original behaviour)."""
    print(f"Error: {context} ({error})")


@dataclass
class Book:
    title: str
    author: str
    year: int
    read: bool = False

    def __post_init__(self):
        if not self.title.strip():
            raise ValueError("Title cannot be empty.")
        if not self.author.strip():
            raise ValueError("Author cannot be empty.")
        if self.year < 0:
            raise ValueError("Year cannot be negative.")


def get_book_statistics(books: List[Book]) -> dict:
    """Return summary statistics for a list of books."""
    total_count = len(books)
    read_count = sum(1 for book in books if book.read)
    unread_count = total_count - read_count
    oldest_book = min(books, key=lambda book: book.year) if books else None
    newest_book = max(books, key=lambda book: book.year) if books else None

    return {
        "total_count": total_count,
        "read_count": read_count,
        "unread_count": unread_count,
        "oldest_book": oldest_book,
        "newest_book": newest_book,
    }


class BookCollection:
    """Manages a collection of books backed by a JSON file.

    Args:
        on_error: Optional callback invoked when a recoverable error occurs
                  (e.g. corrupt data file, I/O failure on save).  Receives the
                  exception instance and a short context string.  When *None*,
                  errors are printed to stdout (original behaviour).
    """

    def __init__(self, on_error: Optional[ErrorCallback] = None):
        self.books: List[Book] = []
        self._is_corrupted = False
        self._on_error: ErrorCallback = on_error or _default_error_handler
        self.load_books()

    def _report_error(self, error: Exception, context: str) -> None:
        """Route an error through the configured callback."""
        self._on_error(error, context)

    def load_books(self):
        """Load books from the JSON file if it exists."""
        if not os.path.exists(DATA_FILE):
            self.books = []
            return

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.books = [Book(**b) for b in data]
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            self._report_error(e, "data.json is corrupted or invalid")
            print("To prevent data loss, saving is disabled until the file is fixed.")
            self._is_corrupted = True
            self.books = []
        except IOError as e:
            self._report_error(e, "Could not read data file")
            self.books = []

    def save_books(self):
        """Save the current book collection to JSON using an atomic write."""
        if self._is_corrupted:
            print("Warning: Saving disabled to prevent overwriting corrupted data.")
            return

        try:
            fd, temp_path = tempfile.mkstemp(
                dir=os.path.dirname(os.path.abspath(DATA_FILE)), text=True
            )
            with os.fdopen(fd, "w") as f:
                json.dump([asdict(b) for b in self.books], f, indent=2)

            if os.path.exists(DATA_FILE):
                os.remove(DATA_FILE)
            os.rename(temp_path, DATA_FILE)
        except IOError as e:
            self._report_error(e, "Could not save books")

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection.

        Raises:
            ValueError: If validation fails.
        """
        book = Book(title=title, author=author, year=year)
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        return self.books

    def find_book_by_title(self, title: str) -> Optional[Book]:
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, title: str) -> bool:
        book = self.find_book_by_title(title)
        if book:
            book.read = True
            self.save_books()
            return True
        return False

    def remove_book(self, title: str) -> bool:
        """Remove a book by title."""
        book = self.find_book_by_title(title)
        if book:
            self.books.remove(book)
            self.save_books()
            return True
        return False

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by a given author."""
        return [b for b in self.books if b.author.lower() == author.lower()]

    def list_by_year(self, start: int, end: int) -> List[Book]:
        """Filter books by publication year range (inclusive).

        Args:
            start: The earliest publication year to include.
            end: The latest publication year to include.

        Returns:
            List of books with year between start and end (inclusive).

        Raises:
            ValueError: If start is greater than end.
        """
        if start > end:
            raise ValueError(
                f"Start year ({start}) cannot be greater than end year ({end})."
            )
        return [b for b in self.books if start <= b.year <= end]
