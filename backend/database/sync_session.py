"""Session synchrone SQLAlchemy pour les endpoints FastAPI"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from backend.config.settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=2,
    pool_recycle=3600,
)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_sync_db():
    """Dependency FastAPI pour obtenir une session DB synchrone."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
