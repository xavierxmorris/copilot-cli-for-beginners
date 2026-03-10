import sys
from typing import Callable, Dict, List

from books import Book, BookCollection
from utils import get_book_details, print_books


def default_error_handler(error: Exception, context: str) -> None:
    """Default onError callback — prints a friendly message to stderr."""
    print(f"\n[ERROR] {context}: {error}\n", file=sys.stderr)


# Pass the error callback when constructing the collection.
collection: BookCollection = BookCollection(on_error=default_error_handler)


def handle_list() -> None:
    books = collection.list_books()
    print_books(books)


def handle_add() -> None:
    print("\nAdd a New Book\n")

    title, author, year = get_book_details()

    try:
        collection.add_book(title, author, year)
        print("\nBook added successfully.\n")
    except ValueError as e:
        print(f"\nError: {e}\n")


def handle_remove() -> None:
    print("\nRemove a Book\n")

    title = input("Enter the title of the book to remove: ").strip()
    removed = collection.remove_book(title)
    if removed:
        print("\nBook removed successfully.\n")
    else:
        print("\nBook not found.\n")


def handle_find() -> None:
    print("\nFind Books by Author\n")

    author = input("Author name: ").strip()
    books = collection.find_by_author(author)

    print_books(books)


def handle_year() -> None:
    print("\nFilter Books by Year Range\n")

    try:
        start = int(input("Start year: ").strip())
        end = int(input("End year: ").strip())
        books = collection.list_by_year(start, end)
        print_books(books)
    except ValueError as e:
        print(f"\nError: {e}\n")


def handle_mark_read() -> None:
    print("\nMark a Book as Read\n")

    title = input("Enter the title of the book to mark as read: ").strip()
    marked = collection.mark_as_read(title)
    if marked:
        print("\nBook marked as read.\n")
    else:
        print("\nBook not found.\n")


def show_help() -> None:
    print("""
Book Collection Helper

Commands:
  list     - Show all books
  add      - Add a new book
  remove   - Remove a book by title
  find     - Find books by author
  year     - Filter books by year range
  read     - Mark a book as read
  help     - Show this help message
""")


def main() -> None:
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1].lower()
    command_handlers: Dict[str, Callable[[], None]] = {
        "list": handle_list,
        "add": handle_add,
        "remove": handle_remove,
        "find": handle_find,
        "year": handle_year,
        "read": handle_mark_read,
        "help": show_help,
    }
    handler = command_handlers.get(command)

    if handler is None:
        print("Unknown command.\n")
        show_help()
        return

    try:
        handler()
    except Exception as e:
        default_error_handler(e, f"Unexpected error while running '{command}'")


if __name__ == "__main__":
    main()
