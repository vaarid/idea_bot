from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from src.core.database import IdeaRepository, UserSettingsRepository
from src.core.models import SessionLocal, Idea
from src.utils.logger import logger
from src.utils.validation import SecurityValidator, ValidationError, rate_limiter
from datetime import datetime
import pytz

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
        
        # Добавляем основную клавиатуру
        main_keyboard = self.get_main_keyboard()
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)
        await update.message.reply_text("Используйте кнопки ниже для быстрого доступа:", reply_markup=main_keyboard)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help."""
        help_text = """
 Справка по командам Idea Bot:

 Основные команды:
/save <текст> - сохранить идею
/list - показать последние 10 идей
/today - показать идеи за сегодня
/done <ID> - отметить идею как выполненную
/edit <ID> <новый текст> - редактировать идею
/stats - показать статистику
/help - эта справка

 Как использовать:
 Отправьте любое текстовое сообщение - оно будет сохранено как идея
 Используйте команды для управления своими идеями
 Бот автоматически отслеживает вашу активность
 Время отображается в московском часовом поясе

 Примеры:
/save Новая идея для проекта
/done 5 - отметить идею с ID 5 как выполненную
/edit 3 Обновленный текст идеи
Просто отправьте: "Вспомнить купить молоко"
        """
        
        await update.message.reply_text(help_text)
    
    async def save_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /save."""
        user_id = update.effective_user.id
        
        # Проверка rate limit
        if not rate_limiter.is_allowed(user_id):
            await update.message.reply_text("⏰ Слишком много запросов. Подождите минуту.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Укажите текст идеи: /save <ваша идея>")
            return
        
        content = " ".join(context.args)
        
        try:
            # Валидация контента
            SecurityValidator.validate_message_content(content)
            content = SecurityValidator.sanitize_content(content)
            
            idea = self.idea_repo.create_idea(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = idea.created_at.astimezone(moscow_tz)
            
            response = f"""
✅ Идея сохранена!

 ID: {idea.id}
🕐 Время (МСК): {moscow_time.strftime('%H:%M')}
📄 Содержание: {content[:100]}{'...' if len(content) > 100 else ''}
            """
            
            await update.message.reply_text(response)
            logger.info(f"Пользователь {user_id} сохранил идею: {idea.id}")
            
        except ValidationError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения идеи: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении идеи")
    
    async def list_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /list."""
        user_id = update.effective_user.id
        
        try:
            ideas = self.idea_repo.get_ideas_by_user(user_id, limit=10)
            
            if not ideas:
                await update.message.reply_text("📝 У вас пока нет сохраненных идей")
                return
            
            response = "📋 Ваши последние идеи:\n\n"
            
            for i, idea in enumerate(ideas, 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
                content_preview = idea.content[:50] + "..." if len(idea.content) > 50 else idea.content
                status = "✅" if idea.is_done else "⏳"
                response += f"{status} {i}. ({date_str})\n{content_preview}\n\n"
            
            # Добавляем кнопки для быстрого доступа
            keyboard = [
                [InlineKeyboardButton("✅ Отметить выполненными", callback_data="mark_done")],
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("📅 За сегодня", callback_data="today")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка идей: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении идей")
    
    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /today."""
        user_id = update.effective_user.id
        
        try:
            ideas = self.idea_repo.get_ideas_today(user_id)
            
            if not ideas:
                await update.message.reply_text(" У вас пока нет идей за сегодня")
                return
            
            response = f" Идеи за сегодня ({len(ideas)} шт.):\n\n"
            
            for i, idea in enumerate(ideas, 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                time_str = moscow_time.strftime('%H:%M')
                content_preview = idea.content[:60] + "..." if len(idea.content) > 60 else idea.content
                status = "✅" if idea.is_done else "⏳"
                response += f"{status} {i}. {time_str}: {content_preview}\n\n"
            
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
        
        # Обработка кнопок клавиатуры
        if content == "📝 Мои идеи":
            await self.list_command(update, context)
            return
        elif content == "📊 Статистика":
            await self.stats_command(update, context)
            return
        elif content == "📅 За сегодня":
            await self.today_command(update, context)
            return
        elif content == "✅ Выполненные":
            await self.done_ideas_command(update, context)
            return
        elif content == "❓ Помощь":
            await self.help_command(update, context)
            return
        
        # Обработка простых номеров для отметки идей как выполненных
        if content.isdigit():
            number = int(content)
            if 1 <= number <= 10:  # Разумный лимит
                await self.handle_number_input(update, context, number)
            return
        
        try:
            # Проверка rate limit
            if not rate_limiter.is_allowed(user_id):
                await update.message.reply_text("⏰ Слишком много запросов. Подождите минуту.")
                return
            
            # Валидация контента
            SecurityValidator.validate_message_content(content)
            content = SecurityValidator.sanitize_content(content)
            
            idea = self.idea_repo.create_idea(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = idea.created_at.astimezone(moscow_tz)
            
            response = f"💡 Идея сохранена! (ID: {idea.id}, время МСК: {moscow_time.strftime('%H:%M')})"
            await update.message.reply_text(response)
            
            logger.info(f"Пользователь {user_id} сохранил идею через текстовое сообщение: {idea.id}")
            
        except ValidationError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка сохранения идеи из текста: {e}")
            await update.message.reply_text("❌ Произошла ошибка при сохранении идеи")
    
    async def done_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /done."""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите номер идеи: /done <номер>\n\nПример: /done 1")
            return
        
        try:
            number = int(context.args[0])
            
            # Ищем идею по номеру в списке пользователя
            idea = self.idea_repo.get_idea_by_user_number(user_id, number)
            
            if idea:
                if idea.is_done:
                    await update.message.reply_text(f"✅ Идея #{number} уже отмечена как выполненная!")
                    return
                
                # Отмечаем как выполненную
                idea.is_done = True
                self.idea_repo.db.commit()
                
                await update.message.reply_text(f"✅ Идея #{number} отмечена как выполненная!\n\n💡 {idea.content}")
                logger.info(f"Пользователь {user_id} отметил идею {idea.id} (номер {number}) как выполненную")
            else:
                await update.message.reply_text(f"❌ Идея #{number} не найдена в вашем списке")
                
        except ValueError:
            await update.message.reply_text("❌ Номер идеи должен быть числом")
        except Exception as e:
            logger.error(f"Ошибка отметки идеи как выполненной: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отметке идеи")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /stats."""
        user_id = update.effective_user.id
        
        try:
            stats = self.idea_repo.get_user_stats(user_id)
            user_settings = self.user_repo.get_or_create_user_settings(user_id)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz).strftime('%H:%M')
            
            response = f"""
📊 Ваша статистика:

📝 Всего идей: {stats['total_ideas']}
✅ Выполнено: {stats['done_ideas']}
⏳ В ожидании: {stats['pending_ideas']}
📅 За сегодня: {stats['today_ideas']}

🔥 Streak: {user_settings.streak_count} дней
🕐 Текущее время (МСК): {current_time}
⏰ Время дайджеста: {user_settings.digest_time}
            """
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении статистики")
    
    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /edit."""
        user_id = update.effective_user.id
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /edit <ID> <новый текст>")
            return
        
        try:
            idea_id = int(context.args[0])
            new_content = " ".join(context.args[1:])
            
            success = self.idea_repo.update_idea_content(idea_id, user_id, new_content)
            
            if success:
                await update.message.reply_text(f"✅ Идея {idea_id} обновлена!")
                logger.info(f"Пользователь {user_id} обновил идею {idea_id}")
            else:
                await update.message.reply_text("❌ Идея не найдена или не принадлежит вам")
                
        except ValueError:
            await update.message.reply_text("❌ ID должен быть числом")
        except Exception as e:
            logger.error(f"Ошибка редактирования идеи: {e}")
            await update.message.reply_text("❌ Произошла ошибка")
    
    def get_main_keyboard(self):
        """Получение основной клавиатуры."""
        keyboard = [
            [KeyboardButton("📝 Мои идеи"), KeyboardButton("📊 Статистика")],
            [KeyboardButton("📅 За сегодня"), KeyboardButton("✅ Выполненные")],
            [KeyboardButton("❓ Помощь")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    async def done_ideas_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать выполненные идеи."""
        user_id = update.effective_user.id
        
        try:
            # Получаем выполненные идеи
            done_ideas = self.db.query(Idea).filter(
                Idea.user_id == user_id,
                Idea.is_done == True
            ).order_by(Idea.created_at.desc()).limit(10).all()
            
            if not done_ideas:
                await update.message.reply_text("✅ У вас пока нет выполненных идей")
                return
            
            response = "✅ Ваши выполненные идеи:\n\n"
            
            for i, idea in enumerate(done_ideas, 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
                content_preview = idea.content[:50] + "..." if len(idea.content) > 50 else idea.content
                response += f"🔹 {i}. ({date_str})\n{content_preview}\n\n"
            
            await update.message.reply_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения выполненных идей: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении выполненных идей")
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик callback кнопок."""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        if query.data == "mark_done":
            await self.show_pending_ideas_for_done(query, user_id)
        elif query.data == "stats":
            await self.stats_callback(query, user_id)
        elif query.data == "today":
            await self.today_callback(query, user_id)
        elif query.data.startswith("done_idea_"):
            # Обработка inline кнопок для отметки идей как выполненных
            idea_id = int(query.data.replace("done_idea_", ""))
            await self.mark_idea_done_callback(query, user_id, idea_id)
    
    async def stats_callback(self, query, user_id):
        """Callback для статистики."""
        try:
            stats = self.idea_repo.get_user_stats(user_id)
            user_settings = self.user_repo.get_or_create_user_settings(user_id)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz).strftime('%H:%M')
            
            response = f"""
📊 Ваша статистика:

📝 Всего идей: {stats['total_ideas']}
✅ Выполнено: {stats['done_ideas']}
⏳ В ожидании: {stats['pending_ideas']}
📅 За сегодня: {stats['today_ideas']}

🔥 Streak: {user_settings.streak_count} дней
🕐 Текущее время (МСК): {current_time}
⏰ Время дайджеста: {user_settings.digest_time}
            """
            
            await query.edit_message_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении статистики")
    
    async def today_callback(self, query, user_id):
        """Callback для идей за сегодня."""
        try:
            ideas = self.idea_repo.get_ideas_today(user_id)
            
            if not ideas:
                await query.edit_message_text("📝 У вас пока нет идей за сегодня")
                return
            
            response = f"📅 Идеи за сегодня ({len(ideas)} шт.):\n\n"
            
            for idea in ideas:
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                time_str = moscow_time.strftime('%H:%M')
                content_preview = idea.content[:60] + "..." if len(idea.content) > 60 else idea.content
                status = "✅" if idea.is_done else "⏳"
                response += f"{status} {time_str}: {content_preview}\n\n"
            
            await query.edit_message_text(response)
            
        except Exception as e:
            logger.error(f"Ошибка получения идей за сегодня: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении идей")
    
    async def show_pending_ideas_for_done(self, query, user_id):
        """Показать невыполненные идеи для отметки как выполненные."""
        try:
            # Получаем только невыполненные идеи
            pending_ideas = self.idea_repo.get_ideas_by_user(user_id, limit=10)
            pending_ideas = [idea for idea in pending_ideas if not idea.is_done]
            
            if not pending_ideas:
                await query.edit_message_text("🎉 У вас нет невыполненных идей!")
                return
            
            response = "✅ Выберите идею для отметки как выполненную:\n\n"
            
            # Создаем inline кнопки
            keyboard = []
            
            for i, idea in enumerate(pending_ideas, 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y')
                time_str = moscow_time.strftime('%H:%M')
                
                # Обрезаем длинный текст
                content_preview = idea.content[:60] + "..." if len(idea.content) > 60 else idea.content
                
                response += f"**{i}.** {content_preview}\n"
                response += f"   📅 {date_str} в {time_str}\n\n"
                
                # Добавляем кнопку для каждой идеи
                button_text = f"✅ {i}"
                callback_data = f"done_idea_{idea.id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            response += "💡 **Или введите номер:** `1`, `2`, `3` и т.д."
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка получения невыполненных идей: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении идей")
    
    async def mark_idea_done_callback(self, query, user_id, idea_id):
        """Отметить идею как выполненную через inline кнопку."""
        try:
            idea = self.idea_repo.get_idea_by_id(idea_id, user_id)
            
            if not idea:
                await query.edit_message_text("❌ Идея не найдена")
                return
            
            if idea.is_done:
                await query.edit_message_text("✅ Идея уже отмечена как выполненная!")
                return
            
            # Отмечаем как выполненную
            idea.is_done = True
            self.idea_repo.db.commit()
            
            await query.edit_message_text(f"✅ Идея #{idea.id} отмечена как выполненная!\n\n💡 {idea.content}")
            logger.info(f"Пользователь {user_id} отметил идею {idea.id} как выполненную через inline кнопку")
            
        except Exception as e:
            logger.error(f"Ошибка отметки идеи как выполненной: {e}")
            await query.edit_message_text("❌ Произошла ошибка при отметке идеи")
    
    async def handle_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, number: int):
        """Обработка ввода номера для отметки идеи как выполненной."""
        user_id = update.effective_user.id
        
        try:
            # Ищем идею по номеру в списке пользователя
            idea = self.idea_repo.get_idea_by_user_number(user_id, number)
            
            if idea:
                if idea.is_done:
                    await update.message.reply_text(f"✅ Идея #{number} уже отмечена как выполненная!")
                    return
                
                # Отмечаем как выполненную
                idea.is_done = True
                self.idea_repo.db.commit()
                
                await update.message.reply_text(f"✅ Идея #{number} отмечена как выполненная!\n\n💡 {idea.content}")
                logger.info(f"Пользователь {user_id} отметил идею {idea.id} (номер {number}) как выполненную через номер")
            else:
                await update.message.reply_text(f"❌ Идея #{number} не найдена в вашем списке")
                
        except Exception as e:
            logger.error(f"Ошибка обработки номера {number}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отметке идеи")
    
    def get_handlers(self):
        """Получение всех обработчиков."""
        return [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("save", self.save_command),
            CommandHandler("list", self.list_command),
            CommandHandler("today", self.today_command),
            CommandHandler("done", self.done_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("edit", self.edit_command),
            CallbackQueryHandler(self.button_callback),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message),
        ]
