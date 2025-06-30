from typing import Generic, List, Optional, Type, TypeVar, Any, Dict

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import Base
from app.models import User


ModelType = TypeVar('ModelType', bound=Base)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
UpdateSchemaType = TypeVar('UpdateSchemaType', bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType]):
    """
    Базовый класс CRUD для моделей SQLAlchemy.
    Предоставляет базовые методы get, get_multi, create и update
    """

    def __init__(self, model: Type[ModelType]):
        """
        Объект CRUD с методами по умолчанию для создания,
        чтения, обновления (частичного) и списка.
        Аргументы:
        модель: класс модели SQLAlchemy
        """
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ) -> Optional[ModelType]:
        """Получение одного объекта по его идентификатору"""
        db_obj = await session.execute(
            select(self.model).where(
                self.model.id == obj_id
            )
        )
        return db_obj.scalars().first()

    async def get_multi(
        self,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Получите несколько объектов с пагинацией"""
        db_objs = await session.execute(
            select(self.model).offset(offset).limit(limit)
        )
        return db_objs.scalars().all()

    async def create(
        self,
        obj_in: CreateSchemaType,
        session: AsyncSession,
        user: Optional[User] = None
    ) -> ModelType:
        """Создайте новый объекта"""
        obj_in_data = obj_in.dict()
        if user is not None:
            obj_in_data['user_id'] = user.id
        db_obj = self.model(**obj_in_data)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(
            self,
            db_obj: ModelType,
            obj_in: UpdateSchemaType,
            session: AsyncSession,
    ) -> ModelType:
        update_data: Dict[str, Any] = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        session.add(db_obj)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj
