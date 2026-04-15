"""Book model and collection for the Book API.

A standalone teaching sample adapted from the main book-app-project.
Adds integer IDs for RESTful API resource identity.
"""

import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional


DATA_FILE = "data.json"


class BookError(Exception):
    """Base exception for book-related errors."""


class BookNotFoundError(BookError):
    """Raised when a book cannot be found."""


class InvalidBookDataError(BookError):
    """Raised when book data is invalid."""


class StorageError(BookError):
    """Raised when reading or writing book data fails."""


@dataclass
class Book:
    """Represents a single book in the collection.

    Attributes:
        id: Unique integer identifier for API resource identity.
        title: The book's title.
        author: The book's author.
        year: Publication year.
        read: Whether the book has been read.
    """

    id: int
    title: str
    author: str
    year: int
    read: bool = False


def _next_id(books: List[Book]) -> int:
    """Return the next available book ID.

    Args:
        books: Current list of books.

    Returns:
        The next integer ID (max existing + 1, or 1 if empty).
    """
    if not books:
        return 1
    return max(b.id for b in books) + 1


class BookCollection:
    """Manages a collection of books with JSON file persistence.

    Example:
        >>> collection = BookCollection()
        >>> book = collection.add_book("Dune", "Frank Herbert", 1965)
        >>> book.title
        'Dune'
    """

    def __init__(self) -> None:
        self.books: List[Book] = []
        self.load_books()

    def load_books(self) -> None:
        """Load books from the JSON file if it exists.

        Raises:
            StorageError: If the data file is corrupted.
        """
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                self.books = [Book(**b) for b in data]
        except FileNotFoundError:
            self.books = []
        except json.JSONDecodeError as e:
            raise StorageError(
                "data.json is corrupted"
            ) from e

    def save_books(self) -> None:
        """Save the current book collection to JSON.

        Raises:
            StorageError: If writing to the data file fails.
        """
        try:
            with open(DATA_FILE, "w") as f:
                json.dump([asdict(b) for b in self.books], f, indent=2)
        except OSError as e:
            raise StorageError(
                f"Failed to save books: {e}"
            ) from e

    def add_book(self, title: str, author: str, year: int) -> Book:
        """Add a new book to the collection.

        Args:
            title: The book's title (must be non-empty).
            author: The book's author (must be non-empty).
            year: Publication year (must be between 1 and 2027).

        Returns:
            The newly created Book.

        Raises:
            InvalidBookDataError: If any field is invalid.

        Example:
            >>> collection = BookCollection()
            >>> book = collection.add_book("1984", "George Orwell", 1949)
            >>> book.author
            'George Orwell'
        """
        if not title or not title.strip():
            raise InvalidBookDataError("Title cannot be empty")
        if not author or not author.strip():
            raise InvalidBookDataError("Author cannot be empty")
        if not isinstance(year, int) or year < 1 or year > 2027:
            raise InvalidBookDataError(
                "Year must be an integer between 1 and 2027"
            )

        book = Book(
            id=_next_id(self.books),
            title=title.strip(),
            author=author.strip(),
            year=year,
        )
        self.books.append(book)
        self.save_books()
        return book

    def list_books(self) -> List[Book]:
        """Return all books in the collection.

        Returns:
            A list of all Book objects.

        Example:
            >>> collection = BookCollection()
            >>> books = collection.list_books()
            >>> isinstance(books, list)
            True
        """
        return self.books

    def find_book_by_id(self, book_id: int) -> Optional[Book]:
        """Find a book by its unique ID.

        Args:
            book_id: The integer ID to search for.

        Returns:
            The matching Book, or None if not found.

        Example:
            >>> collection = BookCollection()
            >>> result = collection.find_book_by_id(999)
            >>> result is None
            True
        """
        for book in self.books:
            if book.id == book_id:
                return book
        return None

    def find_book_by_title(self, title: str) -> Optional[Book]:
        """Find a book by title (case-insensitive).

        Args:
            title: The title to search for.

        Returns:
            The first matching Book, or None if not found.

        Example:
            >>> collection = BookCollection()
            >>> result = collection.find_book_by_title("nonexistent")
            >>> result is None
            True
        """
        for book in self.books:
            if book.title.lower() == title.lower():
                return book
        return None

    def mark_as_read(self, book_id: int) -> Book:
        """Mark a book as read by its ID.

        Args:
            book_id: The ID of the book to mark as read.

        Returns:
            The updated Book.

        Raises:
            BookNotFoundError: If no book with the given ID exists.

        Example:
            >>> collection = BookCollection()
            >>> book = collection.add_book("Test", "Author", 2000)
            >>> updated = collection.mark_as_read(book.id)
            >>> updated.read
            True
        """
        book = self.find_book_by_id(book_id)
        if not book:
            raise BookNotFoundError(
                f"No book found with id {book_id}"
            )
        book.read = True
        self.save_books()
        return book

    def remove_book(self, book_id: int) -> bool:
        """Remove a book by its ID.

        Args:
            book_id: The ID of the book to remove.

        Returns:
            True if the book was removed.

        Raises:
            BookNotFoundError: If no book with the given ID exists.

        Example:
            >>> collection = BookCollection()
            >>> book = collection.add_book("Temp", "Author", 2000)
            >>> collection.remove_book(book.id)
            True
        """
        book = self.find_book_by_id(book_id)
        if not book:
            raise BookNotFoundError(
                f"No book found with id {book_id}"
            )
        self.books.remove(book)
        self.save_books()
        return True

    def find_by_author(self, author: str) -> List[Book]:
        """Find all books by a given author (case-insensitive).

        Args:
            author: The author name to search for.

        Returns:
            A list of matching Book objects.

        Example:
            >>> collection = BookCollection()
            >>> results = collection.find_by_author("Unknown")
            >>> len(results)
            0
        """
        return [
            b for b in self.books
            if b.author.lower() == author.lower()
        ]
