"""Configuration de la session SQLAlchemy"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.config.settings import settings

# Remplacer postgresql:// par postgresql+asyncpg:// pour l'async
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """Dependency FastAPI pour obtenir une session DB."""
    async with async_session() as session:
        yield session
