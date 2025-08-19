from typing import Optional
import yaml
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = Field(default="sqlite:///./db.sqlite", env="DATABASE_URL")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", env="SECRET_KEY")
    
    # LLM APIs
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    ollama_host: str = Field(default="http://localhost:11434", env="OLLAMA_HOST")
    
    # WhatsApp Twilio
    twilio_account_sid: Optional[str] = Field(default=None, env="TWILIO_ACCOUNT_SID")
    twilio_auth_token: Optional[str] = Field(default=None, env="TWILIO_AUTH_TOKEN")
    twilio_whatsapp_from: Optional[str] = Field(default=None, env="TWILIO_WHATSAPP_FROM")
    
    # WhatsApp Cloud API
    whatsapp_token: Optional[str] = Field(default=None, env="WHATSAPP_TOKEN")
    phone_number_id: Optional[str] = Field(default=None, env="PHONE_NUMBER_ID")
    verify_token: Optional[str] = Field(default=None, env="VERIFY_TOKEN")
    
    # Telegram
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    
    # Debug
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_config() -> dict:
    """Load business configuration from config.yaml"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        config_path = Path("config_example.yaml")
    
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    
    # Default config if no file exists
    return {
        "business": {
            "name": "Mi Negocio",
            "timezone": "America/Mexico_City",
            "language": "es"
        },
        "ai": {
            "mode": "rag_only",
            "temperature": 0.2
        }
    }


settings = Settings()
config = load_config()