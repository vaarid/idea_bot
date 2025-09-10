#!/bin/bash

echo "🧪 Запуск тестовой миграции в Docker..."

# Останавливаем тестовый контейнер если он запущен
docker-compose -f docker-compose.test.yml down

# Собираем образ заново с изменениями
docker-compose -f docker-compose.test.yml build

# Запускаем миграцию в контейнере
echo "📦 Выполняем миграцию в контейнере..."
docker-compose -f docker-compose.test.yml run --rm idea-bot-test python migrate_tasks.py

echo "✅ Миграция завершена!"
echo "🚀 Запускаем тестовый бот..."
docker-compose -f docker-compose.test.yml up -d

echo "📋 Для просмотра логов: docker-compose -f docker-compose.test.yml logs -f"
echo "🛑 Для остановки: docker-compose -f docker-compose.test.yml down"
