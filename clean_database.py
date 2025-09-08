import os
from src.core.models import create_tables, engine, Base, Idea
from src.utils.logger import logger
from config.settings import settings
from sqlalchemy.orm import sessionmaker

def clean_database():
    """
    Очищает базу данных от некорректных идей (названия кнопок).
    """
    db_file = settings.database_url.replace("sqlite:///", "")
    
    logger.info(f"Очистка базы данных: {db_file}")
    
    if not os.path.exists(db_file):
        logger.info("База данных не существует, создаем новую...")
        create_tables()
        return
    
    try:
        # Создаем сессию
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Список названий кнопок, которые могли быть сохранены как идеи
        button_names = [
            "📝 Мои идеи",
            "📊 Статистика", 
            "📅 За сегодня",
            "✅ Выполненные",
            "❓ Помощь",
            "Мои идеи",
            "Статистика",
            "За сегодня", 
            "Выполненные",
            "Помощь"
        ]
        
        # Удаляем идеи с названиями кнопок
        deleted_count = 0
        for button_name in button_names:
            ideas_to_delete = session.query(Idea).filter(Idea.content == button_name).all()
            for idea in ideas_to_delete:
                session.delete(idea)
                deleted_count += 1
                logger.info(f"Удалена идея с ID {idea.id}: '{idea.content}'")
        
        session.commit()
        logger.info(f"Удалено {deleted_count} некорректных идей")
        
        # Показываем оставшиеся идеи
        remaining_ideas = session.query(Idea).all()
        logger.info(f"Осталось {len(remaining_ideas)} идей в базе данных:")
        for idea in remaining_ideas:
            logger.info(f"  ID {idea.id}: '{idea.content[:50]}...' (пользователь {idea.user_id})")
        
        session.close()
        logger.info("Очистка базы данных завершена успешно!")
        
    except Exception as e:
        logger.error(f"Ошибка очистки базы данных: {e}")
        logger.error("Убедитесь, что бот остановлен и файл базы данных не занят другими процессами.")

if __name__ == "__main__":
    clean_database()
