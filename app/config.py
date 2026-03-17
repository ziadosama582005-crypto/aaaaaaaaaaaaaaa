"""
إعدادات التطبيق - يتم تحميل المتغيرات من البيئة
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # --- Firebase (Base64 لـ Render) ---
    FIREBASE_CONFIG_BASE64: str = ""
    FIREBASE_CONFIG_PATH: str = "serviceAccountKey.json"

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

    # --- SMTP (إرسال الإيميلات) ---
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_SERVER: str = "mail.privateemail.com"
    SMTP_PORT: int = 465
    SMTP_FROM_NAME: str = "TR Store"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
