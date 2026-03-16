# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import async_session_maker


# сессия для прямого использования (Celery)
AsyncSessionLocal = async_session_maker


async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        # async with session.begin():
        yield session
