from __future__ import annotations

from pydantic import Field

from jobconnect.modules.api.shared import APIModel, Role, UserStatus


class UserSummary(APIModel):
    user_id: int
    email: str
    role: Role
    status: UserStatus
    created_at: str


class AuthResponse(APIModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserSummary


class RegisterRequest(APIModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)
    role: Role


class LoginRequest(APIModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str
