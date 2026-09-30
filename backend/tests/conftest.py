import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.database.session import engine as base_engine

@pytest.fixture(scope="session")
def engine():
    return base_engine

@pytest.fixture(scope="function")
def db_session(engine):
    """
    Provides a clean SQLAlchemy Session wrapped in a connection transaction.
    Rolls back any modifications made during the test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, expire_on_commit=False)
    session = SessionLocal()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()
