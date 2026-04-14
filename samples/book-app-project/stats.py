"""Book collection statistics functions.

Pure utility functions that compute statistics over a list of Book objects.
No I/O or side effects — every function takes a list and returns a value.

Example:
    >>> from books import Book
    >>> from stats import total_books, read_percentage
    >>> my_books = [Book("Dune", "Frank Herbert", 1965, read=True)]
    >>> total_books(my_books)
    1
    >>> read_percentage(my_books)
    100.0
"""

from typing import Dict, List, Optional, Tuple

from books import Book


def total_books(books: List[Book]) -> int:
    """Return the total number of books.

    Args:
        books: List of Book objects to count.

    Returns:
        The number of books in the list.

    Example:
        >>> total_books([Book("Dune", "Frank Herbert", 1965)])
        1
    """
    return len(books)


def read_count(books: List[Book]) -> int:
    """Return the number of books marked as read.

    Args:
        books: List of Book objects to check.

    Returns:
        Count of books where read is True.

    Example:
        >>> read_count([Book("Dune", "Frank Herbert", 1965, read=True)])
        1
    """
    return sum(1 for book in books if book.read)


def unread_count(books: List[Book]) -> int:
    """Return the number of books not yet read.

    Args:
        books: List of Book objects to check.

    Returns:
        Count of books where read is False.

    Example:
        >>> unread_count([Book("Dune", "Frank Herbert", 1965, read=False)])
        1
    """
    return sum(1 for book in books if not book.read)


def read_percentage(books: List[Book]) -> float:
    """Calculate the percentage of books that have been read.

    Args:
        books: List of Book objects to analyze.

    Returns:
        Percentage of read books (0.0–100.0). Returns 0.0 for an empty list.

    Example:
        >>> read_percentage([
        ...     Book("Dune", "Frank Herbert", 1965, read=True),
        ...     Book("1984", "George Orwell", 1949, read=False),
        ... ])
        50.0
    """
    if not books:
        return 0.0
    return (read_count(books) / len(books)) * 100.0


def year_range(books: List[Book]) -> Optional[Tuple[int, int]]:
    """Find the earliest and latest publication years.

    Args:
        books: List of Book objects to analyze.

    Returns:
        A tuple of (min_year, max_year), or None if the list is empty.

    Example:
        >>> year_range([
        ...     Book("Dune", "Frank Herbert", 1965),
        ...     Book("1984", "George Orwell", 1949),
        ... ])
        (1949, 1965)
    """
    if not books:
        return None
    years = [book.year for book in books]
    return (min(years), max(years))


def books_per_author(books: List[Book]) -> Dict[str, int]:
    """Count how many books each author has in the collection.

    Args:
        books: List of Book objects to group.

    Returns:
        A dictionary mapping author names to their book counts.

    Example:
        >>> books_per_author([
        ...     Book("Dune", "Frank Herbert", 1965),
        ...     Book("Children of Dune", "Frank Herbert", 1976),
        ... ])
        {'Frank Herbert': 2}
    """
    counts: Dict[str, int] = {}
    for book in books:
        counts[book.author] = counts.get(book.author, 0) + 1
    return counts


def average_year(books: List[Book]) -> Optional[float]:
    """Calculate the mean publication year.

    Args:
        books: List of Book objects to analyze.

    Returns:
        The average year as a float, or None if the list is empty.

    Example:
        >>> average_year([
        ...     Book("Dune", "Frank Herbert", 1965),
        ...     Book("1984", "George Orwell", 1949),
        ... ])
        1957.0
    """
    if not books:
        return None
    return sum(book.year for book in books) / len(books)


def format_stats_report(books: List[Book]) -> str:
    """Build a human-readable summary of collection statistics.

    Combines all the other stats functions into a formatted multi-line
    report suitable for printing to the terminal.

    Args:
        books: List of Book objects to summarize.

    Returns:
        A multi-line string with the statistics report.

    Example:
        >>> print(format_stats_report([Book("Dune", "Frank Herbert", 1965, read=True)]))
        === Book Collection Stats ===
        Total books:   1
        Read:          1
        Unread:        0
        Read progress: 100.0%
        Year range:    1965 – 1965
        Average year:  1965.0
        <BLANKLINE>
        Books per author:
          Frank Herbert: 1
    """
    lines = [
        "=== Book Collection Stats ===",
        f"Total books:   {total_books(books)}",
        f"Read:          {read_count(books)}",
        f"Unread:        {unread_count(books)}",
        f"Read progress: {read_percentage(books):.1f}%",
    ]

    yr = year_range(books)
    if yr:
        lines.append(f"Year range:    {yr[0]} \u2013 {yr[1]}")
    else:
        lines.append("Year range:    N/A")

    avg = average_year(books)
    if avg is not None:
        lines.append(f"Average year:  {avg:.1f}")
    else:
        lines.append("Average year:  N/A")

    author_counts = books_per_author(books)
    if author_counts:
        lines.append("")
        lines.append("Books per author:")
        for author, count in sorted(author_counts.items()):
            lines.append(f"  {author}: {count}")

    return "\n".join(lines)
