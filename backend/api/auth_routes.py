"""Authentication routes: signup, signin, signout, current user."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from typing import Optional

from backend.schemas.auth import (
    AuthResponse,
    SigninRequest,
    SignupRequest,
    UserResponse,
)
from backend.services import auth_service
from backend.services.auth_service import COOKIE_NAME
from backend.utils.config import get_settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _set_session_cookie(response: Response, token: str) -> None:
    """Attach the JWT session cookie (HttpOnly so JS cannot read it)."""
    settings = get_settings()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        httponly=True,
        samesite="lax",
        secure=False,  # app is served over plain HTTP in dev/container
        path="/",
    )


def _start_session(response: Response, user: dict, message: str) -> AuthResponse:
    """Issue the session cookie and build the response for a signed-in user."""
    _set_session_cookie(response, auth_service.create_access_token(user))
    return AuthResponse(message=message, user=UserResponse(**user))


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
async def signup(request: SignupRequest, response: Response):
    """Create a new user account and start a session."""
    try:
        user = auth_service.create_user(request.email, request.password)
    except auth_service.DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except auth_service.AuthError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return _start_session(response, user, "Account created")


@router.post("/signin", response_model=AuthResponse)
async def signin(request: SigninRequest, response: Response):
    """Verify credentials and start a session."""
    try:
        user = auth_service.authenticate(request.email, request.password)
    except auth_service.InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        )

    return _start_session(response, user, "Signed in")


@router.post("/signout", status_code=status.HTTP_200_OK)
async def signout(response: Response):
    """Clear the session cookie."""
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"message": "Signed out"}


def _current_user(access_token: Optional[str] = Cookie(default=None)) -> dict:
    """Dependency: resolve the session cookie to a user, or 401."""
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not signed in"
        )
    try:
        user = auth_service.get_user_from_token(access_token)
    except auth_service.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session"
        )
    return user


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(_current_user)):
    """Return the currently signed-in user."""
    return UserResponse(id=user["id"], email=user["email"])
