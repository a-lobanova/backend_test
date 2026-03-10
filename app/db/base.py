# base.py
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.settings import settings

engine = create_async_engine(settings.ASYNC_DATABASE_URL)  # движок БД async
async_session_maker = async_sessionmaker(engine, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
