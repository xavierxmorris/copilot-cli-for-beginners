"""FastAPI Book Collection API with JWT Authentication.

⚠️  DEMO ONLY — this is a teaching sample for the Copilot CLI course.
It uses a hardcoded secret key and a single demo user.

Run the server:
    uvicorn app:app --reload

Get a token:
    POST /token  (username: "demo", password: "password")

Use the token:
    Authorization: Bearer <your-token>
"""

from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from auth import (
    Token,
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from books import (
    BookCollection,
    BookNotFoundError,
    InvalidBookDataError,
)


# ── Pydantic Request/Response Models ────────────────────────────────


class BookCreate(BaseModel):
    """Request body for creating a new book.

    Attributes:
        title: The book's title (required, non-empty).
        author: The book's author (required, non-empty).
        year: Publication year (between 1 and 2027).
    """

    title: str = Field(..., min_length=1, examples=["Dune"])
    author: str = Field(
        ..., min_length=1, examples=["Frank Herbert"]
    )
    year: int = Field(..., ge=1, le=2027, examples=[1965])


class BookResponse(BaseModel):
    """Response model for a single book.

    Attributes:
        id: Unique integer identifier.
        title: The book's title.
        author: The book's author.
        year: Publication year.
        read: Whether the book has been read.
    """

    id: int
    title: str
    author: str
    year: int
    read: bool


# ── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(
    title="Book Collection API",
    description=(
        "A demo API with JWT authentication. "
        "Use POST /token to get an access token, then include it "
        "as `Authorization: Bearer <token>` on all other requests."
    ),
    version="1.0.0",
)

# Shared collection instance (reloaded from data.json on startup)
collection = BookCollection()


# ── Authentication Endpoint ──────────────────────────────────────────


@app.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """Authenticate and receive a JWT access token.

    Uses OAuth2 "password" flow — send username and password
    as form data. Returns a bearer token for use in the
    Authorization header.

    Args:
        form_data: OAuth2 form with username and password fields.

    Returns:
        A Token containing the access_token and token_type.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    user = authenticate_user(
        form_data.username, form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username}
    )
    return Token(access_token=access_token, token_type="bearer")


# ── Book Endpoints (all protected) ──────────────────────────────────


@app.get("/books", response_model=List[BookResponse])
async def list_books(
    title: Optional[str] = Query(
        None, description="Filter by title (case-insensitive)"
    ),
    author: Optional[str] = Query(
        None, description="Filter by author (case-insensitive)"
    ),
    current_user: User = Depends(get_current_user),
) -> List[BookResponse]:
    """List all books, with optional title or author filters.

    Args:
        title: Optional title search (exact, case-insensitive).
        author: Optional author filter (exact, case-insensitive).
        current_user: The authenticated user (injected by JWT).

    Returns:
        A list of matching books.
    """
    if title:
        book = collection.find_book_by_title(title)
        books = [book] if book else []
    elif author:
        books = collection.find_by_author(author)
    else:
        books = collection.list_books()

    return [
        BookResponse(
            id=b.id,
            title=b.title,
            author=b.author,
            year=b.year,
            read=b.read,
        )
        for b in books
    ]


@app.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_book(
    book_data: BookCreate,
    current_user: User = Depends(get_current_user),
) -> BookResponse:
    """Add a new book to the collection.

    Args:
        book_data: The book's title, author, and year.
        current_user: The authenticated user (injected by JWT).

    Returns:
        The newly created book with its assigned ID.

    Raises:
        HTTPException: 400 if the book data is invalid.
    """
    try:
        book = collection.add_book(
            title=book_data.title,
            author=book_data.author,
            year=book_data.year,
        )
    except InvalidBookDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from None

    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        read=book.read,
    )


@app.get("/books/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
) -> BookResponse:
    """Get a single book by its ID.

    Args:
        book_id: The book's unique integer ID.
        current_user: The authenticated user (injected by JWT).

    Returns:
        The requested book.

    Raises:
        HTTPException: 404 if the book is not found.
    """
    book = collection.find_book_by_id(book_id)
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No book found with id {book_id}",
        )
    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        read=book.read,
    )


@app.delete(
    "/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
) -> None:
    """Remove a book by its ID.

    Args:
        book_id: The book's unique integer ID.
        current_user: The authenticated user (injected by JWT).

    Raises:
        HTTPException: 404 if the book is not found.
    """
    try:
        collection.remove_book(book_id)
    except BookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None


@app.patch(
    "/books/{book_id}/read", response_model=BookResponse
)
async def mark_book_as_read(
    book_id: int,
    current_user: User = Depends(get_current_user),
) -> BookResponse:
    """Mark a book as read.

    Args:
        book_id: The book's unique integer ID.
        current_user: The authenticated user (injected by JWT).

    Returns:
        The updated book.

    Raises:
        HTTPException: 404 if the book is not found.
    """
    try:
        book = collection.mark_as_read(book_id)
    except BookNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from None

    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        read=book.read,
    )
