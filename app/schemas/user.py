from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate


class UserRead(BaseUser[int]):
    """
    Схема для чтения пользователя.
    """
    pass


class UserCreate(BaseUserCreate):
    """
    Схема для создания пользователя.
    """
    pass


class UserUpdate(BaseUserUpdate):
    """
    Схема для обновления пользователя.
    """
    pass
