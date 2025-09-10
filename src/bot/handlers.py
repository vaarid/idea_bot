from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from src.core.database import IdeaRepository, UserSettingsRepository, TaskRepository
from src.core.models import SessionLocal, Idea, Task
from src.utils.logger import logger
from src.utils.validation import SecurityValidator, ValidationError, rate_limiter
from datetime import datetime
import pytz

class BotHandlers:
    """Обработчики команд Telegram бота."""
    
    def __init__(self):
        self.db = SessionLocal()
        self.idea_repo = IdeaRepository(self.db)
        self.task_repo = TaskRepository(self.db)
        self.user_repo = UserSettingsRepository(self.db)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start."""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) запустил бота")
        
        # Создание или получение настроек пользователя
        self.user_repo.get_or_create_user_settings(user.id)
        
        welcome_text = f"""
 Добро пожаловать в Idea Bot, {user.first_name}!

Этот бот поможет вам фиксировать идеи и задачи в любое время.

 Основные команды:
/save <текст> - сохранить идею или задачу
/list - показать последние идеи
/tasks - показать последние задачи
/today - идеи за сегодня
/today_tasks - задачи за сегодня
/help - справка

 Просто отправьте текстовое сообщение, и бот спросит: это идея или задача!
        """
        
        keyboard = [
            [InlineKeyboardButton("💡 Сохранить идею", callback_data="save_idea")],
            [InlineKeyboardButton("📋 Сохранить задачу", callback_data="save_task")],
            [InlineKeyboardButton("📝 Мои идеи", callback_data="my_ideas")],
            [InlineKeyboardButton("📋 Мои задачи", callback_data="my_tasks")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")]
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
/save <текст> - сохранить идею или задачу
/list - показать последние 10 идей
/tasks - показать последние 10 задач
/today - показать идеи за сегодня
/today_tasks - показать задачи за сегодня
/done <номер> - отметить идею/задачу как выполненную (автоопределение)
/done_idea <номер> - отметить конкретную идею как выполненную
/done_task <номер> - отметить конкретную задачу как выполненную
/edit <ID> <новый текст> - редактировать идею/задачу
/stats - показать статистику
/help - эта справка

 Как использовать:
 Отправьте любое текстовое сообщение - бот спросит: идея или задача?
 Используйте команды для управления своими идеями и задачами
 Бот автоматически отслеживает вашу активность
 Время отображается в московском часовом поясе

 Примеры:
/save Новая идея для проекта
/tasks - показать мои задачи
/done 1 - отметить элемент с номером 1 (автоопределение)
/done_task 1 - точно отметить задачу с номером 1
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
            # Получаем все идеи пользователя
            all_ideas = self.idea_repo.get_ideas_by_user(user_id, limit=1000)  # Большой лимит для получения всех
            
            if not all_ideas:
                await update.message.reply_text("📝 У вас пока нет сохраненных идей")
                return
            
            # Сохраняем контекст - пользователь смотрит список идей
            context.user_data['last_viewed'] = 'ideas'
            context.user_data['ideas_page'] = 0  # Начинаем с первой страницы
            context.user_data['all_ideas'] = all_ideas  # Сохраняем все идеи
            
            await self.show_ideas_page(update, context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения списка идей: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении идей")
    
    async def show_ideas_page(self, update, context, page_num):
        """Показать страницу с идеями."""
        try:
            all_ideas = context.user_data.get('all_ideas', [])
            if not all_ideas:
                await update.message.reply_text("📝 У вас пока нет сохраненных идей")
                return
            
            items_per_page = 10
            total_pages = (len(all_ideas) + items_per_page - 1) // items_per_page
            start_idx = page_num * items_per_page
            end_idx = start_idx + items_per_page
            ideas = all_ideas[start_idx:end_idx]
            
            response = f"📋 Ваши идеи (стр. {page_num + 1}/{total_pages}):\n\n"
            
            # Создаем кнопки для быстрого доступа
            keyboard = []
            
            for i, idea in enumerate(ideas, start_idx + 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
                content_preview = idea.content[:50] + "..." if len(idea.content) > 50 else idea.content
                status = "✅" if idea.is_done else "⏳"
                response += f"{status} {i}. ({date_str})\n{content_preview}\n\n"
                
                # Добавляем кнопки для каждой идеи
                idea_buttons = []
                
                # Кнопка "Показать полностью" для длинных идей
                if len(idea.content) > 50:
                    idea_buttons.append(InlineKeyboardButton(f"📖 {i}", callback_data=f"show_idea_{idea.id}"))
                
                # Кнопка выполнения/отмены выполнения
                if idea.is_done:
                    idea_buttons.append(InlineKeyboardButton(f"❌ {i}", callback_data=f"undo_idea_{idea.id}"))
                else:
                    idea_buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"done_idea_{idea.id}"))
                
                if idea_buttons:
                    keyboard.append(idea_buttons)
            
            # Добавляем кнопки пагинации
            pagination_buttons = []
            if page_num > 0:
                pagination_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"ideas_page_{page_num - 1}"))
            if page_num < total_pages - 1:
                pagination_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"ideas_page_{page_num + 1}"))
            
            if pagination_buttons:
                keyboard.append(pagination_buttons)
            
            # Добавляем основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("📅 За сегодня", callback_data="today")]
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'message'):
                await update.message.reply_text(response, reply_markup=reply_markup)
            else:
                await update.edit_message_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа страницы идей: {e}")
            if hasattr(update, 'message'):
                await update.message.reply_text("❌ Произошла ошибка при получении идей")
            else:
                await update.edit_message_text("❌ Произошла ошибка при получении идей")
    
    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /today."""
        user_id = update.effective_user.id
        
        try:
            # Получаем все идеи за сегодня
            all_ideas = self.idea_repo.get_ideas_today(user_id)
            
            if not all_ideas:
                await update.message.reply_text("📝 У вас пока нет идей за сегодня")
                return
            
            # Сохраняем контекст для пагинации
            context.user_data['today_ideas_page'] = 0
            context.user_data['all_today_ideas'] = all_ideas
            
            await self.show_today_ideas_page(update, context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения идей за сегодня: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении идей")
    
    async def show_today_ideas_page(self, update, context, page_num):
        """Показать страницу с идеями за сегодня."""
        try:
            all_ideas = context.user_data.get('all_today_ideas', [])
            if not all_ideas:
                await update.message.reply_text("📝 У вас пока нет идей за сегодня")
                return
            
            items_per_page = 10
            total_pages = (len(all_ideas) + items_per_page - 1) // items_per_page
            start_idx = page_num * items_per_page
            end_idx = start_idx + items_per_page
            ideas = all_ideas[start_idx:end_idx]
            
            response = f"📅 Идеи за сегодня (стр. {page_num + 1}/{total_pages}):\n\n"
            
            # Создаем кнопки для быстрого доступа
            keyboard = []
            
            for i, idea in enumerate(ideas, start_idx + 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = idea.created_at.astimezone(moscow_tz)
                time_str = moscow_time.strftime('%H:%M')
                content_preview = idea.content[:50] + "..." if len(idea.content) > 50 else idea.content
                status = "✅" if idea.is_done else "⏳"
                response += f"{status} {i}. {time_str}: {content_preview}\n\n"
                
                # Добавляем кнопки для каждой идеи
                idea_buttons = []
                
                # Кнопка "Показать полностью" для длинных идей
                if len(idea.content) > 50:
                    idea_buttons.append(InlineKeyboardButton(f"📖 {i}", callback_data=f"show_idea_{idea.id}"))
                
                # Кнопка выполнения/отмены выполнения
                if idea.is_done:
                    idea_buttons.append(InlineKeyboardButton(f"❌ {i}", callback_data=f"undo_idea_{idea.id}"))
                else:
                    idea_buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"done_idea_{idea.id}"))
                
                if idea_buttons:
                    keyboard.append(idea_buttons)
            
            # Добавляем кнопки пагинации
            pagination_buttons = []
            if page_num > 0:
                pagination_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"today_ideas_page_{page_num - 1}"))
            if page_num < total_pages - 1:
                pagination_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"today_ideas_page_{page_num + 1}"))
            
            if pagination_buttons:
                keyboard.append(pagination_buttons)
            
            # Добавляем основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("📅 За сегодня", callback_data="today")]
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'message'):
                await update.message.reply_text(response, reply_markup=reply_markup)
            else:
                await update.edit_message_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа страницы идей за сегодня: {e}")
            if hasattr(update, 'message'):
                await update.message.reply_text("❌ Произошла ошибка при получении идей")
            else:
                await update.edit_message_text("❌ Произошла ошибка при получении идей")
    
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
        elif content == "📋 Мои задачи":
            await self.list_tasks_command(update, context)
            return
        elif content == "📊 Статистика":
            await self.stats_command(update, context)
            return
        elif content == "📅 За сегодня":
            await self.today_command(update, context)
            return
        elif content == "📅 Задачи за сегодня":
            await self.today_tasks_command(update, context)
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
            
            # Сохраняем контент для последующего выбора типа
            context.user_data['pending_content'] = content
            
            # Спрашиваем, что это: идея или задача
            keyboard = [
                [InlineKeyboardButton("💡 Идея", callback_data="save_idea")],
                [InlineKeyboardButton("📋 Задача", callback_data="save_task")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Что это?\n\n📝 {content}",
                reply_markup=reply_markup
            )
            
        except ValidationError as e:
            await update.message.reply_text(f"❌ {str(e)}")
        except Exception as e:
            logger.error(f"Ошибка обработки текстового сообщения: {e}")
            await update.message.reply_text("❌ Произошла ошибка при обработке сообщения")
    
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
            idea_stats = self.idea_repo.get_user_stats(user_id)
            task_stats = self.task_repo.get_user_stats(user_id)
            user_settings = self.user_repo.get_or_create_user_settings(user_id)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz).strftime('%H:%M')
            
            response = f"""
📊 Ваша статистика:

💡 ИДЕИ:
📝 Всего идей: {idea_stats['total_ideas']}
✅ Выполнено: {idea_stats['done_ideas']}
⏳ В ожидании: {idea_stats['pending_ideas']}
📅 За сегодня: {idea_stats['today_ideas']}

📋 ЗАДАЧИ:
📝 Всего задач: {task_stats['total_tasks']}
✅ Выполнено: {task_stats['done_tasks']}
⏳ В ожидании: {task_stats['pending_tasks']}
📅 За сегодня: {task_stats['today_tasks']}

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
            [KeyboardButton("📝 Мои идеи"), KeyboardButton("📋 Мои задачи")],
            [KeyboardButton("📅 За сегодня"), KeyboardButton("📅 Задачи за сегодня")],
            [KeyboardButton("📊 Статистика"), KeyboardButton("✅ Выполненные")],
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
        elif query.data == "mark_tasks_done":
            await self.show_pending_tasks_for_done(query, user_id)
        elif query.data == "stats":
            await self.stats_callback(query, user_id)
        elif query.data == "today":
            await self.today_callback(query, user_id)
        elif query.data == "today_tasks":
            await self.today_tasks_callback(query, user_id)
        elif query.data == "my_ideas":
            context.user_data['last_viewed'] = 'ideas'
            await self.list_callback(query, user_id)
        elif query.data == "my_tasks":
            context.user_data['last_viewed'] = 'tasks'
            await self.list_tasks_callback(query, user_id)
        elif query.data == "save_idea":
            await self.save_idea_callback(update, context)
        elif query.data == "save_task":
            await self.save_task_callback(update, context)
        elif query.data.startswith("done_idea_"):
            # Обработка inline кнопок для отметки идей как выполненных
            idea_id = int(query.data.replace("done_idea_", ""))
            await self.mark_idea_done_callback(query, user_id, idea_id)
        elif query.data.startswith("done_task_"):
            # Обработка inline кнопок для отметки задач как выполненных
            task_id = int(query.data.replace("done_task_", ""))
            await self.mark_task_done_callback(query, user_id, task_id)
        elif query.data.startswith("show_idea_"):
            # Обработка показа полного текста идеи
            idea_id = int(query.data.replace("show_idea_", ""))
            await self.show_full_idea(query, user_id, idea_id)
        elif query.data.startswith("show_task_"):
            # Обработка показа полного текста задачи
            task_id = int(query.data.replace("show_task_", ""))
            await self.show_full_task(query, user_id, task_id)
        elif query.data.startswith("ideas_page_"):
            # Обработка пагинации идей
            page_num = int(query.data.replace("ideas_page_", ""))
            await self.show_ideas_page(query, context, page_num)
        elif query.data.startswith("tasks_page_"):
            # Обработка пагинации задач
            page_num = int(query.data.replace("tasks_page_", ""))
            await self.show_tasks_page(query, context, page_num)
        elif query.data.startswith("today_tasks_page_"):
            # Обработка пагинации задач за сегодня
            page_num = int(query.data.replace("today_tasks_page_", ""))
            await self.show_today_tasks_page(query, context, page_num)
        elif query.data.startswith("today_ideas_page_"):
            # Обработка пагинации идей за сегодня
            page_num = int(query.data.replace("today_ideas_page_", ""))
            await self.show_today_ideas_page(query, context, page_num)
        elif query.data.startswith("undo_idea_"):
            # Обработка отмены выполнения идеи
            idea_id = int(query.data.replace("undo_idea_", ""))
            await self.undo_idea_done_callback(query, user_id, idea_id)
        elif query.data.startswith("undo_task_"):
            # Обработка отмены выполнения задачи
            task_id = int(query.data.replace("undo_task_", ""))
            await self.undo_task_done_callback(query, user_id, task_id)
    
    async def stats_callback(self, query, user_id):
        """Callback для статистики."""
        try:
            idea_stats = self.idea_repo.get_user_stats(user_id)
            task_stats = self.task_repo.get_user_stats(user_id)
            user_settings = self.user_repo.get_or_create_user_settings(user_id)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            current_time = datetime.now(moscow_tz).strftime('%H:%M')
            
            response = f"""
📊 Ваша статистика:

💡 ИДЕИ:
📝 Всего идей: {idea_stats['total_ideas']}
✅ Выполнено: {idea_stats['done_ideas']}
⏳ В ожидании: {idea_stats['pending_ideas']}
📅 За сегодня: {idea_stats['today_ideas']}

📋 ЗАДАЧИ:
📝 Всего задач: {task_stats['total_tasks']}
✅ Выполнено: {task_stats['done_tasks']}
⏳ В ожидании: {task_stats['pending_tasks']}
📅 За сегодня: {task_stats['today_tasks']}

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
            # Получаем все идеи за сегодня
            all_ideas = self.idea_repo.get_ideas_today(user_id)
            
            if not all_ideas:
                await query.edit_message_text("📝 У вас пока нет идей за сегодня")
                return
            
            # Создаем временный context для callback
            class TempContext:
                def __init__(self):
                    self.user_data = {'all_today_ideas': all_ideas, 'today_ideas_page': 0}
            
            temp_context = TempContext()
            await self.show_today_ideas_page(query, temp_context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения идей за сегодня: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении идей")
    
    async def today_tasks_callback(self, query, user_id):
        """Callback для задач за сегодня."""
        try:
            # Получаем все задачи за сегодня
            all_tasks = self.task_repo.get_tasks_today(user_id)
            
            if not all_tasks:
                await query.edit_message_text("📅 У вас нет задач за сегодня")
                return
            
            # Создаем временный context для callback
            class TempContext:
                def __init__(self):
                    self.user_data = {'all_today_tasks': all_tasks, 'today_tasks_page': 0}
            
            temp_context = TempContext()
            await self.show_today_tasks_page(query, temp_context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения задач за сегодня: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении задач")
    
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
    
    async def show_pending_tasks_for_done(self, query, user_id):
        """Показать невыполненные задачи для отметки как выполненные."""
        try:
            # Получаем только невыполненные задачи
            pending_tasks = self.task_repo.get_tasks_by_user(user_id, limit=10)
            pending_tasks = [task for task in pending_tasks if not task.is_done]
            
            if not pending_tasks:
                await query.edit_message_text("🎉 У вас нет невыполненных задач!")
                return
            
            response = "✅ Выберите задачу для отметки как выполненную:\n\n"
            
            # Создаем inline кнопки
            keyboard = []
            
            for i, task in enumerate(pending_tasks, 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = task.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y')
                time_str = moscow_time.strftime('%H:%M')
                
                # Обрезаем длинный текст
                content_preview = task.content[:60] + "..." if len(task.content) > 60 else task.content
                
                response += f"**{i}.** {content_preview}\n"
                response += f"   📅 {date_str} в {time_str}\n\n"
                
                # Добавляем кнопку для каждой задачи
                button_text = f"✅ {i}"
                callback_data = f"done_task_{task.id}"
                keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
            
            response += "💡 **Или введите номер:** `1`, `2`, `3` и т.д."
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка получения невыполненных задач: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении задач")
    
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
    
    async def mark_task_done_callback(self, query, user_id, task_id):
        """Отметить задачу как выполненную через inline кнопку."""
        try:
            task = self.task_repo.get_task_by_id(task_id, user_id)
            
            if not task:
                await query.edit_message_text("❌ Задача не найдена")
                return
            
            if task.is_done:
                await query.edit_message_text("✅ Задача уже отмечена как выполненная!")
                return
            
            # Отмечаем как выполненную
            task.is_done = True
            self.task_repo.db.commit()
            
            await query.edit_message_text(f"✅ Задача #{task.id} отмечена как выполненная!\n\n📋 {task.content}")
            logger.info(f"Пользователь {user_id} отметил задачу {task.id} как выполненную через inline кнопку")
            
        except Exception as e:
            logger.error(f"Ошибка отметки задачи как выполненной: {e}")
            await query.edit_message_text("❌ Произошла ошибка при отметке задачи")
    
    async def undo_idea_done_callback(self, query, user_id, idea_id):
        """Отменить отметку идеи как выполненной через inline кнопку."""
        try:
            idea = self.idea_repo.get_idea_by_id(idea_id, user_id)
            
            if not idea:
                await query.edit_message_text("❌ Идея не найдена")
                return
            
            if not idea.is_done:
                await query.edit_message_text("⏳ Идея уже отмечена как невыполненная!")
                return
            
            # Отменяем отметку как выполненную
            idea.is_done = False
            self.idea_repo.db.commit()
            
            await query.edit_message_text(f"⏳ Идея #{idea.id} отмечена как невыполненная!\n\n💡 {idea.content}")
            logger.info(f"Пользователь {user_id} отменил отметку идеи {idea.id} как выполненной через inline кнопку")
            
        except Exception as e:
            logger.error(f"Ошибка отмены отметки идеи как выполненной: {e}")
            await query.edit_message_text("❌ Произошла ошибка при отмене отметки идеи")
    
    async def undo_task_done_callback(self, query, user_id, task_id):
        """Отменить отметку задачи как выполненной через inline кнопку."""
        try:
            task = self.task_repo.get_task_by_id(task_id, user_id)
            
            if not task:
                await query.edit_message_text("❌ Задача не найдена")
                return
            
            if not task.is_done:
                await query.edit_message_text("⏳ Задача уже отмечена как невыполненная!")
                return
            
            # Отменяем отметку как выполненную
            task.is_done = False
            self.task_repo.db.commit()
            
            await query.edit_message_text(f"⏳ Задача #{task.id} отмечена как невыполненная!\n\n📋 {task.content}")
            logger.info(f"Пользователь {user_id} отменил отметку задачи {task.id} как выполненной через inline кнопку")
            
        except Exception as e:
            logger.error(f"Ошибка отмены отметки задачи как выполненной: {e}")
            await query.edit_message_text("❌ Произошла ошибка при отмене отметки задачи")
    
    async def show_full_idea(self, query, user_id, idea_id):
        """Показать полный текст идеи."""
        try:
            idea = self.idea_repo.get_idea_by_id(idea_id, user_id)
            
            if not idea:
                await query.edit_message_text("❌ Идея не найдена")
                return
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = idea.created_at.astimezone(moscow_tz)
            date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
            status = "✅" if idea.is_done else "⏳"
            
            response = f"""💡 **Полный текст идеи #{idea.id}**

{status} **Статус:** {'Выполнена' if idea.is_done else 'В ожидании'}
📅 **Дата создания:** {date_str}
📝 **Содержание:**

{idea.content}"""
            
            # Кнопка "Назад" для возврата к списку
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку", callback_data="my_ideas")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа полного текста идеи: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении идеи")
    
    async def show_full_task(self, query, user_id, task_id):
        """Показать полный текст задачи."""
        try:
            task = self.task_repo.get_task_by_id(task_id, user_id)
            
            if not task:
                await query.edit_message_text("❌ Задача не найдена")
                return
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = task.created_at.astimezone(moscow_tz)
            date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
            status = "✅" if task.is_done else "⏳"
            
            response = f"""📋 **Полный текст задачи #{task.id}**

{status} **Статус:** {'Выполнена' if task.is_done else 'В ожидании'}
📅 **Дата создания:** {date_str}
📝 **Содержание:**

{task.content}"""
            
            # Кнопка "Назад" для возврата к списку
            keyboard = [
                [InlineKeyboardButton("⬅️ Назад к списку", callback_data="my_tasks")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(response, parse_mode='Markdown', reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа полного текста задачи: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении задачи")
    
    async def handle_number_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, number: int):
        """Обработка ввода номера для отметки идеи или задачи как выполненной."""
        user_id = update.effective_user.id
        
        try:
            # Получаем контекст - какой список последний просматривал пользователь
            last_viewed = context.user_data.get('last_viewed', None)
            
            # Если контекст есть, ищем только в соответствующем списке
            if last_viewed == 'ideas':
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
                    return
                else:
                    await update.message.reply_text(f"❌ Идея #{number} не найдена в вашем списке")
                    return
            
            elif last_viewed == 'tasks':
                task = self.task_repo.get_task_by_user_number(user_id, number)
                if task:
                    if task.is_done:
                        await update.message.reply_text(f"✅ Задача #{number} уже отмечена как выполненная!")
                        return
                    
                    # Отмечаем как выполненную
                    task.is_done = True
                    self.task_repo.db.commit()
                    
                    await update.message.reply_text(f"✅ Задача #{number} отмечена как выполненная!\n\n📋 {task.content}")
                    logger.info(f"Пользователь {user_id} отметил задачу {task.id} (номер {number}) как выполненную через номер")
                    return
                else:
                    await update.message.reply_text(f"❌ Задача #{number} не найдена в вашем списке")
                    return
            
            # Если контекста нет, ищем в обеих таблицах (старая логика)
            idea = self.idea_repo.get_idea_by_user_number(user_id, number)
            task = self.task_repo.get_task_by_user_number(user_id, number)
            
            # Если найдена и идея, и задача с одинаковым номером
            if idea and task:
                await update.message.reply_text(f"❓ Найдены и идея, и задача с номером {number}.\n\nИспользуйте команды:\n/done_idea {number} - для идеи\n/done_task {number} - для задачи")
                return
            
            # Если найдена только идея
            if idea:
                if idea.is_done:
                    await update.message.reply_text(f"✅ Идея #{number} уже отмечена как выполненная!")
                    return
                
                # Отмечаем как выполненную
                idea.is_done = True
                self.idea_repo.db.commit()
                
                await update.message.reply_text(f"✅ Идея #{number} отмечена как выполненная!\n\n💡 {idea.content}")
                logger.info(f"Пользователь {user_id} отметил идею {idea.id} (номер {number}) как выполненную через номер")
                return
            
            # Если найдена только задача
            if task:
                if task.is_done:
                    await update.message.reply_text(f"✅ Задача #{number} уже отмечена как выполненная!")
                    return
                
                # Отмечаем как выполненную
                task.is_done = True
                self.task_repo.db.commit()
                
                await update.message.reply_text(f"✅ Задача #{number} отмечена как выполненная!\n\n📋 {task.content}")
                logger.info(f"Пользователь {user_id} отметил задачу {task.id} (номер {number}) как выполненную через номер")
                return
            
            # Если ничего не найдено
            await update.message.reply_text(f"❌ Идея или задача #{number} не найдена в вашем списке")
                
        except Exception as e:
            logger.error(f"Ошибка обработки номера {number}: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отметке")
    
    async def done_idea_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /done_idea."""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите номер идеи: /done_idea <номер>\n\nПример: /done_idea 1")
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
    
    async def done_task_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /done_task."""
        user_id = update.effective_user.id
        
        if not context.args:
            await update.message.reply_text("❌ Укажите номер задачи: /done_task <номер>\n\nПример: /done_task 1")
            return
        
        try:
            number = int(context.args[0])
            
            # Ищем задачу по номеру в списке пользователя
            task = self.task_repo.get_task_by_user_number(user_id, number)
            
            if task:
                if task.is_done:
                    await update.message.reply_text(f"✅ Задача #{number} уже отмечена как выполненная!")
                    return
                
                # Отмечаем как выполненную
                task.is_done = True
                self.task_repo.db.commit()
                
                await update.message.reply_text(f"✅ Задача #{number} отмечена как выполненная!\n\n📋 {task.content}")
                logger.info(f"Пользователь {user_id} отметил задачу {task.id} (номер {number}) как выполненную")
            else:
                await update.message.reply_text(f"❌ Задача #{number} не найдена в вашем списке")
                
        except ValueError:
            await update.message.reply_text("❌ Номер задачи должен быть числом")
        except Exception as e:
            logger.error(f"Ошибка отметки задачи как выполненной: {e}")
            await update.message.reply_text("❌ Произошла ошибка при отметке задачи")
    
    async def list_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать последние задачи пользователя."""
        user_id = update.effective_user.id
        
        try:
            # Получаем все задачи пользователя
            all_tasks = self.task_repo.get_tasks_by_user(user_id, limit=1000)  # Большой лимит для получения всех
            
            if not all_tasks:
                await update.message.reply_text("📋 У вас пока нет задач.\n\nОтправьте текстовое сообщение, чтобы создать задачу!")
                return
            
            # Сохраняем контекст - пользователь смотрит список задач
            context.user_data['last_viewed'] = 'tasks'
            context.user_data['tasks_page'] = 0  # Начинаем с первой страницы
            context.user_data['all_tasks'] = all_tasks  # Сохраняем все задачи
            
            await self.show_tasks_page(update, context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения задач: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении задач")
    
    async def show_tasks_page(self, update, context, page_num):
        """Показать страницу с задачами."""
        try:
            all_tasks = context.user_data.get('all_tasks', [])
            if not all_tasks:
                await update.message.reply_text("📋 У вас пока нет задач")
                return
            
            items_per_page = 10
            total_pages = (len(all_tasks) + items_per_page - 1) // items_per_page
            start_idx = page_num * items_per_page
            end_idx = start_idx + items_per_page
            tasks = all_tasks[start_idx:end_idx]
            
            response = f"📋 Ваши задачи (стр. {page_num + 1}/{total_pages}):\n\n"
            
            # Создаем кнопки для быстрого доступа
            keyboard = []
            
            for i, task in enumerate(tasks, start_idx + 1):
                moscow_tz = pytz.timezone('Europe/Moscow')
                moscow_time = task.created_at.astimezone(moscow_tz)
                date_str = moscow_time.strftime('%d.%m.%Y %H:%M')
                content_preview = task.content[:50] + "..." if len(task.content) > 50 else task.content
                status = "✅" if task.is_done else "⏳"
                response += f"{status} {i}. ({date_str})\n{content_preview}\n\n"
                
                # Добавляем кнопки для каждой задачи
                task_buttons = []
                
                # Кнопка "Показать полностью" для длинных задач
                if len(task.content) > 50:
                    task_buttons.append(InlineKeyboardButton(f"📖 {i}", callback_data=f"show_task_{task.id}"))
                
                # Кнопка выполнения/отмены выполнения
                if task.is_done:
                    task_buttons.append(InlineKeyboardButton(f"❌ {i}", callback_data=f"undo_task_{task.id}"))
                else:
                    task_buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"done_task_{task.id}"))
                
                if task_buttons:
                    keyboard.append(task_buttons)
            
            # Добавляем кнопки пагинации
            pagination_buttons = []
            if page_num > 0:
                pagination_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"tasks_page_{page_num - 1}"))
            if page_num < total_pages - 1:
                pagination_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"tasks_page_{page_num + 1}"))
            
            if pagination_buttons:
                keyboard.append(pagination_buttons)
            
            # Добавляем основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("📅 За сегодня", callback_data="today_tasks")]
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'message'):
                await update.message.reply_text(response, reply_markup=reply_markup)
            else:
                await update.edit_message_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа страницы задач: {e}")
            if hasattr(update, 'message'):
                await update.message.reply_text("❌ Произошла ошибка при получении задач")
            else:
                await update.edit_message_text("❌ Произошла ошибка при получении задач")
    
    async def today_tasks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать задачи за сегодня."""
        user_id = update.effective_user.id
        
        try:
            # Получаем все задачи за сегодня
            all_tasks = self.task_repo.get_tasks_today(user_id)
            
            if not all_tasks:
                await update.message.reply_text("📅 У вас нет задач за сегодня.\n\nОтправьте текстовое сообщение, чтобы создать задачу!")
                return
            
            # Сохраняем контекст для пагинации
            context.user_data['today_tasks_page'] = 0
            context.user_data['all_today_tasks'] = all_tasks
            
            await self.show_today_tasks_page(update, context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения задач за сегодня: {e}")
            await update.message.reply_text("❌ Произошла ошибка при получении задач")
    
    async def show_today_tasks_page(self, update, context, page_num):
        """Показать страницу с задачами за сегодня."""
        try:
            all_tasks = context.user_data.get('all_today_tasks', [])
            if not all_tasks:
                await update.message.reply_text("📅 У вас нет задач за сегодня")
                return
            
            items_per_page = 10
            total_pages = (len(all_tasks) + items_per_page - 1) // items_per_page
            start_idx = page_num * items_per_page
            end_idx = start_idx + items_per_page
            tasks = all_tasks[start_idx:end_idx]
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            today = datetime.now(moscow_tz).strftime('%d.%m.%Y')
            
            response = f"📅 Задачи за сегодня ({today}, стр. {page_num + 1}/{total_pages}):\n\n"
            
            # Создаем кнопки для быстрого доступа
            keyboard = []
            
            for i, task in enumerate(tasks, start_idx + 1):
                moscow_time = task.created_at.astimezone(moscow_tz)
                time_str = moscow_time.strftime('%H:%M')
                content_preview = task.content[:50] + "..." if len(task.content) > 50 else task.content
                status = "✅" if task.is_done else "⏳"
                response += f"{status} {i}. {time_str}: {content_preview}\n\n"
                
                # Добавляем кнопки для каждой задачи
                task_buttons = []
                
                # Кнопка "Показать полностью" для длинных задач
                if len(task.content) > 50:
                    task_buttons.append(InlineKeyboardButton(f"📖 {i}", callback_data=f"show_task_{task.id}"))
                
                # Кнопка выполнения/отмены выполнения
                if task.is_done:
                    task_buttons.append(InlineKeyboardButton(f"❌ {i}", callback_data=f"undo_task_{task.id}"))
                else:
                    task_buttons.append(InlineKeyboardButton(f"✅ {i}", callback_data=f"done_task_{task.id}"))
                
                if task_buttons:
                    keyboard.append(task_buttons)
            
            # Добавляем кнопки пагинации
            pagination_buttons = []
            if page_num > 0:
                pagination_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"today_tasks_page_{page_num - 1}"))
            if page_num < total_pages - 1:
                pagination_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"today_tasks_page_{page_num + 1}"))
            
            if pagination_buttons:
                keyboard.append(pagination_buttons)
            
            # Добавляем основные кнопки
            keyboard.extend([
                [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
                [InlineKeyboardButton("📅 За сегодня", callback_data="today_tasks")]
            ])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if hasattr(update, 'message'):
                await update.message.reply_text(response, reply_markup=reply_markup)
            else:
                await update.edit_message_text(response, reply_markup=reply_markup)
            
        except Exception as e:
            logger.error(f"Ошибка показа страницы задач за сегодня: {e}")
            if hasattr(update, 'message'):
                await update.message.reply_text("❌ Произошла ошибка при получении задач")
            else:
                await update.edit_message_text("❌ Произошла ошибка при получении задач")
    
    async def save_idea_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для сохранения идеи."""
        user_id = update.effective_user.id
        query = update.callback_query
        await query.answer()
        
        try:
            content = context.user_data.get('pending_content')
            if not content:
                await query.edit_message_text("❌ Контент не найден. Попробуйте снова.")
                return
            
            idea = self.idea_repo.create_idea(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = idea.created_at.astimezone(moscow_tz)
            
            response = f"💡 Идея сохранена! (ID: {idea.id}, время МСК: {moscow_time.strftime('%H:%M')})"
            await query.edit_message_text(response)
            
            # Очищаем pending_content
            context.user_data.pop('pending_content', None)
            
            logger.info(f"Пользователь {user_id} сохранил идею через callback: {idea.id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения идеи через callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка при сохранении идеи")
    
    async def save_task_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Callback для сохранения задачи."""
        user_id = update.effective_user.id
        query = update.callback_query
        await query.answer()
        
        try:
            content = context.user_data.get('pending_content')
            if not content:
                await query.edit_message_text("❌ Контент не найден. Попробуйте снова.")
                return
            
            task = self.task_repo.create_task(user_id, content)
            
            # Обновляем streak
            self.user_repo.update_streak(user_id, increment=True)
            
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_time = task.created_at.astimezone(moscow_tz)
            
            response = f"📋 Задача сохранена! (ID: {task.id}, время МСК: {moscow_time.strftime('%H:%M')})"
            await query.edit_message_text(response)
            
            # Очищаем pending_content
            context.user_data.pop('pending_content', None)
            
            logger.info(f"Пользователь {user_id} сохранил задачу через callback: {task.id}")
            
        except Exception as e:
            logger.error(f"Ошибка сохранения задачи через callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка при сохранении задачи")
    
    async def list_callback(self, query, user_id):
        """Callback для показа идей."""
        try:
            # Получаем все идеи пользователя
            all_ideas = self.idea_repo.get_ideas_by_user(user_id, limit=1000)
            
            if not all_ideas:
                await query.edit_message_text("📝 У вас пока нет идей.\n\nОтправьте текстовое сообщение, чтобы создать идею!")
                return
            
            # Создаем временный context для callback
            class TempContext:
                def __init__(self):
                    self.user_data = {'all_ideas': all_ideas, 'ideas_page': 0}
            
            temp_context = TempContext()
            await self.show_ideas_page(query, temp_context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения идей через callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении идей")
    
    async def list_tasks_callback(self, query, user_id):
        """Callback для показа задач."""
        try:
            # Получаем все задачи пользователя
            all_tasks = self.task_repo.get_tasks_by_user(user_id, limit=1000)
            
            if not all_tasks:
                await query.edit_message_text("📋 У вас пока нет задач.\n\nОтправьте текстовое сообщение, чтобы создать задачу!")
                return
            
            # Создаем временный context для callback
            class TempContext:
                def __init__(self):
                    self.user_data = {'all_tasks': all_tasks, 'tasks_page': 0}
            
            temp_context = TempContext()
            await self.show_tasks_page(query, temp_context, 0)
            
        except Exception as e:
            logger.error(f"Ошибка получения задач через callback: {e}")
            await query.edit_message_text("❌ Произошла ошибка при получении задач")
    
    def get_handlers(self):
        """Получение всех обработчиков."""
        return [
            CommandHandler("start", self.start_command),
            CommandHandler("help", self.help_command),
            CommandHandler("save", self.save_command),
            CommandHandler("list", self.list_command),
            CommandHandler("tasks", self.list_tasks_command),
            CommandHandler("today", self.today_command),
            CommandHandler("today_tasks", self.today_tasks_command),
            CommandHandler("done", self.done_command),
            CommandHandler("done_idea", self.done_idea_command),
            CommandHandler("done_task", self.done_task_command),
            CommandHandler("stats", self.stats_command),
            CommandHandler("edit", self.edit_command),
            CallbackQueryHandler(self.button_callback),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message),
        ]
