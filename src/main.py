import sys
import os
from telegram.ext import Application
from src.bot.handlers import BotHandlers
from src.core.models import create_tables
from src.utils.logger import logger
from config.settings import settings

def main():
    """Основная функция запуска бота."""
    
    try:
        # Создание таблиц в базе данных
        logger.info("Создание таблиц в базе данных...")
        create_tables()
        logger.info("Таблицы созданы успешно")
        
        # Создание приложения Telegram
        logger.info("Инициализация Telegram бота...")
        application = Application.builder().token(settings.telegram_bot_token).build()
        
        # Создание обработчиков
        handlers = BotHandlers()
        handlers_list = handlers.get_handlers()
        
        # Добавление обработчиков
        for handler in handlers_list:
            application.add_handler(handler)
        
        logger.info("Обработчики добавлены успешно")
        
        # Запуск бота
        logger.info("Запуск бота...")
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Проверка наличия токена
    if not settings.telegram_bot_token or settings.telegram_bot_token == "your_telegram_bot_token_here":
        print(" Ошибка: Не указан TELEGRAM_BOT_TOKEN в файле .env")
        print("Скопируйте .env.example в .env и заполните необходимые поля")
        sys.exit(1)
    
    # Запуск бота
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка запуска: {e}")
        sys.exit(1)
