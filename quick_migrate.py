#!/usr/bin/env python3
"""
Быстрая миграция без Docker
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

from src.core.models import create_tables, Task
from src.utils.logger import logger

def quick_migrate():
    """Быстрая миграция."""
    try:
        logger.info("🚀 Начинаем быструю миграцию...")
        
        # Создаем все таблицы (включая новую таблицу tasks)
        create_tables()
        
        logger.info("✅ Миграция завершена успешно! Таблица 'tasks' добавлена.")
        print("✅ Миграция завершена успешно! Таблица 'tasks' добавлена.")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при миграции: {e}")
        print(f"❌ Ошибка при миграции: {e}")
        raise

if __name__ == "__main__":
    quick_migrate()
