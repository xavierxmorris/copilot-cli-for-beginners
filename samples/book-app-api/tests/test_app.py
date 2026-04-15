"""Tests for the Book Collection API with JWT authentication.

Follows project test standards:
- Group related tests in classes
- Use descriptive names: test_<what>_<condition>_<expected>
- Order: happy path → edge cases → error cases
- Use tmp_path + monkeypatch for data file isolation
"""

import sys
import os

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..")
)

import pytest

import books
from books import BookCollection
from auth import (
    authenticate_user,
    create_access_token,
    verify_password,
    _hash_password,
)

from fastapi.testclient import TestClient
from app import app, collection


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Redirect DATA_FILE to a temp directory for every test."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    # Reload the shared collection so it uses the temp file
    collection.books = []
    collection.load_books()
    return temp_file


@pytest.fixture
def client():
    """Provide a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    """Get valid Authorization headers for the demo user."""
    response = client.post(
        "/token",
        data={"username": "demo", "password": "password"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def populated_collection(auth_headers, client):
    """Add sample books and return the auth headers."""
    sample_books = [
        {
            "title": "Dune",
            "author": "Frank Herbert",
            "year": 1965,
        },
        {
            "title": "Neuromancer",
            "author": "William Gibson",
            "year": 1984,
        },
        {
            "title": "Foundation",
            "author": "Isaac Asimov",
            "year": 1951,
        },
    ]
    for book_data in sample_books:
        client.post(
            "/books",
            json=book_data,
            headers=auth_headers,
        )
    return auth_headers


# ── Auth Unit Tests ──────────────────────────────────────────────────


class TestVerifyPassword:
    """Tests for password hashing and verification."""

    def test_correct_password_returns_true(self):
        hashed = _hash_password("secret")
        assert verify_password("secret", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = _hash_password("secret")
        assert verify_password("wrong", hashed) is False


class TestAuthenticateUser:
    """Tests for the authenticate_user function."""

    def test_valid_credentials_returns_user(self):
        user = authenticate_user("demo", "password")
        assert user is not None
        assert user.username == "demo"

    def test_wrong_username_returns_none(self):
        result = authenticate_user("unknown", "password")
        assert result is None

    def test_wrong_password_returns_none(self):
        result = authenticate_user("demo", "wrongpass")
        assert result is None


# ── Token Endpoint Tests ─────────────────────────────────────────────


class TestLogin:
    """Tests for POST /token."""

    def test_login_success_returns_token(self, client):
        response = client.post(
            "/token",
            data={"username": "demo", "password": "password"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client):
        response = client.post(
            "/token",
            data={"username": "demo", "password": "wrong"},
        )
        assert response.status_code == 401
        assert "Incorrect" in response.json()["detail"]

    def test_login_wrong_username_returns_401(self, client):
        response = client.post(
            "/token",
            data={"username": "nobody", "password": "password"},
        )
        assert response.status_code == 401


# ── Unauthorized Access Tests ────────────────────────────────────────


class TestUnauthorized:
    """All book endpoints reject requests without a valid token."""

    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/books"),
            ("POST", "/books"),
            ("GET", "/books/1"),
            ("DELETE", "/books/1"),
            ("PATCH", "/books/1/read"),
        ],
    )
    def test_endpoint_without_token_returns_401(
        self, client, method, path
    ):
        response = client.request(method, path)
        assert response.status_code == 401

    def test_invalid_token_returns_401(self, client):
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/books", headers=headers)
        assert response.status_code == 401

    def test_expired_token_returns_401(self, client):
        from datetime import timedelta

        token = create_access_token(
            data={"sub": "demo"},
            expires_delta=timedelta(seconds=-1),
        )
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/books", headers=headers)
        assert response.status_code == 401


# ── Book CRUD Tests ──────────────────────────────────────────────────


class TestCreateBook:
    """Tests for POST /books."""

    def test_create_book_returns_201(
        self, client, auth_headers
    ):
        response = client.post(
            "/books",
            json={
                "title": "Dune",
                "author": "Frank Herbert",
                "year": 1965,
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Dune"
        assert data["id"] == 1
        assert data["read"] is False

    def test_create_book_increments_id(
        self, client, auth_headers
    ):
        client.post(
            "/books",
            json={
                "title": "Book 1",
                "author": "Author",
                "year": 2000,
            },
            headers=auth_headers,
        )
        response = client.post(
            "/books",
            json={
                "title": "Book 2",
                "author": "Author",
                "year": 2001,
            },
            headers=auth_headers,
        )
        assert response.json()["id"] == 2

    def test_create_book_empty_title_returns_422(
        self, client, auth_headers
    ):
        response = client.post(
            "/books",
            json={
                "title": "",
                "author": "Author",
                "year": 2000,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_create_book_invalid_year_returns_422(
        self, client, auth_headers
    ):
        response = client.post(
            "/books",
            json={
                "title": "Book",
                "author": "Author",
                "year": 0,
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestListBooks:
    """Tests for GET /books."""

    def test_list_empty_collection_returns_empty(
        self, client, auth_headers
    ):
        response = client.get("/books", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_list_returns_all_books(
        self, client, populated_collection
    ):
        response = client.get(
            "/books", headers=populated_collection
        )
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_filter_by_title(
        self, client, populated_collection
    ):
        response = client.get(
            "/books?title=Dune",
            headers=populated_collection,
        )
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Dune"

    def test_filter_by_author(
        self, client, populated_collection
    ):
        response = client.get(
            "/books?author=Isaac%20Asimov",
            headers=populated_collection,
        )
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Foundation"

    def test_filter_by_title_not_found(
        self, client, populated_collection
    ):
        response = client.get(
            "/books?title=Nonexistent",
            headers=populated_collection,
        )
        assert len(response.json()) == 0


class TestGetBook:
    """Tests for GET /books/{id}."""

    def test_get_existing_book(
        self, client, populated_collection
    ):
        response = client.get(
            "/books/1", headers=populated_collection
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Dune"

    def test_get_nonexistent_book_returns_404(
        self, client, auth_headers
    ):
        response = client.get(
            "/books/999", headers=auth_headers
        )
        assert response.status_code == 404


class TestDeleteBook:
    """Tests for DELETE /books/{id}."""

    def test_delete_existing_book(
        self, client, populated_collection
    ):
        response = client.delete(
            "/books/1", headers=populated_collection
        )
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(
            "/books/1", headers=populated_collection
        )
        assert response.status_code == 404

    def test_delete_nonexistent_book_returns_404(
        self, client, auth_headers
    ):
        response = client.delete(
            "/books/999", headers=auth_headers
        )
        assert response.status_code == 404


class TestMarkAsRead:
    """Tests for PATCH /books/{id}/read."""

    def test_mark_as_read_returns_updated_book(
        self, client, populated_collection
    ):
        response = client.patch(
            "/books/1/read", headers=populated_collection
        )
        assert response.status_code == 200
        assert response.json()["read"] is True

    def test_mark_nonexistent_book_returns_404(
        self, client, auth_headers
    ):
        response = client.patch(
            "/books/999/read", headers=auth_headers
        )
        assert response.status_code == 404
