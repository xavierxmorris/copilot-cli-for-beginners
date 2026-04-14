from typing import List, Tuple
from books import Book, InvalidBookDataError


# --- Data processing (pure functions, no I/O) ---


def format_book_entry(index: int, book: Book) -> str:
    """Format a single book as a compact line."""
    status = "✓" if book.read else " "
    return f"{index}. [{status}] {book.title} by {book.author} ({book.year})"


def format_book_detail(index: int, book: Book) -> str:
    """Format a single book with emoji status."""
    status = "✅ Read" if book.read else "📖 Unread"
    return f"{index}. {book.title} by {book.author} ({book.year}) - {status}"


def parse_year(year_str: str) -> int:
    """Parse a year string into an integer."""
    try:
        return int(year_str)
    except ValueError:
        raise InvalidBookDataError("Invalid year. Defaulting to 0.") from None


# --- Display functions (handle all I/O) ---


def print_menu() -> None:
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def get_user_choice() -> str:
    return input("Choose an option (1-5): ").strip()


def get_book_details() -> Tuple[str, str, int]:
    title = input("Enter book title: ").strip()
    author = input("Enter author: ").strip()

    year_input = input("Enter publication year: ").strip()
    try:
        year = parse_year(year_input)
    except InvalidBookDataError as e:
        print(str(e))
        year = 0

    return title, author, year


def print_books(books: List[Book]) -> None:
    if not books:
        print("No books in your collection.")
        return

    print("\nYour Books:")
    for index, book in enumerate(books, start=1):
        print(format_book_detail(index, book))


def show_books(books: List[Book]) -> None:
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")
    for index, book in enumerate(books, start=1):
        print(format_book_entry(index, book))
    print()
