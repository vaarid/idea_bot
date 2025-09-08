# conventions.md

## Правила кодирования и стандарты【49†source】

### Общие принципы
- Читаемость и простота (KISS, DRY).  
- Понятные имена переменных и функций.  
- Комментарии для сложной логики.  
- Структурированная архитектура проекта.

### Структура проекта
```
idea_bot/
├── src/
│   ├── bot/              # Telegram-бот
│   ├── core/             # Бизнес-логика
│   ├── integrations/     # API интеграции (Whisper, Sheets)
│   └── utils/            # Утилиты
├── tests/                # Тесты
├── docker/               # Docker-конфигурации
├── config/               # Настройки и .env.example
└── docs/                 # Документация
```

---

## Python стандарты
- **Стиль кода**: PEP8.  
- **Имена переменных/функций**: snake_case.  
- **Классы**: PascalCase.  
- **Константы**: UPPER_CASE.  
- **Типизация**: использовать `typing` (List, Dict, Optional).  
- **Docstrings**: в формате Google или reST.

---

## Архитектурные паттерны
- **Repository Pattern** — слой данных.  
- **Service Layer** — бизнес-логика.  
- **Command Pattern** — выполнение команд.  
- **Observer Pattern** — уведомления.

---

## Обработка ошибок
- Базовое исключение `IdeaBotError`.  
- Специализированные: `ValidationError`, `AIProcessingError`, `DatabaseError`.  
- Логирование всех ошибок через стандартный `logging`.

---

## Логирование
- Уровни: DEBUG, INFO, ERROR.  
- Формат: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.  
- Файлы: `logs/idea_bot.log`.  
- Консольный и файловый хендлеры.

---

## Конфигурация
- Все чувствительные данные — через `.env`.  
- Пример файла `.env.example`:  
```
TELEGRAM_BOT_TOKEN="..."
OPENAI_API_KEY="..."
OLLAMA_BASE_URL="http://localhost:11434"
DATABASE_URL="sqlite:///ideas.db"
```

---

## Тестирование
- Использовать `pytest`.  
- Unit-тесты для сервисов.  
- Mock/patch для API.  
- Интеграционные тесты для команд бота.

---

## Docker и деплой
- **Dockerfile** — минимальный (python:3.11-slim).  
- **docker-compose.yml**: сервисы idea-bot + ollama.  
- **CI/CD**: GitHub Actions (тесты + build).

---

## Безопасность
- Валидация всех входящих данных.  
- Ограничения на размер сообщений/файлов.  
- Защита от XSS и инъекций.  
- Безопасное хранение токенов.

---

## Документация
- **README.md**: описание, установка, использование.  
- **API docs**: OpenAPI/Swagger (если подключен FastAPI).  
- **Комментарии**: для сложных функций и алгоритмов.

---

## Дополнения и рекомендации
- Включить **линтеры** (flake8, black).  
- Подключить **pre-commit hooks** для форматирования.  
- Добавить **coverage-тесты** (pytest-cov).  
- Обновлять **CHANGELOG.md** при каждой версии.
