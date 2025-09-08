from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from src.core.models import Idea, UserSettings, SessionLocal
from src.utils.logger import logger

class IdeaRepository:
    """Репозиторий для работы с идеями."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_idea(self, user_id: int, content: str, category: str = None, tags: str = None) -> Idea:
        """Создание новой идеи."""
        try:
            idea = Idea(
                user_id=user_id,
                content=content,
                category=category,
                tags=tags
            )
            self.db.add(idea)
            self.db.commit()
            self.db.refresh(idea)
            logger.info(f"Создана идея {idea.id} для пользователя {user_id}")
            return idea
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания идеи: {e}")
            raise
    
    def get_ideas_by_user(self, user_id: int, limit: int = 10) -> List[Idea]:
        """Получение идей пользователя."""
        return self.db.query(Idea).filter(
            Idea.user_id == user_id
        ).order_by(Idea.created_at.desc()).limit(limit).all()
    
    def get_ideas_today(self, user_id: int) -> List[Idea]:
        """Получение идей за сегодня."""
        today = date.today()
        return self.db.query(Idea).filter(
            Idea.user_id == user_id,
            Idea.created_at >= today
        ).order_by(Idea.created_at.desc()).all()
    
    def get_idea_by_id(self, idea_id: int, user_id: int) -> Optional[Idea]:
        """Получение идеи по ID."""
        return self.db.query(Idea).filter(
            Idea.id == idea_id,
            Idea.user_id == user_id
        ).first()

class UserSettingsRepository:
    """Репозиторий для работы с настройками пользователя."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_or_create_user_settings(self, user_id: int) -> UserSettings:
        """Получение или создание настроек пользователя."""
        settings = self.db.query(UserSettings).filter(
            UserSettings.user_id == user_id
        ).first()
        
        if not settings:
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            logger.info(f"Созданы настройки для пользователя {user_id}")
        
        return settings
    
    def update_streak(self, user_id: int, increment: bool = True) -> UserSettings:
        """Обновление streak пользователя."""
        settings = self.get_or_create_user_settings(user_id)
        
        if increment:
            settings.streak_count += 1
        else:
            settings.streak_count = 0
        
        settings.last_activity = datetime.utcnow()
        self.db.commit()
        self.db.refresh(settings)
        
        logger.info(f"Обновлен streak пользователя {user_id}: {settings.streak_count}")
        return settings
