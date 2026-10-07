"""Unit tests for the auth service (password hashing, users, JWT tokens)."""

import pytest

from backend.services import auth_service
from backend.utils import db


@pytest.fixture(autouse=True)
def fresh_users_table():
    """Each test starts from an empty users table."""
    db.clear_users()


class TestPasswordHashing:
    def test_hash_roundtrip(self):
        hashed = auth_service.hash_password("hunter22!")
        assert hashed != "hunter22!"
        assert auth_service.verify_password("hunter22!", hashed)

    def test_verify_wrong_password(self):
        hashed = auth_service.hash_password("hunter22!")
        assert not auth_service.verify_password("wrong-pass", hashed)

    def test_verify_garbage_hash(self):
        assert not auth_service.verify_password("whatever", "not-a-hash")

    def test_rejects_password_over_bcrypt_limit(self):
        # 80 ASCII chars is schema-legal but exceeds bcrypt's 72-byte cap;
        # must surface as AuthError (-> 400), never ValueError (-> 500).
        with pytest.raises(auth_service.AuthError):
            auth_service.hash_password("a" * 80)


class TestCreateUser:
    def test_creates_user_normalized(self):
        user = auth_service.create_user("  Person@Example.COM ", "password123")
        assert user["email"] == "person@example.com"
        assert user["id"] > 0

    def test_rejects_short_password(self):
        with pytest.raises(auth_service.AuthError):
            auth_service.create_user("short@example.com", "short")

    def test_rejects_duplicate_email(self):
        auth_service.create_user("dup@example.com", "password123")
        with pytest.raises(auth_service.DuplicateEmailError):
            auth_service.create_user("DUP@example.com", "password123")

    def test_password_not_stored_plaintext(self):
        auth_service.create_user("stored@example.com", "password123")
        row = db.get_user_by_email("stored@example.com")
        assert row["password_hash"] != "password123"
        assert row["password_hash"].startswith("$2")


class TestAuthenticate:
    def test_valid_credentials(self):
        auth_service.create_user("login@example.com", "password123")
        user = auth_service.authenticate("login@example.com", "password123")
        assert user["email"] == "login@example.com"

    def test_wrong_password(self):
        auth_service.create_user("login@example.com", "password123")
        with pytest.raises(auth_service.InvalidCredentialsError):
            auth_service.authenticate("login@example.com", "nope-nope")

    def test_unknown_email(self):
        with pytest.raises(auth_service.InvalidCredentialsError):
            auth_service.authenticate("ghost@example.com", "password123")


class TestTokens:
    def test_token_roundtrip(self):
        auth_service.create_user("tok@example.com", "password123")
        user = auth_service.authenticate("tok@example.com", "password123")
        token = auth_service.create_access_token(user)
        resolved = auth_service.get_user_from_token(token)
        assert resolved["email"] == "tok@example.com"

    def test_invalid_token_raises(self):
        with pytest.raises(auth_service.InvalidTokenError):
            auth_service.decode_access_token("not.a.jwt")

    def test_tampered_token_raises(self):
        auth_service.create_user("tok@example.com", "password123")
        user = auth_service.authenticate("tok@example.com", "password123")
        token = auth_service.create_access_token(user)
        with pytest.raises(auth_service.InvalidTokenError):
            auth_service.decode_access_token(token[:-2] + "xx")

    def test_token_signed_with_other_secret_rejected(self):
        """A session must not be forgeable with a known/other key."""
        import jwt as pyjwt

        forged = pyjwt.encode(
            {"sub": "1", "email": "victim@example.com"},
            "attacker-controlled-guess-0123456789abcdef",
            algorithm="HS256",
        )
        with pytest.raises(auth_service.InvalidTokenError):
            auth_service.decode_access_token(forged)

    def test_deleted_user_resolves_to_none(self):
        auth_service.create_user("gone@example.com", "password123")
        user = auth_service.authenticate("gone@example.com", "password123")
        token = auth_service.create_access_token(user)
        db.clear_users()
        assert auth_service.get_user_from_token(token) is None
