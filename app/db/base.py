# base.py
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.settings import settings

# from app.models import *


# --- engine ---
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,  # True, если хочешь видеть SQL в логах
)


# --- session factory ---
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass
