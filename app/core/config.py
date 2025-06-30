from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import EmailStr


class Settings(BaseSettings):
    """
    Конфигурация приложения с использованием Pydantic BaseSettings.
    Все поля можно переопределить с помощью переменных среды или файла .env.
    По умолчанию поля уже указаны
    """
    app_title: str = 'Справочник'
    app_description: str = 'Справочник для Организаций и их деятельности'
    database_url: str = 'sqlite+aiosqlite:///./fastapi.db'
    postgres_user: str = 'admin'
    postgres_password: str = 'admin123'
    postgres_db: str = 'mydatabase'
    secret: str = 'SECRET'
    token_lifetime: int = 3600
    token_url: str = 'auth/jwt/login'
    api_key: str = 'secret-many-many-very-very-key-for-api'
    auth_backend_name: str = 'jwt'
    password_length: int = 3
    admin_email: Optional[EmailStr] = None
    admin_password: Optional[str] = None

    class Config:
        env_file = '.env'


settings = Settings()
