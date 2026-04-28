"""
Async SQLAlchemy engine, session factory, and dependency for FastAPI.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from core.config import settings  # see config.py below

# asyncpg driver: postgresql+asyncpg://user:pass@host/db
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,          # set True only in dev to log SQL
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,             # drop stale connections automatically
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,         # keep attrs accessible after commit
)


async def get_db() -> AsyncSession:
    """FastAPI dependency — yields a DB session, closes it after the request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def create_tables():
    """
    Called once at startup (dev only).
    In production, use Alembic migrations instead.
    """
    from persistence.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)