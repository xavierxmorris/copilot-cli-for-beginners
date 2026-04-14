"""Tests for the Book Collection API (with JWT authentication).

Covers: registration, login, logout (token blocklist), protected routes,
expired tokens, malformed tokens, and book CRUD behind authentication.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest

# Add parent directory to path so we can import the app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import (  # noqa: E402
    JWT_ALGORITHM,
    JWT_SECRET,
    app,
    blocked_tokens,
    users,
)
import books  # noqa: E402


@pytest.fixture(autouse=True)
def use_temp_data_file(tmp_path, monkeypatch):
    """Redirect DATA_FILE to a temp directory for test isolation."""
    temp_file = tmp_path / "data.json"
    temp_file.write_text("[]")
    monkeypatch.setattr(books, "DATA_FILE", str(temp_file))
    from app import collection
    collection.load_books()
    # Clear in-memory stores between tests
    users.clear()
    blocked_tokens.clear()
    return temp_file


@pytest.fixture
def client():
    """Create a Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def _register_and_login(client, username="alice", password="secret123"):
    """Helper: register a user, log in, return the Authorization header dict."""
    client.post("/register", json={
        "username": username, "password": password
    })
    resp = client.post("/login", json={
        "username": username, "password": password
    })
    token = resp.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_header(client):
    """Return Authorization headers for a registered+logged-in user."""
    return _register_and_login(client)


# --- Registration tests ---


class TestRegister:
    def test_register_success(self, client):
        response = client.post("/register", json={
            "username": "alice", "password": "secret123"
        })
        assert response.status_code == 201
        assert "registered" in response.get_json()["message"]

    def test_register_duplicate_username(self, client):
        client.post("/register", json={
            "username": "alice", "password": "secret123"
        })
        response = client.post("/register", json={
            "username": "alice", "password": "other"
        })
        assert response.status_code == 400
        assert "already exists" in response.get_json()["error"]

    def test_register_missing_username(self, client):
        response = client.post("/register", json={"password": "secret123"})
        assert response.status_code == 400

    def test_register_missing_password(self, client):
        response = client.post("/register", json={"username": "bob"})
        assert response.status_code == 400

    def test_register_empty_username(self, client):
        response = client.post("/register", json={
            "username": "  ", "password": "secret123"
        })
        assert response.status_code == 400

    def test_register_empty_password(self, client):
        response = client.post("/register", json={
            "username": "bob", "password": ""
        })
        assert response.status_code == 400


# --- Login tests ---


class TestLogin:
    def test_login_success_returns_token(self, client):
        client.post("/register", json={
            "username": "alice", "password": "secret123"
        })
        response = client.post("/login", json={
            "username": "alice", "password": "secret123"
        })
        assert response.status_code == 200
        data = response.get_json()
        assert "token" in data
        # Verify the token is valid
        decoded = pyjwt.decode(
            data["token"], JWT_SECRET, algorithms=[JWT_ALGORITHM]
        )
        assert decoded["sub"] == "alice"

    def test_login_wrong_password(self, client):
        client.post("/register", json={
            "username": "alice", "password": "secret123"
        })
        response = client.post("/login", json={
            "username": "alice", "password": "wrong"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client):
        response = client.post("/login", json={
            "username": "nobody", "password": "secret123"
        })
        assert response.status_code == 401

    def test_login_missing_fields(self, client):
        response = client.post("/login", json={})
        assert response.status_code == 401


# --- Logout tests (token blocklist) ---


class TestLogout:
    def test_logout_revokes_token(self, client, auth_header):
        response = client.post("/logout", headers=auth_header)
        assert response.status_code == 200
        assert "Logged out" in response.get_json()["message"]
        # Token should now be blocked
        response = client.get("/books", headers=auth_header)
        assert response.status_code == 401
        assert "revoked" in response.get_json()["error"]

    def test_logout_without_token(self, client):
        response = client.post("/logout")
        assert response.status_code == 400
        assert "No token" in response.get_json()["error"]


# --- Protected route tests ---


class TestProtectedRoutes:
    def test_list_books_requires_token(self, client):
        response = client.get("/books")
        assert response.status_code == 401
        assert "Login required" in response.get_json()["error"]

    def test_add_book_requires_token(self, client):
        response = client.post("/books", json={
            "title": "Test", "author": "Author", "year": 2000
        })
        assert response.status_code == 401

    def test_remove_book_requires_token(self, client):
        response = client.delete("/books/Test")
        assert response.status_code == 401

    def test_mark_as_read_requires_token(self, client):
        response = client.put("/books/Test/read")
        assert response.status_code == 401

    def test_search_requires_token(self, client):
        response = client.get("/books/search?author=Test")
        assert response.status_code == 401

    def test_health_is_public(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_register_is_public(self, client):
        response = client.post("/register", json={
            "username": "test", "password": "test"
        })
        assert response.status_code == 201

    def test_login_is_public(self, client):
        response = client.post("/login", json={
            "username": "test", "password": "test"
        })
        # 401 because user doesn't exist, not "Login required"
        assert response.status_code == 401
        assert "Invalid credentials" in response.get_json()["error"]


# --- Token edge cases ---


class TestTokenEdgeCases:
    def test_expired_token(self, client):
        client.post("/register", json={
            "username": "alice", "password": "secret123"
        })
        # Manually create an already-expired token
        payload = {
            "sub": "alice",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = pyjwt.encode(
            payload, JWT_SECRET, algorithm=JWT_ALGORITHM
        )
        response = client.get("/books", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert response.status_code == 401
        assert "expired" in response.get_json()["error"]

    def test_malformed_token(self, client):
        response = client.get("/books", headers={
            "Authorization": "Bearer not-a-real-jwt"
        })
        assert response.status_code == 401
        assert "Invalid token" in response.get_json()["error"]

    def test_missing_bearer_prefix(self, client):
        response = client.get("/books", headers={
            "Authorization": "Token abc123"
        })
        assert response.status_code == 401
        assert "Login required" in response.get_json()["error"]

    def test_wrong_secret(self, client):
        payload = {
            "sub": "alice",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=7),
        }
        bad_token = pyjwt.encode(payload, "wrong-secret", algorithm="HS256")
        response = client.get("/books", headers={
            "Authorization": f"Bearer {bad_token}"
        })
        assert response.status_code == 401
        assert "Invalid token" in response.get_json()["error"]


# --- Book CRUD tests (authenticated) ---


class TestListBooks:
    def test_empty_collection(self, client, auth_header):
        response = client.get("/books", headers=auth_header)
        assert response.status_code == 200
        assert response.get_json() == []

    def test_returns_seeded_books(self, client, auth_header, use_temp_data_file):
        use_temp_data_file.write_text(json.dumps([
            {"title": "Dune", "author": "Frank Herbert", "year": 1965, "read": False}
        ]))
        from app import collection
        collection.load_books()

        response = client.get("/books", headers=auth_header)
        data = response.get_json()
        assert len(data) == 1
        assert data[0]["title"] == "Dune"


class TestAddBook:
    def test_add_valid_book(self, client, auth_header):
        response = client.post("/books", json={
            "title": "1984",
            "author": "George Orwell",
            "year": 1949,
        }, headers=auth_header)
        assert response.status_code == 201
        assert response.get_json()["title"] == "1984"

    def test_add_book_invalid_year(self, client, auth_header):
        response = client.post("/books", json={
            "title": "Bad Book",
            "author": "Nobody",
            "year": -5,
        }, headers=auth_header)
        assert response.status_code == 400
        assert "error" in response.get_json()


class TestRemoveBook:
    def test_remove_existing_book(self, client, auth_header):
        client.post("/books", json={
            "title": "Temp", "author": "Author", "year": 2000
        }, headers=auth_header)
        response = client.delete("/books/Temp", headers=auth_header)
        assert response.status_code == 200

    def test_remove_nonexistent_book(self, client, auth_header):
        response = client.delete("/books/NoSuchBook", headers=auth_header)
        assert response.status_code == 404


class TestHealth:
    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"
