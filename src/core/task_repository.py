from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from src.core.models import Task, SessionLocal
from src.utils.logger import logger

class TaskRepository:
    """Репозиторий для работы с задачами."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, user_id: int, content: str, category: str = None, tags: str = None) -> Task:
        """Создание новой задачи."""
        try:
            task = Task(
                user_id=user_id,
                content=content,
                category=category,
                tags=tags
            )
            self.db.add(task)
            self.db.commit()
            self.db.refresh(task)
            logger.info(f"Создана задача {task.id} для пользователя {user_id}")
            return task
        except Exception as e:
            self.db.rollback()
            logger.error(f"Ошибка создания задачи: {e}")
            raise
    
    def get_tasks_by_user(self, user_id: int, limit: int = 10) -> List[Task]:
        """Получение задач пользователя."""
        return self.db.query(Task).filter(
            Task.user_id == user_id
        ).order_by(Task.created_at.desc()).limit(limit).all()
    
    def get_tasks_today(self, user_id: int) -> List[Task]:
        """Получение задач за сегодня."""
        today = date.today()
        return self.db.query(Task).filter(
            Task.user_id == user_id,
            Task.created_at >= today
        ).order_by(Task.created_at.desc()).all()
    
    def get_task_by_id(self, task_id: int, user_id: int) -> Optional[Task]:
        """Получение задачи по ID."""
        return self.db.query(Task).filter(
            Task.id == task_id,
            Task.user_id == user_id
        ).first()
    
    def mark_task_done(self, task_id: int, user_id: int) -> bool:
        """Отметить задачу как выполненную."""
        task = self.get_task_by_id(task_id, user_id)
        if task:
            task.is_done = True
            self.db.commit()
            return True
        return False
    
    def update_task_content(self, task_id: int, user_id: int, new_content: str) -> bool:
        """Обновить содержание задачи."""
        task = self.get_task_by_id(task_id, user_id)
        if task:
            task.content = new_content
            self.db.commit()
            return True
    
    def get_user_stats(self, user_id: int) -> dict:
        """Получить статистику пользователя по задачам."""
        total_tasks = self.db.query(Task).filter(Task.user_id == user_id).count()
        done_tasks = self.db.query(Task).filter(
            Task.user_id == user_id, 
            Task.is_done == True
        ).count()
        today_tasks = len(self.get_tasks_today(user_id))
        
        return {
            'total_tasks': total_tasks,
            'done_tasks': done_tasks,
            'pending_tasks': total_tasks - done_tasks,
            'today_tasks': today_tasks
        }
    
    def get_task_by_user_number(self, user_id: int, number: int) -> Optional[Task]:
        """Получение задачи пользователя по номеру в его списке."""
        user_tasks = self.get_tasks_by_user(user_id, limit=10)
        
        if 1 <= number <= len(user_tasks):
            return user_tasks[number - 1]
        return None
    
    def get_pending_task_by_number(self, user_id: int, number: int) -> Optional[Task]:
        """Получение невыполненной задачи по номеру в списке невыполненных."""
        pending_tasks = self.get_tasks_by_user(user_id, limit=10)
        pending_tasks = [task for task in pending_tasks if not task.is_done]
        
        if 1 <= number <= len(pending_tasks):
            return pending_tasks[number - 1]
        return None