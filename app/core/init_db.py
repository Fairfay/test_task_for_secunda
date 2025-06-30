import contextlib
import logging
from typing import Any, Optional

from fastapi_users.exceptions import UserAlreadyExists
from pydantic import EmailStr
from sqlalchemy import select

from app.core.config import settings
from app.core.db import get_async_session
from app.core.user import get_user_db, get_user_manager
from app.schemas.user import UserCreate
from app.models.building import Building
from app.models.activity import Activity
from app.models.phone import Phone
from app.models.organization import (
    Organization, organization_phones,
    organization_activities
)


get_async_session_context = contextlib.asynccontextmanager(get_async_session)
get_user_db_context = contextlib.asynccontextmanager(get_user_db)
get_user_manager_context = contextlib.asynccontextmanager(get_user_manager)


def _get_or_create(
    session,
    model,
    filter_by: dict,
    defaults: Optional[dict] = None
) -> Any:
    """Универсальный get_or_create для моделей SQLAlchemy"""
    async def inner():
        result = await session.execute(select(model).filter_by(**filter_by))
        instance = result.scalars().first()
        if instance is None:
            params = {**filter_by}
            if defaults:
                params.update(defaults)
            instance = model(**params)
            session.add(instance)
            await session.flush()
        return instance
    return inner()


async def create_user(
    email: EmailStr,
    password: str,
    is_superuser: bool = False
):
    """Создание пользователя если его еще нет"""
    try:
        async with get_async_session_context() as session:
            async with get_user_db_context(session) as user_db:
                async with get_user_manager_context(user_db) as user_manager:
                    await user_manager.create(
                        UserCreate(
                            email=email,
                            password=password,
                            is_superuser=is_superuser
                        )
                    )
    except UserAlreadyExists:
        logging.info(f'Пользователь {email} уже зарегистрирован.')


async def create_first_superuser():
    """Создание первого админа если еще не создан"""
    if (settings.admin_email is not None and
            settings.admin_password is not None):
        await create_user(
            email=settings.admin_email,
            password=settings.admin_password,
            is_superuser=True,
        )


async def get_or_create_phone(session, number):
    """Получение или создание телефон по номеру"""
    return await _get_or_create(session, Phone, {"number": number})


async def get_or_create_building(session, address, latitude, longitude):
    """Получение или создание адреса"""
    return await _get_or_create(
        session, Building, {"address": address},
        {"latitude": latitude, "longitude": longitude}
    )


async def get_or_create_activity(session, name, parent=None, level=1):
    """Получение или создание активности"""
    return await _get_or_create(
        session, Activity, {"name": name},
        {"parent": parent, "level": level}
    )


async def get_or_create_organization(session, name, building_id):
    """Получение или создание организации"""
    return await _get_or_create(
        session, Organization,
        {"name": name, "building_id": building_id}
    )


async def fill_test_data():
    """Тестовые данные"""
    async with get_async_session_context() as session:
        b1 = await get_or_create_building(
            session,
            "г. Москва, ул. Ленина 1, офис 3", 55.7558, 37.6176
        )
        b2 = await get_or_create_building(
            session, "г. Новосибирск, ул. Блюхера 32/1",
            55.0415, 82.9346
        )

        a1 = await get_or_create_activity(session, "Еда", None, 1)
        a2 = await get_or_create_activity(session, "Мясная продукция", a1, 2)
        a3 = await get_or_create_activity(session, "Молочная продукция", a1, 2)
        a4 = await get_or_create_activity(session, "Автомобили", None, 1)
        a5 = await get_or_create_activity(session, "Грузовые", a4, 2)
        a6 = await get_or_create_activity(session, "Легковые", a4, 2)
        a7 = await get_or_create_activity(session, "Запчасти", a6, 3)
        a8 = await get_or_create_activity(session, "Аксессуары", a6, 3)

        p1 = await get_or_create_phone(session, "2-222-222")
        p2 = await get_or_create_phone(session, "3-333-333")
        p3 = await get_or_create_phone(session, "8-923-666-13-13")

        org1 = await get_or_create_organization(
            session, "ООО Рога и Копыта",
            b2.id
        )
        org2 = await get_or_create_organization(
            session, "ООО Молоко",
        b1.id)

        async def _m2m_exists(table, org_id, obj_id, obj_col):
            result = await session.execute(
                select(table).where(
                    (table.c.organization_id == org_id)
                    & (table.c[obj_col] == obj_id)
                )
            )
            return result.first() is not None

        for org, phone in [(org1, p1), (org1, p2), (org1, p3), (org2, p2)]:
            if not await _m2m_exists(
                organization_phones, org.id,
                phone.id, 'phone_id'
            ):
                await session.execute(organization_phones.insert().values(
                    {"organization_id": org.id, "phone_id": phone.id}
                ))

        for org, act in [(org1, a2), (org1, a1), (org2, a3)]:
            if not await _m2m_exists(
                organization_activities, org.id,
                act.id, 'activity_id'
            ):
                await session.execute(organization_activities.insert().values(
                    {"organization_id": org.id, "activity_id": act.id}
                ))

        await session.commit()
