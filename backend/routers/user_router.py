from fastapi import APIRouter, status
from schemas.user_schema import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register(req: UserRegisterRequest):
    user = await UserService.register(req.email, req.password, req.role)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest):
    return await UserService.login(req.email, req.password)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return await UserService.get_user(user_id)


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
async def delete_user(user_id: int):
    await UserService.delete_user(user_id)
    return {"message": "User deleted"}

@router.put("/{user_id}/role", response_model=UserResponse)
async def update_role(user_id: int, payload: dict):
    role = payload.get("role")
    return await UserService.update_role(user_id, role)
