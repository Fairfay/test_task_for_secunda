from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.schemas.building import BuildingRead, BuildingCreate, BuildingUpdate
from app.crud.building import building_crud
from app.core.db import get_async_session
from app.api.utils import apply_patch, get_object_or_404
from app.models.building import Building

router = APIRouter(prefix="/buildings", tags=["Здания"])


@router.get(
    "/",
    response_model=List[BuildingRead],
    tags=["Здания"],
    summary="Получает список зданий"
)
async def get_buildings(
    session: AsyncSession = Depends(get_async_session)
):
    """
    Возвращает список всех зданий в системе.

    **Ответ:**
    - Список объектов здания.
    """
    return await building_crud.get_multi(session)


@router.post(
    "/",
    response_model=BuildingRead,
    tags=["Здания"],
    summary="Создает здание"
)
async def create_building(
    building_in: BuildingCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Создаёт новое здание.

    **Параметры:**
    - building_in: данные для создания здания

    **Ответ:**
    - Объект созданного здания.
    """
    return await building_crud.create(building_in, session)


@router.get(
    "/{building_id}",
    response_model=BuildingRead,
    tags=["Здания"],
    summary="Получает здание по ID"
)
async def get_building(
    building_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Возвращает здание по его уникальному идентификатору.

    **Параметры:**
    - building_id: ID здания

    **Ответ:**
    - Объект здания.
    """
    return await get_object_or_404(
        building_crud, building_id,
        session, "Building"
    )


@router.patch(
    "/{building_id}",
    response_model=BuildingRead,
    tags=["Здания"],
    summary="Обновляет здание по ID"
)
async def update_building(
    building_id: int,
    building_in: BuildingUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Обновляет данные здания по его ID.

    **Параметры:**
    - building_id: ID здания
    - building_in: новые данные здания

    **Ответ:**
    - Обновлённый объект здания.
    """
    db_building = await get_object_or_404(
        building_crud, building_id,
        session, "Building"
    )
    apply_patch(db_building, building_in)
    await session.commit()
    await session.refresh(db_building)
    return db_building


@router.delete(
    "/{building_id}",
    tags=["Здания"],
    summary="Удаляет здание по ID"
)
async def delete_building(
    building_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удаляет здание по ID, если к нему не привязаны организации.

    **Параметры:**
    - building_id: ID здания

    **Ответ:**
    - ok: True, если удаление прошло успешно.
    """
    result = await session.execute(
        select(Building)
        .options(selectinload(Building.organizations))
        .where(Building.id == building_id)
    )
    db_building = result.scalars().first()

    if not db_building:
        raise HTTPException(status_code=404, detail="Building not found")

    if db_building.organizations:
        raise HTTPException(
            status_code=400,
            detail="Невозможно удалить здание: существуют связанные организации."
        )

    await session.delete(db_building)
    await session.commit()
    return {"ok": True}
