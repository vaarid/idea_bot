import pytest
import os
import tempfile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.core.models import Base

@pytest.fixture(scope="session")
def test_engine():
    """Фикстура для тестовой базы данных."""
    # Создаем временную базу данных в памяти
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def test_db(test_engine):
    """Фикстура для тестовой сессии базы данных."""
    Session = sessionmaker(bind=test_engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
