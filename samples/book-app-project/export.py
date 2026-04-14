"""Export utilities for book collections.

Provides functions to export books to CSV, JSON, and plain
dictionaries for use in other formats or tools.
"""

import csv
import io
import json
from typing import List

from books import Book, StorageError


def books_to_csv_string(books: List[Book]) -> str:
    """Convert a list of books to a CSV-formatted string.

    Uses the csv module with an in-memory StringIO buffer to produce
    a well-formed CSV string with a header row.

    Args:
        books: The books to convert.

    Returns:
        A CSV string with columns: title, author, year, read.
        If books is empty, returns just the header row.

    Example:
        >>> from books import Book
        >>> b = Book("Dune", "Frank Herbert", 1965, read=True)
        >>> print(books_to_csv_string([b]))
        title,author,year,read
        Dune,Frank Herbert,1965,True
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["title", "author", "year", "read"])
    for book in books:
        writer.writerow([book.title, book.author, book.year, book.read])
    return output.getvalue()


def export_books_to_csv(books: List[Book], filepath: str) -> int:
    """Write books to a CSV file at the given path.

    Args:
        books: The books to export.
        filepath: Destination file path for the CSV output.

    Returns:
        The number of books written.

    Raises:
        StorageError: If the file cannot be written.

    Example:
        >>> from books import Book
        >>> books = [Book("Dune", "Frank Herbert", 1965)]
        >>> export_books_to_csv(books, "my_books.csv")
        1
    """
    try:
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["title", "author", "year", "read"])
            for book in books:
                writer.writerow([book.title, book.author, book.year, book.read])
    except OSError as e:
        raise StorageError(f"Could not write CSV to {filepath}") from e
    return len(books)


def books_to_dicts(books: List[Book]) -> List[dict]:
    """Convert books to a list of plain dictionaries.

    Useful as an intermediate step before JSON export or for
    passing book data to other tools and formats.

    Args:
        books: The books to convert.

    Returns:
        A list of dictionaries, one per book, with keys
        title, author, year, and read.

    Example:
        >>> from books import Book
        >>> b = Book("Dune", "Frank Herbert", 1965, read=True)
        >>> books_to_dicts([b])
        [{'title': 'Dune', 'author': 'Frank Herbert', 'year': 1965, 'read': True}]
    """
    return [
        {
            "title": book.title,
            "author": book.author,
            "year": book.year,
            "read": book.read,
        }
        for book in books
    ]


def export_books_to_json(
    books: List[Book], filepath: str, indent: int = 2
) -> int:
    """Write books as a JSON array to a file.

    Args:
        books: The books to export.
        filepath: Destination file path for the JSON output.
        indent: Number of spaces for JSON indentation. Defaults to 2.

    Returns:
        The number of books written.

    Raises:
        StorageError: If the file cannot be written.

    Example:
        >>> from books import Book
        >>> books = [Book("Dune", "Frank Herbert", 1965)]
        >>> export_books_to_json(books, "my_books.json")
        1
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(books_to_dicts(books), f, indent=indent)
    except OSError as e:
        raise StorageError(f"Could not write JSON to {filepath}") from e
    return len(books)
