import pytest
from src.core.database import IdeaRepository, UserSettingsRepository
from src.core.models import create_tables, SessionLocal

class TestDatabase:
    """Тесты для работы с базой данных."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        create_tables()
        self.db = SessionLocal()
        self.idea_repo = IdeaRepository(self.db)
        self.user_repo = UserSettingsRepository(self.db)
        # Очищаем данные перед каждым тестом
        from src.core.models import Idea, UserSettings
        self.db.query(Idea).delete()
        self.db.query(UserSettings).delete()
        self.db.commit()
    
    def teardown_method(self):
        """Очистка после каждого теста."""
        self.db.close()
    
    def test_create_idea(self):
        """Тест создания идеи через репозиторий."""
        idea = self.idea_repo.create_idea(
            user_id=12345,
            content="Тестовая идея через репозиторий"
        )
        
        assert idea.id is not None
        assert idea.user_id == 12345
        assert idea.content == "Тестовая идея через репозиторий"
    
    def test_get_ideas_by_user(self):
        """Тест получения идей пользователя."""
        # Создаем несколько идей
        self.idea_repo.create_idea(12345, "Идея 1")
        self.idea_repo.create_idea(12345, "Идея 2")
        self.idea_repo.create_idea(67890, "Идея другого пользователя")
        
        # Получаем идеи пользователя 12345
        ideas = self.idea_repo.get_ideas_by_user(12345)
        
        assert len(ideas) == 2
        assert all(idea.user_id == 12345 for idea in ideas)
        
        # Получаем идеи пользователя 67890
        ideas_other = self.idea_repo.get_ideas_by_user(67890)
        assert len(ideas_other) == 1
        assert ideas_other[0].user_id == 67890
    
    def test_user_settings_creation(self):
        """Тест создания настроек пользователя."""
        settings = self.user_repo.get_or_create_user_settings(12345)
        
        assert settings.user_id == 12345
        assert settings.digest_time == "08:00"  # значение по умолчанию
        assert settings.streak_count == 0
    
    def test_update_streak(self):
        """Тест обновления streak."""
        # Создаем настройки пользователя
        settings = self.user_repo.get_or_create_user_settings(12345)
        assert settings.streak_count == 0
        
        # Увеличиваем streak
        updated_settings = self.user_repo.update_streak(12345, increment=True)
        assert updated_settings.streak_count == 1
        
        # Увеличиваем еще раз
        updated_settings = self.user_repo.update_streak(12345, increment=True)
        assert updated_settings.streak_count == 2
