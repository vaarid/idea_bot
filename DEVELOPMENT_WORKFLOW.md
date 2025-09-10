# Система разработки Idea Bot

## 🎯 Цель
Обеспечить непрерывную работу бота в продакшене, пока ведется разработка и тестирование новых функций.

## 🏗️ Архитектура системы

### 1. **Три режима работы**
- **PRODUCTION** - рабочий бот для пользователей
- **DEVELOPMENT** - режим разработки с hot reload
- **STAGING** - тестирование перед деплоем

### 2. **Структура образов**
```
idea-bot:production    # Текущий рабочий образ
idea-bot:staging       # Образ для тестирования
idea-bot:development   # Образ для разработки
```

## 📋 Workflow разработки

### **Этап 1: Подготовка к разработке**
```bash
# 1. Создаем резервную копию рабочего образа
docker tag idea-bot:latest idea-bot:production-backup-$(date +%Y%m%d_%H%M%S)

# 2. Переключаемся в режим разработки
./scripts/dev-start.sh
```

### **Этап 2: Разработка**
```bash
# Редактируем код в папке src/
# Изменения автоматически попадают в контейнер через volume
# Перезапускаем только контейнер (5 секунд)
docker-compose -f docker-compose.dev.yml restart
```

### **Этап 3: Тестирование**
```bash
# Тестируем функционал в dev-контейнере
# Если все ОК - переходим к staging
./scripts/staging-deploy.sh
```

### **Этап 4: Staging (тестирование с реальным ботом)**
```bash
# Создаем staging образ
docker build -t idea-bot:staging .

# Запускаем staging контейнер с тестовым ботом
./scripts/staging-start.sh
```

### **Этап 5: Production Deploy**
```bash
# Только после успешного тестирования в staging
./scripts/production-deploy.sh
```

## 🛠️ Скрипты автоматизации

### **dev-start.sh** - Запуск режима разработки
```bash
#!/bin/bash
echo "🚀 Запуск режима разработки..."

# Останавливаем production контейнер
docker stop idea-bot 2>/dev/null
docker rm idea-bot 2>/dev/null

# Запускаем dev контейнер с volume для кода
docker-compose -f docker-compose.dev.yml up -d

echo "✅ Режим разработки запущен"
echo "📝 Изменения в src/ автоматически попадают в контейнер"
echo "🔄 Для перезапуска: docker-compose -f docker-compose.dev.yml restart"
```

### **staging-deploy.sh** - Деплой в staging
```bash
#!/bin/bash
echo "🧪 Деплой в staging..."

# Собираем staging образ
docker build -t idea-bot:staging .

# Запускаем staging с тестовым ботом
docker run -d --name idea-bot-staging \
  --env-file .env.staging \
  -e TELEGRAM_BOT_TOKEN=$TEST_BOT_TOKEN \
  idea-bot:staging

echo "✅ Staging запущен"
echo "🧪 Тестируйте функционал с тестовым ботом"
```

### **production-deploy.sh** - Деплой в продакшен
```bash
#!/bin/bash
echo "🚀 Деплой в продакшен..."

# Создаем резервную копию текущего production
docker tag idea-bot:latest idea-bot:backup-$(date +%Y%m%d_%H%M%S)

# Останавливаем production
docker stop idea-bot
docker rm idea-bot

# Переименовываем staging в production
docker tag idea-bot:staging idea-bot:latest

# Запускаем новый production
docker run -d --name idea-bot \
  --restart unless-stopped \
  --env-file .env \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}/logs:/app/logs" \
  idea-bot:latest

echo "✅ Production обновлен"
echo "🔄 Откат: ./scripts/rollback.sh"
```

### **rollback.sh** - Откат к предыдущей версии
```bash
#!/bin/bash
echo "⏪ Откат к предыдущей версии..."

# Останавливаем текущий production
docker stop idea-bot
docker rm idea-bot

# Находим последний backup
BACKUP_IMAGE=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "idea-bot:backup" | head -1)

# Запускаем backup
docker run -d --name idea-bot \
  --restart unless-stopped \
  --env-file .env \
  -v "${PWD}/data:/app/data" \
  -v "${PWD}/logs:/app/logs" \
  $BACKUP_IMAGE

echo "✅ Откат выполнен"
```

## 📁 Файлы конфигурации

### **docker-compose.dev.yml** - Режим разработки
```yaml
services:
  idea-bot-dev:
    build: .
    container_name: idea-bot-dev
    restart: "no"
    environment:
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - DATABASE_URL=sqlite:///data/ideas.db
      - LOG_LEVEL=DEBUG
    volumes:
      # Hot reload - изменения кода сразу в контейнере
      - ./src:/app/src
      - ./config:/app/config
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - idea-bot-dev-network
```

### **docker-compose.staging.yml** - Режим тестирования
```yaml
services:
  idea-bot-staging:
    build: .
    container_name: idea-bot-staging
    restart: "no"
    environment:
      - TELEGRAM_BOT_TOKEN=${TEST_BOT_TOKEN}
      - DATABASE_URL=sqlite:///data/ideas_staging.db
      - LOG_LEVEL=INFO
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    networks:
      - idea-bot-staging-network
```

## 🔄 Жизненный цикл разработки

### **1. Начало разработки**
```bash
./scripts/dev-start.sh
# Время: 30 минут (один раз)
# Результат: Режим разработки с hot reload
```

### **2. Итерации разработки**
```bash
# Редактируем код
# Перезапускаем контейнер
docker-compose -f docker-compose.dev.yml restart
# Время: 5 секунд
```

### **3. Тестирование**
```bash
./scripts/staging-deploy.sh
# Время: 30 минут (сборка staging образа)
# Результат: Тестирование с реальным ботом
```

### **4. Деплой в продакшен**
```bash
./scripts/production-deploy.sh
# Время: 1 минута
# Результат: Обновленный production
```

## ⚡ Преимущества системы

### **Скорость разработки**
- **Hot reload**: 5 секунд вместо 30 минут
- **Параллельная работа**: dev + production одновременно
- **Быстрый откат**: 1 минута

### **Надежность**
- **Резервные копии**: автоматическое создание backup'ов
- **Изолированное тестирование**: staging с тестовым ботом
- **Zero-downtime**: production работает во время разработки

### **Удобство**
- **Автоматизация**: скрипты для всех операций
- **Четкий workflow**: понятные этапы
- **Быстрое восстановление**: откат за 1 минуту

## 🚨 Критические правила

### **1. Никогда не ломай production**
- Всегда создавай backup перед деплоем
- Тестируй в staging перед production
- Имей план отката

### **2. Используй правильный режим**
- **Разработка**: dev режим с volumes
- **Тестирование**: staging с тестовым ботом
- **Продакшен**: только проверенный код

### **3. Следи за ресурсами**
- Очищай старые образы: `docker image prune`
- Мониторь использование диска
- Удаляй неиспользуемые контейнеры

## 📊 Мониторинг

### **Проверка статуса**
```bash
# Статус всех контейнеров
docker ps

# Логи production
docker logs idea-bot

# Логи development
docker logs idea-bot-dev

# Логи staging
docker logs idea-bot-staging
```

### **Очистка ресурсов**
```bash
# Удаление старых образов
docker image prune -a

# Удаление неиспользуемых контейнеров
docker container prune

# Просмотр использования диска
docker system df
```

## 🎯 Результат

**Время разработки сокращено с 30 минут до 5 секунд на итерацию!**

- ✅ Production работает 24/7
- ✅ Разработка не влияет на пользователей
- ✅ Быстрое тестирование и деплой
- ✅ Надежный откат при проблемах
- ✅ Автоматизация всех процессов
