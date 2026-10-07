"""Authentication service: password hashing and JWT session tokens.

Passwords are hashed with bcrypt. Sessions are stateless JWTs that the API
stores in an HttpOnly cookie; a fresh SQLite database means no session table
is required.
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import bcrypt
import jwt

from backend.schemas.auth import MIN_PASSWORD_LENGTH
from backend.utils.config import get_settings
from backend.utils import db

ALGORITHM = "HS256"
COOKIE_NAME = "access_token"
# bcrypt only uses the first 72 bytes of a password; longer input raises
# ValueError, so reject it up front as a domain error instead of a 500.
BCRYPT_MAX_BYTES = 72


class AuthError(Exception):
    """Raised for domain-level authentication failures."""


class DuplicateEmailError(AuthError):
    """Raised when signup is attempted with an already-registered email."""


class InvalidCredentialsError(AuthError):
    """Raised when signin credentials do not match any user."""


class InvalidTokenError(AuthError):
    """Raised when a session token is missing, expired or malformed."""


def hash_password(password: str) -> str:
    """Hash a password with bcrypt (salted automatically)."""
    if len(password.encode("utf-8")) > BCRYPT_MAX_BYTES:
        raise AuthError(
            f"Password must be at most {BCRYPT_MAX_BYTES} bytes long"
        )
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Check a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def create_user(email: str, password: str) -> Dict:
    """Register a new user. Returns the public user dict.

    Raises:
        DuplicateEmailError: if the email is already registered.
        AuthError: if the password does not meet requirements.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise AuthError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
        )

    normalized_email = email.strip().lower()
    if db.get_user_by_email(normalized_email) is not None:
        raise DuplicateEmailError("Email is already registered")

    try:
        user = db.create_user(normalized_email, hash_password(password))
    except Exception as exc:  # pragma: no cover - race on duplicate email
        if "UNIQUE" in str(exc).upper():
            raise DuplicateEmailError("Email is already registered") from exc
        raise

    return {"id": user["id"], "email": user["email"]}


def authenticate(email: str, password: str) -> Dict:
    """Verify credentials and return the public user dict.

    Raises:
        InvalidCredentialsError: if no user matches or the password is wrong.
    """
    user = db.get_user_by_email(email.strip().lower())
    if user is None or not verify_password(password, user["password_hash"]):
        raise InvalidCredentialsError("Invalid email or password")
    return {"id": user["id"], "email": user["email"]}


def create_access_token(user: Dict) -> str:
    """Create a signed JWT for the given user."""
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict:
    """Decode and validate a JWT. Returns the token payload.

    Raises:
        InvalidTokenError: if the token is expired or otherwise invalid.
    """
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid or expired session") from exc


def get_user_from_token(token: str) -> Optional[Dict]:
    """Resolve a JWT to its user, or None if the user no longer exists."""
    payload = decode_access_token(token)
    try:
        user_id = int(payload.get("sub", ""))
    except (TypeError, ValueError):
        raise InvalidTokenError("Invalid or expired session")
    return db.get_user_by_id(user_id)
