"""Integration tests for the /api/auth endpoints (cookie-based sessions)."""

SESSION_COOKIE = "access_token"


class TestSignup:
    def test_signup_returns_201_and_sets_cookie(self, client):
        response = client.post(
            "/api/auth/signup",
            json={"email": "new@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        body = response.json()
        assert body["user"]["email"] == "new@example.com"
        assert "id" in body["user"]
        assert SESSION_COOKIE in response.cookies
        # HttpOnly: JS cannot read the token
        set_cookie = response.headers["set-cookie"]
        assert "HttpOnly" in set_cookie
        assert "SameSite=lax" in set_cookie

    def test_signup_duplicate_email_conflict(self, client, registered_user):
        response = client.post("/api/auth/signup", json=registered_user)
        assert response.status_code == 409

    def test_signup_short_password_rejected(self, client):
        response = client.post(
            "/api/auth/signup",
            json={"email": "short@example.com", "password": "abc"},
        )
        assert response.status_code == 422

    def test_signup_invalid_email_rejected(self, client):
        response = client.post(
            "/api/auth/signup",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert response.status_code == 422

    def test_signup_overlong_password_400_not_500(self, client):
        """80-char password is schema-valid but exceeds bcrypt's 72 bytes."""
        response = client.post(
            "/api/auth/signup",
            json={"email": "long@example.com", "password": "a" * 80},
        )
        assert response.status_code == 400


class TestSignin:
    def test_signin_success(self, client, registered_user):
        response = client.post("/api/auth/signin", json=registered_user)
        assert response.status_code == 200
        assert response.json()["user"]["email"] == registered_user["email"]
        assert SESSION_COOKIE in response.cookies

    def test_signin_wrong_password(self, client, registered_user):
        response = client.post(
            "/api/auth/signin",
            json={"email": registered_user["email"], "password": "wrong-pass"},
        )
        assert response.status_code == 401

    def test_signin_unknown_user(self, client):
        response = client.post(
            "/api/auth/signin",
            json={"email": "ghost@example.com", "password": "password123"},
        )
        assert response.status_code == 401


class TestMe:
    def test_me_without_cookie_unauthorized(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_me_after_signup(self, client):
        client.post(
            "/api/auth/signup",
            json={"email": "me@example.com", "password": "password123"},
        )
        response = client.get("/api/auth/me")
        assert response.status_code == 200
        assert response.json() == {"id": response.json()["id"], "email": "me@example.com"}

    def test_me_with_garbage_cookie_unauthorized(self, client):
        client.cookies.set(SESSION_COOKIE, "garbage-token")
        assert client.get("/api/auth/me").status_code == 401

    def test_me_with_forged_cookie_unauthorized(self, client):
        """A token signed with a different key must not authenticate."""
        import jwt as pyjwt

        forged = pyjwt.encode(
            {"sub": "1", "email": "victim@example.com"},
            "attacker-controlled-guess-0123456789abcdef",
            algorithm="HS256",
        )
        client.cookies.set(SESSION_COOKIE, forged)
        assert client.get("/api/auth/me").status_code == 401


class TestSignout:
    def test_signout_clears_session(self, client, registered_user):
        client.post("/api/auth/signin", json=registered_user)
        assert client.get("/api/auth/me").status_code == 200

        response = client.post("/api/auth/signout")
        assert response.status_code == 200

        # Cookie cleared client-side; session no longer usable
        assert client.get("/api/auth/me").status_code == 401
