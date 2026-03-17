"""
إعدادات التطبيق - يتم تحميل المتغيرات من البيئة
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- قاعدة البيانات ---
    DATABASE_URL: str = "sqlite:///./loyalty.db"

    # --- JWT ---
    SECRET_KEY: str = "change-me-in-production-use-a-strong-random-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 ساعة

    # --- Super Admin الافتراضي ---
    ADMIN_EMAIL: str = "admin@loyalty.com"
    ADMIN_PASSWORD: str = "admin123"

    # --- عام ---
    APP_NAME: str = "Loyalty Points System"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
