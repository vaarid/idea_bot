# Руководство по разработке Idea Bot

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

# Руководство по администрированию Idea Bot

## �� Запуск и остановка

### Запуск бота
```bash
# Основной способ запуска
python -m src.main

# Альтернативный способ
python src/main.py

# Через Docker
docker-compose up --build
```

### Остановка бота
```bash
# В консоли нажмите Ctrl+C
# Или через Docker
docker-compose down
```

## 🗄️ Управление базой данных

### Очистка базы данных
```bash
# Удаление некорректных записей (названия кнопок)
python clean_database.py
```

### Миграция базы данных
```bash
# Полная пересоздание базы данных
python migrate_db.py
```

### Создание таблиц
```bash
python -c "from src.core.models import create_tables; create_tables()"
```

## 📊 Мониторинг и логи

### Просмотр логов
```bash
# Логи в реальном времени
tail -f logs/idea_bot.log

# Последние 100 строк
tail -n 100 logs/idea_bot.log

# Поиск ошибок
grep -i error logs/idea_bot.log
```

### Проверка статуса
```bash
# Проверка конфигурации
python -c "from config.settings import settings; print('Token:', bool(settings.telegram_bot_token))"

# Проверка базы данных
python -c "from src.core.models import engine; print('DB OK' if engine else 'DB Error')"
```

## 🔧 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный тест
pytest tests/test_models.py

# Покрытие кода
pytest --cov=src --cov-report=html
```

### Тестирование компонентов
```bash
# Тест аудио сервиса
python test_audio.py

# Тест Whisper
python test_whisper.py
```

## 🐳 Docker команды

### Управление контейнерами
```bash
# Сборка и запуск
docker-compose up --build

# Запуск в фоне
docker-compose up -d

# Остановка
docker-compose down

# Пересборка
docker-compose build --no-cache

# Просмотр логов
docker-compose logs -f
```

## 🔄 Обновление и развертывание

### Обновление кода
```bash
# Получение обновлений
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt

# Перезапуск
docker-compose up --build -d
```

### Резервное копирование
```bash
# Копирование базы данных
cp ideas.db backup/ideas_$(date +%Y%m%d_%H%M%S).db

# Копирование логов
cp logs/idea_bot.log backup/logs_$(date +%Y%m%d_%H%M%S).log
```

## 🛠️ Диагностика проблем

### Проверка зависимостей
```bash
# Проверка установленных пакетов
pip list | grep -E "(telegram|pytz|sqlalchemy)"

# Проверка версий
python -c "import telegram; print('Telegram Bot:', telegram.__version__)"
python -c "import pytz; print('pytz:', pytz.__version__)"
```

### Проверка конфигурации
```bash
# Проверка .env файла
python -c "from config.settings import settings; print('Settings loaded:', bool(settings.telegram_bot_token))"

# Проверка токена
python -c "from config.settings import settings; print('Token length:', len(settings.telegram_bot_token))"
```

### Отладка
```bash
# Запуск с отладкой
python -c "
import sys
sys.path.insert(0, '.')
from src.main import main
try:
    main()
except Exception as e:
    import traceback
    print('Error:', e)
    traceback.print_exc()
"
```

## �� Статистика и аналитика

### Просмотр статистики базы данных
```bash
python -c "
from src.core.models import SessionLocal, Idea, UserSettings
db = SessionLocal()
ideas_count = db.query(Idea).count()
users_count = db.query(UserSettings).count()
print(f'Идей: {ideas_count}, Пользователей: {users_count}')
db.close()
"
```

### Экспорт данных
```bash
# Экспорт в CSV (если реализован)
python -c "
from src.core.database import IdeaRepository
from src.core.models import SessionLocal
import pandas as pd

db = SessionLocal()
repo = IdeaRepository(db)
ideas = repo.get_all_ideas()
df = pd.DataFrame([(i.id, i.user_id, i.content, i.created_at) for i in ideas])
df.to_csv('ideas_export.csv', index=False)
print('Экспорт завершен')
"
```

## 🔐 Безопасность

### Проверка токенов
```bash
# Проверка наличия токенов в .env
grep -E "TOKEN|KEY" .env | wc -l

# Проверка безопасности файлов
chmod 600 .env
```

### Очистка временных файлов
```bash
# Очистка аудио файлов
rm -rf temp_audio/*

# Очистка логов старше 30 дней
find logs/ -name "*.log" -mtime +30 -delete
```

## �� Устранение неполадок

### Проблемы с токеном
- Убедитесь, что `.env` файл существует
- Проверьте правильность токена бота
- Токен должен быть получен от @BotFather

### Проблемы с базой данных
- Проверьте права доступа к файлу БД
- Убедитесь, что папка `data/` существует
- Используйте `python migrate_db.py` для пересоздания БД

### Проблемы с timezone
```bash
# Установка pytz
pip install pytz

# Проверка версии
python -c "import pytz; print('pytz version:', pytz.__version__)"
```

### Проблемы с зависимостями
```bash
# Переустановка зависимостей
pip install --upgrade -r requirements.txt

# Проверка конфликтов
pip check
```

## 📁 Структура проекта
src/
├── bot/ # Telegram бот
├── core/ # Бизнес-логика и модели
├── integrations/ # Внешние API
└── utils/ # Утилиты
tests/ # Тесты
config/ # Конфигурация
docs/ # Документация
logs/ # Логи
temp_audio/ # Временные аудио файлы

## 🔧 Разработка

### Добавление новой команды
1. Создайте метод в `src/bot/handlers.py`
2. Добавьте обработчик в `get_handlers()`
3. Напишите тесты в `tests/`

### Работа с базой данных
- Модели: `src/core/models.py`
- Репозитории: `src/core/database.py`
- Миграции: через SQLAlchemy

### Логирование
```python
from src.utils.logger import logger

logger.info("Информационное сообщение")
logger.error("Ошибка")
```
## 📋 Быстрые команды

### Ежедневные задачи
```bash
# Проверка статуса
python -c "from config.settings import settings; print('Bot ready:', bool(settings.telegram_bot_token))"

# Очистка логов
find logs/ -name "*.log" -mtime +7 -delete

# Резервная копия
cp ideas.db backup/ideas_$(date +%Y%m%d).db
```

### Экстренные ситуации
```bash
# Остановка всех процессов
docker-compose down
pkill -f "python.*src.main"

# Восстановление из бэкапа
cp backup/ideas_YYYYMMDD.db ideas.db

# Полная переустановка
python migrate_db.py && python -m src.main
```
```