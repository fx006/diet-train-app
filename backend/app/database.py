"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    # SQLite specific configuration
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    # MySQL specific configuration
    pool_pre_ping=True if "mysql" in settings.database_url else False,
    pool_size=10 if "mysql" in settings.database_url else 5,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
