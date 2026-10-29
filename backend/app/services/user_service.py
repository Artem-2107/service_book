from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.user import User
from app.core.security import get_password_hash
from app.schemas.user import UserCreate, UserResponse, PaginatedUsers


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list(self, page: int = 1, page_size: int = 20, search: str = None):
        query = select(User)
        count_query = select(func.count(User.id))
        
        if search:
            pattern = f"%{search}%"
            query = query.where(User.username.ilike(pattern) | User.full_name.ilike(pattern))
            count_query = count_query.where(User.username.ilike(pattern) | User.full_name.ilike(pattern))
        
        total = (await self.session.execute(count_query)).scalar() or 0
        query = query.order_by(User.created_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.session.execute(query)
        items = result.scalars().all()
        pages = max(1, (total + page_size - 1) // page_size)
        
        return {"items": items, "total": total, "page": page, "pages": pages}

    async def get_by_id(self, user_id: int) -> User:
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
        return user

    async def create(self, data: UserCreate) -> User:
        # Проверка уникальности
        existing = await self.session.execute(select(User).where(User.username == data.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Логин уже занят")
        
        existing = await self.session.execute(select(User).where(User.email == data.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email уже занят")
        
        user = User(
            username=data.username,
            email=data.email,
            hashed_password=get_password_hash(data.password),
            full_name=data.full_name,
            role=data.role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user

    async def delete(self, user_id: int):
        user = await self.get_by_id(user_id)
        if user.username == "admin":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Нельзя удалить главного администратора")
        await self.session.delete(user)
        await self.session.flush()