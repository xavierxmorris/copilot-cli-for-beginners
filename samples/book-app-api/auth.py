"""JWT authentication module for the Book API.

⚠️  DEMO ONLY — not for production use.
This module uses a hardcoded secret key and a single demo user
to teach JWT authentication concepts.

Key concepts demonstrated:
- Password hashing (never store plaintext passwords)
- JWT token creation with expiration
- FastAPI dependency injection for route protection
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


# ── Demo Configuration ──────────────────────────────────────────────
# ⚠️  In production, load SECRET_KEY from environment variables and
#     store users in a real database. This is hardcoded for teaching.
SECRET_KEY = "demo-secret-key-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme tells FastAPI where to find the token
# (the "tokenUrl" must match the login endpoint path)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: The plaintext password.

    Returns:
        The bcrypt hash as a string.
    """
    return bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")


# ── Demo User ───────────────────────────────────────────────────────
# A single pre-seeded user for demonstration purposes.
# The password "password" is stored as a bcrypt hash.
DEMO_USER = {
    "username": "demo",
    "hashed_password": _hash_password("password"),
}


# ── Pydantic Models ─────────────────────────────────────────────────


class Token(BaseModel):
    """Response model for the /token endpoint.

    Attributes:
        access_token: The JWT access token string.
        token_type: Always "bearer" for this API.
    """

    access_token: str
    token_type: str


class User(BaseModel):
    """Represents an authenticated user.

    Attributes:
        username: The user's unique username.
    """

    username: str


# ── Authentication Functions ────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against its bcrypt hash.

    Args:
        plain_password: The password the user typed.
        hashed_password: The stored bcrypt hash.

    Returns:
        True if the password matches, False otherwise.

    Example:
        >>> hashed = _hash_password("secret")
        >>> verify_password("secret", hashed)
        True
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def authenticate_user(
    username: str, password: str
) -> Optional[User]:
    """Validate credentials against the demo user.

    Args:
        username: The username to check.
        password: The plaintext password to verify.

    Returns:
        A User object if credentials are valid, None otherwise.

    Example:
        >>> user = authenticate_user("demo", "password")
        >>> user.username
        'demo'
    """
    if username != DEMO_USER["username"]:
        return None
    if not verify_password(password, DEMO_USER["hashed_password"]):
        return None
    return User(username=username)


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token.

    The token includes the subject ("sub") claim and an expiration
    time. It is signed with HS256 using the demo secret key.

    Args:
        data: Claims to encode in the token (must include "sub").
        expires_delta: Custom expiration time. Defaults to 30 min.

    Returns:
        An encoded JWT string.

    Example:
        >>> token = create_access_token({"sub": "demo"})
        >>> isinstance(token, str)
        True
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """FastAPI dependency that extracts and validates the JWT.

    This is injected into protected routes via FastAPI's Depends()
    system. It decodes the token, checks the "sub" claim, and
    returns the authenticated User.

    Args:
        token: The bearer token extracted from the Authorization
            header by OAuth2PasswordBearer.

    Returns:
        The authenticated User.

    Raises:
        HTTPException: 401 if the token is invalid or expired.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    if username != DEMO_USER["username"]:
        raise credentials_exception

    return User(username=username)
