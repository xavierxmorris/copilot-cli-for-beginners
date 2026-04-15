# Book Collection API — JWT Authentication Demo

> ⚠️ **Demo only** — this sample uses a hardcoded secret key and a single
> demo user. It is designed to teach JWT authentication concepts, **not**
> for production use.

A FastAPI REST API that manages a book collection behind JWT authentication.
Built as a teaching sample for the [Copilot CLI for Beginners](../../README.md) course.

## Quick Start

### 1. Install dependencies

```bash
cd samples/book-app-api
pip install -r requirements.txt
```

### 2. Start the server

```bash
uvicorn app:app --reload
```

The API is now running at `http://127.0.0.1:8000`.
Interactive docs are at `http://127.0.0.1:8000/docs`.

### 3. Get a token

```bash
curl -X POST http://127.0.0.1:8000/token \
  -d "username=demo&password=password"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### 4. Use the token

Copy the `access_token` value and include it in subsequent requests:

```bash
# Set your token (replace with the actual value)
TOKEN="eyJhbGciOiJIUzI1NiIs..."

# Add a book
curl -X POST http://127.0.0.1:8000/books \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Dune", "author": "Frank Herbert", "year": 1965}'

# List all books
curl http://127.0.0.1:8000/books \
  -H "Authorization: Bearer $TOKEN"

# Get a book by ID
curl http://127.0.0.1:8000/books/1 \
  -H "Authorization: Bearer $TOKEN"

# Mark a book as read
curl -X PATCH http://127.0.0.1:8000/books/1/read \
  -H "Authorization: Bearer $TOKEN"

# Search by author
curl "http://127.0.0.1:8000/books?author=Frank%20Herbert" \
  -H "Authorization: Bearer $TOKEN"

# Delete a book
curl -X DELETE http://127.0.0.1:8000/books/1 \
  -H "Authorization: Bearer $TOKEN"
```

## How JWT Authentication Works

```
┌──────────┐    POST /token       ┌──────────┐
│  Client   │ ──────────────────► │  Server   │
│           │  username + password │           │
│           │ ◄────────────────── │           │
│           │  { access_token }   │           │
│           │                     │           │
│           │  GET /books          │           │
│           │  Authorization:     │           │
│           │  Bearer <token>     │           │
│           │ ──────────────────► │           │
│           │                     │  ✓ decode │
│           │ ◄────────────────── │  ✓ verify │
│           │  [ books... ]       │  ✓ return │
└──────────┘                     └──────────┘
```

1. **Login** — send your username and password to `POST /token`
2. **Receive token** — the server verifies credentials and returns a signed JWT
3. **Use token** — include `Authorization: Bearer <token>` in every request
4. **Server validates** — each protected endpoint decodes and verifies the JWT
5. **Token expires** — after 30 minutes, you'll need to log in again

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/token` | ❌ | Get a JWT access token |
| GET | `/books` | ✅ | List books (optional `?title=` or `?author=` filter) |
| POST | `/books` | ✅ | Add a new book |
| GET | `/books/{id}` | ✅ | Get a book by ID |
| DELETE | `/books/{id}` | ✅ | Remove a book |
| PATCH | `/books/{id}/read` | ✅ | Mark a book as read |

## Project Structure

```
book-app-api/
├── app.py              # FastAPI application and endpoints
├── auth.py             # JWT authentication (token + password hashing)
├── books.py            # Book model and collection (data layer)
├── data.json           # Book data (created on first write)
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── tests/
    └── test_app.py     # Pytest tests
```

## Demo Credentials

| Username | Password |
|----------|----------|
| `demo` | `password` |

## Running Tests

```bash
cd samples/book-app-api
pip install pytest httpx
pytest tests/ -v
```
