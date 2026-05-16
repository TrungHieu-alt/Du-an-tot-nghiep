from __future__ import annotations

from fastapi import APIRouter, Depends

from jobconnect.modules.api.shared import CurrentUser, current_user
from jobconnect.modules.auth.schemas import AuthResponse, LoginRequest, RegisterRequest
from jobconnect.modules.auth import service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: RegisterRequest) -> AuthResponse:
    return service.register(request)


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest) -> AuthResponse:
    return service.login(request)


@router.post("/logout", status_code=204)
def logout(_: CurrentUser = Depends(current_user)):
    return service.logout()
