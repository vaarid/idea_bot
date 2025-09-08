import logging
import os
from datetime import datetime
from config.settings import settings

def setup_logger(name: str = "idea_bot") -> logging.Logger:
    """Настройка логгера."""
    
    # Создание директории для логов
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)
    
    # Создание логгера
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Очистка существующих хендлеров
    logger.handlers.clear()
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Файловый хендлер
    file_handler = logging.FileHandler(settings.log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Глобальный логгер
logger = setup_logger()
