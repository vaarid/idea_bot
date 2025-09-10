#!/bin/bash

echo "🚀 РАЗВЕРТЫВАНИЕ ОБНОВЛЕНИЙ IDEA BOT"
echo "===================================="

# Проверяем, что тестирование прошло успешно
read -p "✅ Тестирование прошло успешно? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Отменяем развертывание"
    exit 1
fi

echo "🛑 Останавливаем тестовый бот..."
docker-compose -f docker-compose.test.yml down

echo "🛑 Останавливаем рабочий бот..."
docker-compose down

echo "💾 Создаем резервную копию рабочей базы..."
cp data/idea_bot.db "backup/idea_bot_$(date +%Y%m%d_%H%M%S).db"

echo "🗄️  Выполняем миграцию рабочей базы..."
docker-compose run --rm idea-bot python migrate_tasks.py

echo "🚀 Запускаем обновленный рабочий бот..."
docker-compose up -d

echo ""
echo "✅ ОБНОВЛЕНИЯ РАЗВЕРНУТЫ!"
echo ""
echo "📋 Команды для мониторинга:"
echo "   Просмотр логов:    docker-compose logs -f"
echo "   Статус:            docker-compose ps"
echo "   Остановка:         docker-compose down"
echo ""
echo "🎉 Бот обновлен и готов к работе!"
