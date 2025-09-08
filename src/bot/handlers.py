from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from src.core.database import IdeaRepository, UserSettingsRepository
from src.core.models import SessionLocal
from src.utils.logger import logger
from datetime import datetime

class BotHandlers:
    """Обработчики команд Telegram бота."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.idea_repo = IdeaRepository(self.db)
        self.user_repo = UserSettingsRepository(self.db)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")
        
        # Создание или получение настроек пользователя
        self.user_repo.get_or_create_user_settings(user.id)
        
        welcome_text = f"""
 Добро пожаловать в Idea Bot, {user.first_name}!

Этот бот поможет вам фиксировать идеи и мысли в любое время.

 Основные команды:
/save <текст> - сохранить идею
/list - показать последние идеи
/today - идеи за сегодня
/help - справка

 Просто отправьте текстовое сообщение, и оно будет сохранено как идея!
        """
        
        keyboard = [
            [InlineKeyboardButton(" Сохранить идею", callback_data="save_idea")],
            [InlineKeyboardButton(" Мои идеи", callback_data="my_ideas")],
            [InlineKeyboardButton(" Статистика", callback_data="stats")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        help_text = """
 Справка по командам Idea Bot:

 Основные команды:
/save <текст> - сохранить идею
/list - показать последние 10 идей
/today - показать идеи за сегодня
/help - эта справка

 Как использовать:
 Отправьте любое текстовое сообщение - оно будет сохранено как идея
 Используйте команды для управления своими идеями
 Бот автоматически отслеживает вашу активность

 Примеры:
/save Новая идея для проекта
Просто отправьте: "Вспомнить купить молоко"
        """
        
        await update.message.reply_text(help_text)
    
    async def save_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /save."""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text(" Укажите текст идеи: /save <ваша идея>")
            return
        
        content = " ".join(context.args)
        
        try:
            idea = self.idea_repo.create_idea(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            response = f"""
 Идея сохранена!

 ID: {idea.id}
 Время: {idea.created_at.strftime('%H:%M')}
 Содержание: {content[:100]}{'...' if len(content) > 100 else ''}
            """
            
            await update.message.reply_text(response)
            logger.info(f"Пользователь {user_id} сохранил идею: {idea.id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения идеи: {e}")
            await update.message.reply_text(" Произошла ошибка при сохранении идеи")
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /list."""
        user_id = update.effective_user.id
        
        try:
            ideas = self.idea_repo.get_ideas_by_user(user_id, limit=10)
            
            if not ideas:
                await update.message.reply_text(" У вас пока нет сохраненных идей")
                return
            
            response = " Ваши последние идеи:\n\n"
            
            for idea in ideas:
                date_str = idea.created_at.strftime('%d.%m.%Y %H:%M')
                content_preview = idea.content[:50] + "..." if len(idea.content) > 50 else idea.content
                response += f" ID {idea.id} ({date_str})\n{content_preview}\n\n"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка идей: {e}")
            await update.message.reply_text(" Произошла ошибка при получении идей")
    
    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /today."""
        user_id = update.effective_user.id
        
        try:
            ideas = self.idea_repo.get_ideas_today(user_id)
            
            if not ideas:
                await update.message.reply_text(" У вас пока нет идей за сегодня")
                return
            
            response = f" Идеи за сегодня ({len(ideas)} шт.):\n\n"
            
            for idea in ideas:
                time_str = idea.created_at.strftime('%H:%M')
                content_preview = idea.content[:60] + "..." if len(idea.content) > 60 else idea.content
                response += f" {time_str}: {content_preview}\n\n"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения идей за сегодня: {e}")
            await update.message.reply_text(" Произошла ошибка при получении идей")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик текстовых сообщений."""
        user_id = update.effective_user.id
        content = update.message.text
        
        # Игнорируем команды
        if content.startswith('/'):
            return
        
        try:
            idea = self.idea_repo.create_idea(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            response = f" Идея сохранена! (ID: {idea.id})"
            await update.message.reply_text(response)
            
            logger.info(f"Пользователь {user_id} сохранил идею через текстовое сообщение: {idea.id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения идеи из текста: {e}")
            await update.message.reply_text(" Произошла ошибка при сохранении идеи")
    
    def get_handlers(self):
        """Получение всех обработчиков."""
        return [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("save", self.save_command),
            CommandHandler("list", self.list_command),
            CommandHandler("today", self.today_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message),
        ]
