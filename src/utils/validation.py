"""
Модуль валидации и безопасности.
"""
import re
from typing import Optional
from src.utils.logger import logger

class ValidationError(Exception):
    """Исключение для ошибок валидации."""
    pass

class SecurityValidator:
    """Класс для валидации и проверки безопасности."""
    
    # Максимальная длина сообщения
    MAX_MESSAGE_LENGTH = 4000
    
    # Запрещенные паттерны
    FORBIDDEN_PATTERNS = [
        r'<script.*?>.*?</script>',  # XSS
        r'javascript:',              # JavaScript injection
        r'data:text/html',          # Data URI injection
        r'vbscript:',               # VBScript injection
    ]
    
    # Спам-слова (можно расширить)
    SPAM_WORDS = [
        'реклама', 'спам', 'купить', 'продать', 'заработок',
        'криптовалюта', 'биткоин', 'инвестиции'
    ]
    
    @classmethod
    def validate_message_content(cls, content: str) -> bool:
        """
        Валидация содержания сообщения.
        
        Args:
            content: Текст сообщения
            
        Returns:
            bool: True если сообщение валидно
            
        Raises:
            ValidationError: Если сообщение не прошло валидацию
        """
        if not content or not content.strip():
            raise ValidationError("Сообщение не может быть пустым")
        
        # Проверка длины
        if len(content) > cls.MAX_MESSAGE_LENGTH:
            raise ValidationError(f"Сообщение слишком длинное (максимум {cls.MAX_MESSAGE_LENGTH} символов)")
        
        # Проверка на запрещенные паттерны
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Обнаружен запрещенный паттерн в сообщении: {pattern}")
                raise ValidationError("Сообщение содержит запрещенный контент")
        
        # Проверка на спам (базовая)
        content_lower = content.lower()
        spam_count = sum(1 for word in cls.SPAM_WORDS if word in content_lower)
        if spam_count > 2:  # Если больше 2 спам-слов
            logger.warning(f"Возможный спам в сообщении: {spam_count} спам-слов")
            raise ValidationError("Сообщение может содержать спам")
        
        return True
    
    @classmethod
    def validate_user_id(cls, user_id: int) -> bool:
        """
        Валидация ID пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если ID валиден
            
        Raises:
            ValidationError: Если ID невалиден
        """
        if not isinstance(user_id, int):
            raise ValidationError("ID пользователя должен быть числом")
        
        if user_id <= 0:
            raise ValidationError("ID пользователя должен быть положительным числом")
        
        # Telegram user IDs обычно в диапазоне 1-2^63-1
        if user_id > 2**63 - 1:
            raise ValidationError("ID пользователя слишком большой")
        
        return True
    
    @classmethod
    def validate_idea_id(cls, idea_id: int) -> bool:
        """
        Валидация ID идеи.
        
        Args:
            idea_id: ID идеи
            
        Returns:
            bool: True если ID валиден
            
        Raises:
            ValidationError: Если ID невалиден
        """
        if not isinstance(idea_id, int):
            raise ValidationError("ID идеи должен быть числом")
        
        if idea_id <= 0:
            raise ValidationError("ID идеи должен быть положительным числом")
        
        return True
    
    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """
        Очистка контента от потенциально опасных символов.
        
        Args:
            content: Исходный контент
            
        Returns:
            str: Очищенный контент
        """
        # Удаляем HTML теги
        content = re.sub(r'<[^>]+>', '', content)
        
        # Удаляем лишние пробелы
        content = re.sub(r'\s+', ' ', content).strip()
        
        return content

class RateLimiter:
    """Простой rate limiter для защиты от спама."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Инициализация rate limiter.
        
        Args:
            max_requests: Максимальное количество запросов
            time_window: Временное окно в секундах
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.user_requests = {}  # {user_id: [timestamps]}
    
    def is_allowed(self, user_id: int) -> bool:
        """
        Проверка, разрешен ли запрос от пользователя.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            bool: True если запрос разрешен
        """
        import time
        current_time = time.time()
        
        # Очищаем старые запросы
        if user_id in self.user_requests:
            self.user_requests[user_id] = [
                timestamp for timestamp in self.user_requests[user_id]
                if current_time - timestamp < self.time_window
            ]
        else:
            self.user_requests[user_id] = []
        
        # Проверяем лимит
        if len(self.user_requests[user_id]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return False
        
        # Добавляем текущий запрос
        self.user_requests[user_id].append(current_time)
        return True

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter(max_requests=15, time_window=60)  # 15 запросов в минуту
