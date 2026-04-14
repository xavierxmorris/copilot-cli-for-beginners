"""Book Collection REST API.

A minimal Flask API wrapping the BookCollection class, with
JWT-based authentication (username/password).

Usage:
    pip install -r requirements.txt
    python app.py
"""

import os
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

from books import (
    BookCollection,
    BookError,
    BookNotFoundError,
    InvalidBookDataError,
)

app = Flask(__name__)
collection = BookCollection()

# WARNING: Use a real secret in production. Set JWT_SECRET_KEY env var.
JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "dev-secret-do-not-use-in-prod")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_MINUTES = 7

# In-memory user store (demo only — resets on restart)
users: dict[str, str] = {}

# In-memory token blocklist (demo only — resets on restart)
blocked_tokens: set[str] = set()


# --- Authentication helpers ---


def login_required(f):
    """Decorator that returns 401 if a valid JWT is not provided."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Login required."}), 401

        token = auth_header[7:]  # strip "Bearer "

        if token in blocked_tokens:
            return jsonify({"error": "Token has been revoked."}), 401

        try:
            jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token."}), 401

        return f(*args, **kwargs)

    return decorated


# --- Auth endpoints ---


@app.route("/register", methods=["POST"])
def register():
    """Register a new user with username and password."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required."}), 400
    if username in users:
        return jsonify({"error": "Username already exists."}), 400

    users[username] = generate_password_hash(password)
    return jsonify({"message": f"User '{username}' registered."}), 201


@app.route("/login", methods=["POST"])
def login():
    """Log in with username and password. Returns a JWT token."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if username not in users:
        return jsonify({"error": "Invalid credentials."}), 401
    if not check_password_hash(users[username], password):
        return jsonify({"error": "Invalid credentials."}), 401

    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRY_MINUTES),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return jsonify({"token": token})


@app.route("/logout", methods=["POST"])
def logout():
    """Revoke the current JWT token by adding it to the blocklist."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "No token provided."}), 400

    token = auth_header[7:]
    blocked_tokens.add(token)
    return jsonify({"message": "Logged out."})


# --- Book endpoints (login required) ---


@app.route("/books", methods=["GET"])
@login_required
def list_books():
    """Return all books in the collection."""
    return jsonify([asdict(b) for b in collection.list_books()])


@app.route("/books", methods=["POST"])
@login_required
def add_book():
    """Add a new book. Expects JSON with title, author, year."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "")
    author = data.get("author", "")
    year = data.get("year", 0)

    try:
        book = collection.add_book(title, author, year)
        return jsonify(asdict(book)), 201
    except InvalidBookDataError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/books/<title>", methods=["DELETE"])
@login_required
def remove_book(title: str):
    """Remove a book by title."""
    try:
        collection.remove_book(title)
        return jsonify({"message": f"'{title}' removed."})
    except BookNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/books/<title>/read", methods=["PUT"])
@login_required
def mark_as_read(title: str):
    """Mark a book as read."""
    try:
        collection.mark_as_read(title)
        return jsonify({"message": f"'{title}' marked as read."})
    except BookNotFoundError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/books/search", methods=["GET"])
@login_required
def find_by_author():
    """Find books by author. Pass ?author=<name> as a query parameter."""
    author = request.args.get("author", "")
    if not author:
        return jsonify({"error": "Missing 'author' query parameter."}), 400
    results = collection.find_by_author(author)
    return jsonify([asdict(b) for b in results])


# --- Health check ---


@app.route("/health", methods=["GET"])
def health():
    """Simple health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
