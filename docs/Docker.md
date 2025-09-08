# Инструкция по разворачиванию Idea Bot через Docker

## 🐳 Настройка Docker для автоматического запуска

### 1. Подготовка окружения

#### Создание .env файла
```bash
# Создайте файл .env в корне проекта
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_BASE_URL=http://localhost:11434
DATABASE_URL=sqlite:///data/ideas.db
LOG_LEVEL=INFO
LOG_FILE=/app/logs/idea_bot.log
DIGEST_TIME=08:00
TIMEZONE=Europe/Moscow
EOF
```

#### Создание необходимых директорий
```bash
mkdir -p data logs temp_audio backup
chmod 755 data logs temp_audio backup
```

### 2. Настройка Docker Compose

#### Обновленный docker-compose.yml
```yaml
version: '3.8'

services:
  idea-bot:
    build: .
    container_name: idea-bot
    restart: unless-stopped
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - OLLAMA_BASE_URL=${OLLAMA_BASE_URL}
      - DATABASE_URL=${DATABASE_URL}
      - LOG_LEVEL=${LOG_LEVEL}
      - LOG_FILE=${LOG_FILE}
      - DIGEST_TIME=${DIGEST_TIME}
      - TIMEZONE=${TIMEZONE}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./temp_audio:/app/temp_audio
      - ./backup:/app/backup
    networks:
      - idea-bot-network
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

networks:
  idea-bot-network:
    driver: bridge
```

### 3. Обновление Dockerfile

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt
COPY requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY . .

# Создание необходимых директорий
RUN mkdir -p data logs temp_audio backup

# Установка прав доступа
RUN chmod 755 data logs temp_audio backup

# Создание пользователя для безопасности
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Health check endpoint
EXPOSE 8000

# Команда запуска
CMD ["python", "-m", "src.main"]
```

### 4. Настройка автозапуска

#### Для Linux (systemd)

Создайте файл сервиса:
```bash
sudo nano /etc/systemd/system/idea-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Idea Bot Docker Container
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/your/idea-bot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активация сервиса:
```bash
# Замените /path/to/your/idea-bot на реальный путь
sudo systemctl daemon-reload
sudo systemctl enable idea-bot.service
sudo systemctl start idea-bot.service
```

#### Для Windows (Task Scheduler)

1. Откройте "Планировщик заданий"
2. Создайте новое задание:
   - **Имя**: Idea Bot Auto Start
   - **Триггер**: При запуске компьютера
   - **Действие**: Запуск программы
   - **Программа**: `docker-compose`
   - **Аргументы**: `up -d`
   - **Рабочая папка**: путь к проекту

#### Для macOS (LaunchAgent)

Создайте файл:
```bash
nano ~/Library/LaunchAgents/com.idea-bot.plist
```

Содержимое:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.idea-bot</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/docker-compose</string>
        <string>up</string>
        <string>-d</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/your/idea-bot</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

Загрузка:
```bash
launchctl load ~/Library/LaunchAgents/com.idea-bot.plist
```

### 5. Скрипты управления

#### Создание скрипта запуска
```bash
cat > start-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose up -d
echo "Idea Bot started successfully"
EOF

chmod +x start-bot.sh
```

#### Создание скрипта остановки
```bash
cat > stop-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose down
echo "Idea Bot stopped successfully"
EOF

chmod +x stop-bot.sh
```

#### Создание скрипта перезапуска
```bash
cat > restart-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
docker-compose down
docker-compose up -d
echo "Idea Bot restarted successfully"
EOF

chmod +x restart-bot.sh
```

### 6. Мониторинг и логи

#### Скрипт мониторинга
```bash
cat > monitor-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "=== Idea Bot Status ==="
docker-compose ps

echo -e "\n=== Recent Logs ==="
docker-compose logs --tail=20 idea-bot

echo -e "\n=== Health Check ==="
if docker-compose ps | grep -q "Up"; then
    echo "✅ Bot is running"
else
    echo "❌ Bot is not running"
fi
EOF

chmod +x monitor-bot.sh
```

#### Автоматическое резервное копирование
```bash
cat > backup-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

BACKUP_DIR="backup"
DATE=$(date +%Y%m%d_%H%M%S)

# Создание резервной копии базы данных
if [ -f "data/ideas.db" ]; then
    cp data/ideas.db "$BACKUP_DIR/ideas_$DATE.db"
    echo "Database backed up to $BACKUP_DIR/ideas_$DATE.db"
fi

# Создание резервной копии логов
if [ -f "logs/idea_bot.log" ]; then
    cp logs/idea_bot.log "$BACKUP_DIR/logs_$DATE.log"
    echo "Logs backed up to $BACKUP_DIR/logs_$DATE.log"
fi

# Удаление старых бэкапов (старше 30 дней)
find "$BACKUP_DIR" -name "*.db" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.log" -mtime +30 -delete

echo "Backup completed successfully"
EOF

chmod +x backup-bot.sh
```

### 7. Настройка cron для автоматических задач

```bash
# Добавьте в crontab
crontab -e

# Добавьте следующие строки:
# Ежедневное резервное копирование в 2:00
0 2 * * * /path/to/your/idea-bot/backup-bot.sh

# Проверка статуса каждые 5 минут
*/5 * * * * /path/to/your/idea-bot/monitor-bot.sh > /dev/null 2>&1

# Очистка старых логов еженедельно
0 3 * * 0 find /path/to/your/idea-bot/logs -name "*.log" -mtime +7 -delete
```

### 8. Проверка и тестирование

#### Проверка автозапуска
```bash
# Перезагрузка системы
sudo reboot

# После перезагрузки проверьте статус
docker-compose ps
docker-compose logs idea-bot
```

#### Тестирование восстановления
```bash
# Остановка контейнера
docker-compose down

# Проверка автозапуска (если настроен)
# Контейнер должен запуститься автоматически
```

### 9. Обновление и обслуживание

#### Скрипт обновления
```bash
cat > update-bot.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"

echo "Stopping bot..."
docker-compose down

echo "Pulling latest changes..."
git pull origin main

echo "Rebuilding container..."
docker-compose build --no-cache

echo "Starting bot..."
docker-compose up -d

echo "Update completed successfully"
EOF

chmod +x update-bot.sh
```

### 10. Устранение неполадок

#### Проверка логов
```bash
# Просмотр логов в реальном времени
docker-compose logs -f idea-bot

# Просмотр последних 100 строк
docker-compose logs --tail=100 idea-bot
```

#### Проверка ресурсов
```bash
# Использование ресурсов контейнером
docker stats idea-bot

# Проверка места на диске
docker system df
```

#### Восстановление после сбоя
```bash
# Полная переустановка
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 11. Безопасность

#### Настройка файрвола (Linux)
```bash
# Разрешить только необходимые порты
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

#### Регулярное обновление
```bash
# Добавьте в crontab для еженедельного обновления
0 4 * * 1 /path/to/your/idea-bot/update-bot.sh
```

### 12. Финальная проверка

После настройки выполните:
```bash
# Проверка статуса
./monitor-bot.sh

# Проверка автозапуска
sudo systemctl status idea-bot  # Linux
# или проверьте Task Scheduler в Windows
# или launchctl list | grep idea-bot в macOS

# Тест перезагрузки
sudo reboot
# После перезагрузки проверьте, что бот запустился автоматически
```

Теперь ваш Idea Bot будет автоматически запускаться при включении компьютера и работать в фоновом режиме без зависимости от консоли.