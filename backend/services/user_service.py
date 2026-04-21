from typing import Optional
from fastapi import HTTPException, status
from auth import hash_password, verify_password, create_access_token
from repositories.user_repo import UserRepository
from models.user import User


class UserService:
    @staticmethod
    async def register(email: str, password: str, role: str) -> User:
        existing = await UserRepository.get_by_email(email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        
        password_hash = hash_password(password)
        return await UserRepository.create(email, password_hash, role)

    @staticmethod
    async def login(email: str, password: str) -> dict:
        user = await UserRepository.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        
        access_token = create_access_token({"sub": str(user.user_id)})
        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    async def get_user(user_id: int) -> Optional[User]:
        user = await UserRepository.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    @staticmethod
    async def delete_user(user_id: int) -> bool:
        result = await UserRepository.delete(user_id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return True
    
    @staticmethod
    async def update_role(user_id: int, role: str) -> User:
        if role not in ["candidate", "recruiter"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

        updated = await UserRepository.update_role(user_id, role)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return updated
