"""
Database connection and session management.

Supports:
- SQLite (default, development)
- PostgreSQL (production-ready)
- Connection pooling
- Automatic session management
"""

import os
from typing import Optional
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool

from app.database.models import Base


class DatabaseConfig:
    """Configuration for database connection."""
    
    # Use SQLite by default (development), PostgreSQL in production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./networking_automation.db"
    )
    
    # Use SQLite in-memory for testing
    TEST_DATABASE_URL: str = "sqlite:///:memory:"
    
    @classmethod
    def get_url(cls, is_test: bool = False) -> str:
        """Get database URL."""
        return cls.TEST_DATABASE_URL if is_test else cls.DATABASE_URL


class Database:
    """Database connection and session management."""
    
    _instance: Optional["Database"] = None
    _engine = None
    _SessionLocal = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, database_url: Optional[str] = None, is_test: bool = False):
        """
        Initialize database connection.
        
        Args:
            database_url: Override default URL
            is_test: Use test database
        """
        db = cls()
        
        # Determine URL
        url = database_url or DatabaseConfig.get_url(is_test)
        
        # Create engine
        if url.startswith("sqlite"):
            # SQLite configuration
            db._engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool if is_test else QueuePool,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
        else:
            # PostgreSQL configuration
            db._engine = create_engine(
                url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Test connections before using
                echo=os.getenv("SQL_ECHO", "false").lower() == "true"
            )
        
        # Create session factory
        db._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db._engine)
        
        # Create tables
        Base.metadata.create_all(bind=db._engine)
        
        return db
    
    @classmethod
    def get_session(cls) -> Session:
        """Get new database session."""
        db = cls()
        if db._SessionLocal is None:
            db.initialize()
        return db._SessionLocal()
    
    @classmethod
    def create_tables(cls):
        """Create all tables."""
        db = cls()
        if db._engine is None:
            db.initialize()
        Base.metadata.create_all(bind=db._engine)
    
    @classmethod
    def drop_tables(cls):
        """Drop all tables (careful - development only!)."""
        db = cls()
        if db._engine is None:
            db.initialize()
        Base.metadata.drop_all(bind=db._engine)
    
    @classmethod
    def health_check(cls) -> bool:
        """Check database connectivity."""
        try:
            db = cls()
            if db._engine is None:
                db.initialize()
            with db._engine.connect() as connection:
                return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
    
    @classmethod
    def get_engine(cls):
        """Get SQLAlchemy engine."""
        db = cls()
        if db._engine is None:
            db.initialize()
        return db._engine


# Dependency for FastAPI
def get_db() -> Session:
    """
    FastAPI dependency for getting database session.
    
    Usage in endpoints:
        @app.get("/...")
        async def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = Database.get_session()
    try:
        yield db
    finally:
        db.close()
