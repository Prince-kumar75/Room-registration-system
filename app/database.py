import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Default PostgreSQL URL with SQLite fallback
DEFAULT_PG_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/room_db")
SQLITE_URL = "sqlite:///./room_registration.db"

def get_engine():
    """Try connecting to PostgreSQL first, fallback to SQLite if PostgreSQL connection fails."""
    try:
        engine = create_engine(DEFAULT_PG_URL, pool_pre_ping=True)
        # Test connection
        with engine.connect() as conn:
            pass
        print(f"Connected successfully to primary database: {DEFAULT_PG_URL}")
        return engine
    except Exception as e:
        print(f"PostgreSQL connection failed ({e}). Falling back to SQLite: {SQLITE_URL}")
        return create_engine(
            SQLITE_URL,
            connect_args={"check_same_thread": False}
        )

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
