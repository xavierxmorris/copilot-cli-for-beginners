---
name: docstring-gen
description: Generate Python docstrings - use when adding docstrings, documenting functions, or documenting Python code
---

# Docstring Generation Skill

Generate clear, consistent Python docstrings following Google style.

## When This Skill Activates

This skill loads when you ask to "add docstrings", "generate docstrings", or "document this function".

## Docstring Format (Google Style)

### Functions and Methods

```python
def find_by_author(self, author: str) -> list[Book]:
    """Find all books by a given author.

    Searches the collection for books whose author field matches
    the provided name (case-insensitive).

    Args:
        author: The author name to search for.

    Returns:
        A list of Book objects matching the author. Returns an
        empty list if no matches are found.

    Raises:
        ValueError: If author is an empty string.
    """
```

### Classes

```python
class BookCollection:
    """A collection of books with search and filter capabilities.

    Manages a list of Book objects and provides methods to add,
    remove, search, and filter books. Data is persisted to a
    JSON file.

    Attributes:
        books: The list of Book objects in the collection.
        filepath: Path to the JSON file used for storage.
    """
```

## Rules

1. First line is a concise summary in imperative mood ("Find", not "Finds")
2. Add a blank line between summary and details
3. Document every parameter in `Args:` — include type only if not in the signature
4. Document return value in `Returns:` — describe the meaning, not just the type
5. Document exceptions in `Raises:` only if the function explicitly raises them
6. Skip `Args:` / `Returns:` / `Raises:` sections when they would be empty
7. Keep line length under 79 characters inside docstrings

## Guidelines

- Write for someone reading the code for the first time
- Mention non-obvious behavior (e.g., "comparison is case-insensitive")
- For simple one-liner functions, a single summary line is sufficient
- Do not repeat the function signature in prose
