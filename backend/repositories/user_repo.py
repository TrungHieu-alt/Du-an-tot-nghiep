from typing import Optional
from models.user import User


class UserRepository:
    @staticmethod
    async def create(email: str, password_hash: str, role: str) -> User:
        last_user = await User.find().sort([("user_id", -1)]).limit(1).to_list(1)
        user_id = (last_user[0].user_id + 1) if last_user else 1

        user = User(user_id=user_id, email=email, password_hash=password_hash, role=role)
        await user.insert()
        return user

    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        return await User.find_one(User.user_id == user_id)

    @staticmethod
    async def get_by_email(email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    @staticmethod
    async def delete(user_id: int) -> bool:
        result = await User.find_one(User.user_id == user_id)
        if result:
            await result.delete()
            return True
        return False
    
    @staticmethod
    async def update_role(user_id: int, role: str) -> Optional[User]:
        user = await User.find_one(User.user_id == user_id)
        if not user:
            return None
        user.role = role
        await user.save()
        return user