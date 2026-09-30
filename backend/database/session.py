import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DEFAULT_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres@localhost:5432/ap_control",
)
# Normalize connection strings from Render / Supabase / Heroku
if DEFAULT_DATABASE_URL.startswith("postgres://"):
    DEFAULT_DATABASE_URL = DEFAULT_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DEFAULT_DATABASE_URL.startswith("postgresql://") and not DEFAULT_DATABASE_URL.startswith("postgresql+"):
    DEFAULT_DATABASE_URL = DEFAULT_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(

    DEFAULT_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database sessions with automatic commit/rollback."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db() -> Generator[Session, None, None]:
    """Dependency for yielding db sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
