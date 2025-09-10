from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from config.settings import settings
import pytz

Base = declarative_base()

class Idea(Base):
    """Модель идеи."""
    
    __tablename__ = "ideas"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)  # JSON строка с тегами
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')), onupdate=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    is_processed = Column(Boolean, default=False)
    is_done = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Idea(id={self.id}, user_id={self.user_id}, content='{self.content[:50]}...')>"

class Task(Base):
    """Модель задачи."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)  # JSON строка с тегами
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    updated_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')), onupdate=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    is_processed = Column(Boolean, default=False)
    is_done = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Task(id={self.id}, user_id={self.user_id}, content='{self.content[:50]}...')>"
class UserSettings(Base):
    """Настройки пользователя."""
    
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True, index=True)
    digest_time = Column(String(5), default="08:00")  # HH:MM
    timezone = Column(String(50), default="Europe/Moscow")
    streak_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    created_at = Column(DateTime, default=lambda: datetime.now(pytz.timezone('Europe/Moscow')))
    
    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, streak={self.streak_count})>"

# Создание движка базы данных
engine = create_engine(settings.database_url, echo=False)

# Создание сессии
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Создание таблиц в базе данных."""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получение сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
