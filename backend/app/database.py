"""
Модуль работы с БД через SQLAlchemy 2.0 с асинхронными сессиями.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# Создаём асинхронный движок для PostgreSQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=10,        # Размер пула соединений
    max_overflow=20,     # Максимум дополнительных соединений
)

# Фабрика сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для FastAPI — выдаёт сессию БД на каждый запрос.
    Сессия автоматически закрывается после использования.
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Создание таблиц (используется только для тестов, в проде — Alembic)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)