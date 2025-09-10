#!/usr/bin/env python3
"""
Миграция для добавления таблицы задач в базу данных.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.models import create_tables, Task
from src.core.database import SessionLocal
from src.utils.logger import logger

def migrate_add_tasks_table():
    """Добавить таблицу задач в базу данных."""
    try:
        logger.info("Начинаем миграцию: добавление таблицы задач...")
        
        # Создаем все таблицы (включая новую таблицу tasks)
        create_tables()
        
        logger.info("✅ Миграция завершена успешно! Таблица 'tasks' добавлена.")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при миграции: {e}")
        raise

if __name__ == "__main__":
    migrate_add_tasks_table()
