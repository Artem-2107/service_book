from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, engine, async_session
from app.models.user import User, UserRole
from app.core.security import get_password_hash
from app.routers import (
    auth_router, users_router, clients_router,
    cars_router, orders_router, stats_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _create_default_users()
    print("✅ Приложение запущено")
    yield


app = FastAPI(title="ServiceBook API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(clients_router, prefix="/api")
app.include_router(cars_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(stats_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "ServiceBook API is running"}


async def _create_default_users():
    """Создание пользователей всех ролей при первом запуске."""
    defaults = [
        {"username": "admin", "email": "admin@servicebook.ru", "password": "admin123",
         "full_name": "Администратор", "role": UserRole.ADMIN},
        {"username": "manager", "email": "manager@servicebook.ru", "password": "manager123",
         "full_name": "Мастер-приёмщик", "role": UserRole.MANAGER},
        {"username": "accountant", "email": "accountant@servicebook.ru", "password": "accountant123",
         "full_name": "Бухгалтер", "role": UserRole.ACCOUNTANT},
    ]
    async with async_session() as session:
        for data in defaults:
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.username == data["username"]))
            if not result.scalar_one_or_none():
                user = User(
                    username=data["username"],
                    email=data["email"],
                    hashed_password=get_password_hash(data["password"]),
                    full_name=data["full_name"],
                    role=data["role"],
                    is_active=True,
                )
                session.add(user)
                print(f"✅ Создан пользователь {data['username']} / {data['password']} (роль: {data['role'].value})")
        await session.commit()