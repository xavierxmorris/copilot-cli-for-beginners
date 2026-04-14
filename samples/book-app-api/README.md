# Book Collection API

A minimal Flask REST API for the book collection app. This sample is used by the [Adding Authentication](../../appendices/adding-authentication.md) appendix, where you use GitHub Copilot CLI to add session-based authentication step by step.

## Quick Start

```bash
cd samples/book-app-api
pip install -r requirements.txt
python app.py
```

The API starts on `http://localhost:5000`.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/books` | List all books |
| POST | `/books` | Add a book (JSON body: `title`, `author`, `year`) |
| DELETE | `/books/<title>` | Remove a book by title |
| PUT | `/books/<title>/read` | Mark a book as read |
| GET | `/books/search?author=<name>` | Find books by author |
| GET | `/health` | Health check |

## Example

```bash
# List all books
curl http://localhost:5000/books

# Add a book
curl -X POST http://localhost:5000/books \
  -H "Content-Type: application/json" \
  -d '{"title": "1984", "author": "George Orwell", "year": 1949}'

# Mark as read
curl -X PUT http://localhost:5000/books/1984/read
```

## Note

This API has **no authentication**. That's intentional — the appendix walks you through adding it with Copilot CLI!
