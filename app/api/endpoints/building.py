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

router = APIRouter(prefix="/buildings", tags=["buildings"])


@router.get("/", response_model=List[BuildingRead])
async def get_buildings(
    session: AsyncSession = Depends(get_async_session)
):
    """Получение списка всех зданий."""
    return await building_crud.get_multi(session)


@router.post("/", response_model=BuildingRead)
async def create_building(
    building_in: BuildingCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Создание зданий."""
    return await building_crud.create(building_in, session)


@router.get("/{building_id}", response_model=BuildingRead)
async def get_building(
    building_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение здание по ID."""
    return await get_object_or_404(
        building_crud, building_id,
        session, "Building"
    )


@router.patch("/{building_id}", response_model=BuildingRead)
async def update_building(
    building_id: int,
    building_in: BuildingUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Обновление зданий"""
    db_building = await get_object_or_404(
        building_crud, building_id,
        session, "Building"
    )
    apply_patch(db_building, building_in)
    await session.commit()
    await session.refresh(db_building)
    return db_building


@router.delete("/{building_id}")
async def delete_building(
    building_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление здания по ID (только если нет связанных организаций)."""
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