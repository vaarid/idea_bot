#!/usr/bin/env python3
"""
Простое локальное тестирование без Docker
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Устанавливаем тестовую базу данных
os.environ['DATABASE_URL'] = 'sqlite:///test_idea_bot.db'

from src.core.models import create_tables, Task, Idea
from src.core.database import SessionLocal
from src.core.task_repository import TaskRepository
from src.core.database import IdeaRepository
from src.utils.logger import logger

def test_basic_functionality():
    """Базовое тестирование функционала."""
    try:
        print("🧪 Начинаем локальное тестирование...")
        
        # Создаем таблицы
        create_tables()
        print("✅ Таблицы созданы")
        
        # Тестируем создание
        db = SessionLocal()
        task_repo = TaskRepository(db)
        idea_repo = IdeaRepository(db)
        
        # Создаем тестовые записи
        task = task_repo.create_task(12345, "Тестовая задача")
        idea = idea_repo.create_idea(12345, "Тестовая идея")
        
        print(f"✅ Задача создана: {task.id}")
        print(f"✅ Идея создана: {idea.id}")
        
        # Тестируем получение
        tasks = task_repo.get_tasks_by_user(12345)
        ideas = idea_repo.get_ideas_by_user(12345)
        
        print(f"✅ Получено задач: {len(tasks)}, идей: {len(ideas)}")
        
        # Тестируем отметку о выполнении
        task_repo.mark_task_done(task.id, 12345)
        idea_repo.mark_idea_done(idea.id, 12345)
        
        print("✅ Отметка о выполнении работает")
        
        # Тестируем статистику
        task_stats = task_repo.get_user_stats(12345)
        idea_stats = idea_repo.get_user_stats(12345)
        
        print(f"✅ Статистика задач: {task_stats}")
        print(f"✅ Статистика идей: {idea_stats}")
        
        db.close()
        print("🎉 Все тесты прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        raise

if __name__ == "__main__":
    test_basic_functionality()
