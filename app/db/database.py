"""
Database session configuration.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import SQLALCHEMY_DATABASE_URL

# Create database engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    """
    Dependency function that provides a SQLAlchemy session.
    Yields a session and ensures it gets closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 