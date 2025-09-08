import pytest
from datetime import datetime
from src.core.models import Idea, UserSettings, create_tables, engine
from sqlalchemy.orm import sessionmaker

# Создание тестовой сессии
TestSession = sessionmaker(bind=engine)

class TestModels:
    """Тесты для моделей данных."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        create_tables()
        self.db = TestSession()
        # Очищаем данные перед каждым тестом
        self.db.query(UserSettings).delete()
        self.db.query(Idea).delete()
        self.db.commit()
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.db.close()
    
    def test_idea_creation(self):
        """Тест создания идеи."""
        idea = Idea(
            user_id=12345,
            content="Тестовая идея",
            category="Тест"
        )
        
        self.db.add(idea)
        self.db.commit()
        
        assert idea.id is not None
        assert idea.user_id == 12345
        assert idea.content == "Тестовая идея"
        assert idea.category == "Тест"
        assert idea.created_at is not None
    
    def test_user_settings_creation(self):
        """Тест создания настроек пользователя."""
        settings = UserSettings(
            user_id=54321,  # Используем другой user_id
            digest_time="09:00",
            streak_count=5
        )
        
        self.db.add(settings)
        self.db.commit()
        
        assert settings.id is not None
        assert settings.user_id == 54321
        assert settings.digest_time == "09:00"
        assert settings.streak_count == 5
        assert settings.created_at is not None
