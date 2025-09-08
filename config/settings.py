import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Settings(BaseSettings):
    """Настройки приложения."""
    
    # Telegram Bot
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    
    # AI Services
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ollama_base_url: str = Field("http://localhost:11434", env="OLLAMA_BASE_URL")
    
    # Database
    database_url: str = Field("sqlite:///ideas.db", env="DATABASE_URL")
    
    # Logging
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_file: str = Field("logs/idea_bot.log", env="LOG_FILE")
    
    # Scheduler
    digest_time: str = Field("08:00", env="DIGEST_TIME")
    timezone: str = Field("Europe/Moscow", env="TIMEZONE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore" 
        
# Глобальный экземпляр настроек
settings = Settings()
