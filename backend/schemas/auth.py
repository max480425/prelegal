from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# Single source of truth for the password policy (schema + service share it).
MIN_PASSWORD_LENGTH = 8


class SignupRequest(BaseModel):
    """Request to create a new user account."""
    email: EmailStr
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=128)


class SigninRequest(BaseModel):
    """Request to sign in an existing user."""
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    """Public representation of a user (never includes password hash)."""
    id: int
    email: str


class AuthResponse(BaseModel):
    """Response returned by signup/signin."""
    message: str
    user: UserResponse
