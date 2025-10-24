"""
Database connection management.
Handles SQLAlchemy engine, session factory, and database initialization.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for declarative models
Base = declarative_base()


# PUBLIC_INTERFACE
def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    
    Yields:
        SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# PUBLIC_INTERFACE
def init_db():
    """
    Initialize the database by creating all tables.
    Should be called on application startup.
    """
    import src.database.models  # noqa: F401 - Import to register models
    Base.metadata.create_all(bind=engine)
