from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .app_config import get_settings

settings = get_settings()

# For SQLite, need check_same_thread, but for PostgreSQL it's not needed.
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# PUBLIC_INTERFACE
def get_db():
    """Yield a database session and ensure it is closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
