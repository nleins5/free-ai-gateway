import ssl as _ssl
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def _build_engine():
    """Build async engine with proper SSL handling for Neon/PostgreSQL."""
    url = DATABASE_URL

    # Convert postgres:// to postgresql+asyncpg://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip sslmode param (asyncpg handles SSL differently)
    clean_url = url
    for param in ["?sslmode=require", "&sslmode=require", "?sslmode=prefer", "&sslmode=prefer"]:
        clean_url = clean_url.replace(param, "")
    # Clean up dangling ? or &
    if clean_url.endswith("?"):
        clean_url = clean_url[:-1]

    # Create SSL context for Neon
    ssl_context = _ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = _ssl.CERT_NONE

    return create_async_engine(
        clean_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={"ssl": ssl_context},
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db():
    """Create all tables on startup."""
    from app.db_models import User, Conversation, ChatMessage, RequestLog  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
