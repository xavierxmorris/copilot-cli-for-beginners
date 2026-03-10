from typing import List, TYPE_CHECKING, Tuple

if TYPE_CHECKING:
    from books import Book


def print_menu() -> None:
    print("\n📚 Book Collection App")
    print("1. Add a book")
    print("2. List books")
    print("3. Mark book as read")
    print("4. Remove a book")
    print("5. Exit")


def get_user_choice() -> str:
    while True:
        choice = input("Choose an option (1-5): ").strip()
        if not choice:
            print("Choice cannot be empty.")
            continue
        if not choice.isdigit():
            print("Invalid choice. Please enter a number.")
            continue
        if choice not in {"1", "2", "3", "4", "5"}:
            print("Invalid choice. Please enter a number from 1 to 5.")
            continue
        return choice


def get_book_details() -> Tuple[str, str, int]:
    """Prompt the user for book details with input validation.

    Loops until valid, non-empty values are provided for title and author.
    Year must be a non-negative integer; defaults to 0 if left blank.

    Returns:
        Tuple[str, str, int]: A tuple of (title, author, year).
    """
    title = ""
    while not title:
        title = input("Enter book title: ").strip()
        if not title:
            print("Title cannot be empty.")

    author = ""
    while not author:
        author = input("Enter author: ").strip()
        if not author:
            print("Author cannot be empty.")

    while True:
        year_input = input("Enter publication year (leave blank for 0): ").strip()
        if not year_input:
            return title, author, 0
        try:
            year = int(year_input)
        except ValueError:
            print("Invalid year. Please enter a whole number.")
            continue
        if year < 0:
            print("Invalid year. Please enter a non-negative number.")
            continue
        return title, author, year


def print_books(books: List["Book"]) -> None:
    """Display books in a user-friendly format."""
    if not books:
        print("No books found.")
        return

    print("\nYour Book Collection:\n")

    for index, book in enumerate(books, start=1):
        status = "✓" if book.read else " "
        print(f"{index}. [{status}] {book.title} by {book.author} ({book.year})")

    print()
