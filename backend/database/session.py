import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables if .env exists
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env")))
load_dotenv()

raw_database_url = os.getenv("DATABASE_URL")
DATABASE_URL_CONFIGURED = bool(raw_database_url and raw_database_url.strip())

DEFAULT_DATABASE_URL = raw_database_url.strip() if DATABASE_URL_CONFIGURED else "postgresql+psycopg2://postgres@localhost:5432/ap_control"

# Normalize connection strings from Render / Supabase / Heroku
if DEFAULT_DATABASE_URL.startswith("postgres://"):
    DEFAULT_DATABASE_URL = DEFAULT_DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DEFAULT_DATABASE_URL.startswith("postgresql://") and not DEFAULT_DATABASE_URL.startswith("postgresql+"):
    DEFAULT_DATABASE_URL = DEFAULT_DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

# Ensure sslmode=require for remote Supabase connections if not explicitly specified
if ("supabase.co" in DEFAULT_DATABASE_URL or "supabase.com" in DEFAULT_DATABASE_URL) and "sslmode=" not in DEFAULT_DATABASE_URL.lower():
    separator = "&" if "?" in DEFAULT_DATABASE_URL else "?"
    DEFAULT_DATABASE_URL = f"{DEFAULT_DATABASE_URL}{separator}sslmode=require"

engine = create_engine(
    DEFAULT_DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_size=10,
    max_overflow=20,
    pool_recycle=300,
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
