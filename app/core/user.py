import logging
from typing import Optional, Union

from fastapi import Depends, Request
from fastapi_users import (
    BaseUserManager, FastAPIUsers,
    IntegerIDMixin, InvalidPasswordException
)
from fastapi_users.authentication import (
    AuthenticationBackend, BearerTransport,
    JWTStrategy
)
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_async_session
from app.models.user import User
from app.schemas.user import UserCreate

# Ошибки вынес в константу
PASSWORD_TOO_SHORT_ERROR = (
    f"Пароль должен содержать минимум {settings.password_length} символа"
)
PASSWORD_SIMILAR_TO_EMAIL_ERROR = "Пароль не должен быть похож на email"


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    """
    Зависимость для получения
    SQLAlchemyUserDatabase для пользователей FastAPI
    """
    yield SQLAlchemyUserDatabase(session, User)


bearer_transport = BearerTransport(tokenUrl=settings.token_url)


def get_jwt_strategy() -> JWTStrategy:
    """Возвращает стратегию JWT для бэкэнда аутентификации"""
    return JWTStrategy(
        secret=settings.secret,
        lifetime_seconds=settings.token_lifetime
    )


auth_backend = AuthenticationBackend(
    name=settings.auth_backend_name,
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """
    Настраиваемый менеджер пользователей
    с проверкой пароля и ведением логов
    """
    async def validate_password(
        self,
        password: str,
        user: Union[UserCreate, User],
    ) -> None:
        """Проверка пароля на тупость"""
        if len(password) < settings.password_length:
            raise InvalidPasswordException(
                reason=PASSWORD_TOO_SHORT_ERROR
            )
        if user.email in password:
            raise InvalidPasswordException(
                reason=PASSWORD_SIMILAR_TO_EMAIL_ERROR
            )

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ):
        """Логирование"""
        logging.info(f"Пользователь {user.email} зарегистрирован.")


async def get_user_manager(user_db=Depends(get_user_db)):
    """
    Зависимость для получения
    UserManager для пользователей FastAPI
    """
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

current_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
