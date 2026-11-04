from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repo import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.user import UserCreate, Token, UserResponse


class AuthService:
    def __init__(self, session: AsyncSession):
        self.repo = UserRepository(session)

    async def register(self, data: UserCreate):
        if await self.repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Логин уже занят")
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже занят")
        return await self.repo.create(
            username=data.username, email=data.email, password=data.password,
            full_name=data.full_name, role=data.role,
        )

    async def login(self, username: str, password: str) -> Token:
        user = await self.repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный логин или пароль")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Пользователь деактивирован")
        # ИСПРАВЛЕНО: str(user.id) вместо user.id
        token = create_access_token(data={"sub": str(user.id), "role": user.role.value})
        return Token(access_token=token, user=UserResponse.model_validate(user))