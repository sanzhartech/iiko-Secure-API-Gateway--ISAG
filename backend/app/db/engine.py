import os
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base

# Determine database URL. For SQLite we use the async driver aiosqlite.
# Example: sqlite+aiosqlite:///./gateway.db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./gateway.db")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def init_db() -> None:
    """
    Create tables in the database if they do not exist.
    Will be used during FastAPI startup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def run_migrations(database_url: str) -> None:
    """
    Apply Alembic migrations to the configured database.

    This is used by the application startup path so schema changes are managed
    explicitly instead of being inferred from ORM metadata at runtime.
    """
    from alembic import command
    from alembic.config import Config

    backend_root = Path(__file__).resolve().parents[2]
    config = Config(str(backend_root / "alembic.ini"))
    config.set_main_option("script_location", str(backend_root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for async database sessions.
    """
    async with AsyncSessionLocal() as session:
        yield session
