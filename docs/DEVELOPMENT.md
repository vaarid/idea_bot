# Руководство по разработке Idea Bot

## 🚀 Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка окружения
```bash
# Скопируйте файл с примером настроек
cp .env.example .env

# Отредактируйте .env файл, добавив ваш токен бота
# TELEGRAM_BOT_TOKEN=your_actual_bot_token_here
```

### 3. Запуск бота
```bash
# Запуск через модуль
python -m src

# Или напрямую
python src/main.py
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# Конкретный тест
pytest tests/test_models.py::TestModels::test_idea_creation
```

### Покрытие кода
```bash
pytest --cov=src --cov-report=html
```

## 🐳 Docker

### Сборка и запуск
```bash
# Сборка образа
docker build -t idea-bot .

# Запуск с docker-compose
docker-compose up --build

# Запуск в фоне
docker-compose up -d
```

## 📁 Структура проекта

```
src/
├── bot/           # Telegram бот
├── core/          # Бизнес-логика и модели
├── integrations/  # Внешние API
└── utils/         # Утилиты

tests/             # Тесты
config/            # Конфигурация
docs/              # Документация
```

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

## 🚨 Отладка

### Проблемы с токеном
- Убедитесь, что `.env` файл существует
- Проверьте правильность токена бота
- Токен должен быть получен от @BotFather

### Проблемы с базой данных
- Проверьте права доступа к файлу БД
- Убедитесь, что папка `data/` существует

### Логи
- Логи сохраняются в `logs/idea_bot.log`
- Уровень логирования настраивается в `.env`
