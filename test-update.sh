#!/bin/bash

echo "🧪 ТЕСТИРОВАНИЕ ОБНОВЛЕНИЙ IDEA BOT"
echo "=================================="

# Проверяем, что рабочий бот не запущен
if docker ps | grep -q "idea-bot"; then
    echo "⚠️  ВНИМАНИЕ: Рабочий бот запущен!"
    echo "   Остановите его командой: docker-compose down"
    read -p "   Продолжить тестирование? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Собираем тестовый образ с обновлениями..."
docker-compose -f docker-compose.test.yml build

echo "🗄️  Выполняем миграцию базы данных..."
docker-compose -f docker-compose.test.yml run --rm idea-bot-test python migrate_tasks.py

echo "🚀 Запускаем тестовый бот..."
docker-compose -f docker-compose.test.yml up -d

echo ""
echo "✅ ТЕСТОВЫЙ БОТ ЗАПУЩЕН!"
echo ""
echo "📋 Команды для управления:"
echo "   Просмотр логов:    docker-compose -f docker-compose.test.yml logs -f"
echo "   Остановка:         docker-compose -f docker-compose.test.yml down"
echo "   Перезапуск:        docker-compose -f docker-compose.test.yml restart"
echo ""
echo "🧪 Протестируйте функционал:"
echo "   1. Отправьте текстовое сообщение боту"
echo "   2. Проверьте выбор 'идея' или 'задача'"
echo "   3. Проверьте кнопки 'Мои задачи'"
echo "   4. Проверьте статистику"
echo "   5. Проверьте отметку о выполнении"
echo ""
echo "💡 После тестирования нажмите Ctrl+C для остановки логов"
