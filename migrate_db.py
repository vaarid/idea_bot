#!/usr/bin/env python3
"""
Скрипт для миграции базы данных.
"""
import os
from src.core.models import create_tables, engine
from src.utils.logger import logger

def migrate_database():
    """Миграция базы данных."""
    try:
        # Удаляем старую базу данных
        db_files = ["ideas.db", "data/ideas.db"]
        for db_file in db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
                logger.info(f"Удален файл базы данных: {db_file}")
        
        # Создаем новые таблицы
        logger.info("Создание новых таблиц...")
        create_tables()
        logger.info("Миграция завершена успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка миграции: {e}")
        raise

if __name__ == "__main__":
    migrate_database()
