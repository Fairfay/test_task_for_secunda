from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.schemas.activity import (
    ActivityFlatRead, ActivityRead,
    ActivityCreate, ActivityUpdate
)
from app.crud.activity import activity_crud
from app.core.db import get_async_session
from app.models.activity import Activity
from app.api.utils import not_found, apply_patch

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("/", response_model=List[ActivityFlatRead])
async def get_activities(
    session: AsyncSession = Depends(get_async_session),
    limit: int = 100,
    offset: int = 0
):
    """Получение список всех видов деятельности с пагинацией."""
    result = await session.execute(
        select(Activity).offset(offset).limit(limit)
    )
    return result.scalars().all()


@router.post("/", response_model=ActivityRead)
async def create_activity(
    activity_in: ActivityCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Создание видов деятельности."""
    db_activity = await activity_crud.create(activity_in, session)
    result = await session.execute(
        select(Activity)
        .options(
            selectinload(Activity.children)
            .selectinload(Activity.children)
            .selectinload(Activity.children)
        )
        .where(Activity.id == db_activity.id)
    )
    activity_with_children = result.scalars().first()
    return activity_with_children


@router.get("/tree", response_model=List[ActivityRead])
async def get_activity_tree(
    session: AsyncSession = Depends(get_async_session),
    max_level: int = 3
):
    """Получиение дерево видов деятельности с возможностью указания глубины."""
    result = await session.execute(select(Activity))
    activities = result.scalars().all()
    return build_activity_tree(activities, max_level=max_level)


@router.get("/{activity_id}", response_model=ActivityRead)
async def get_activity(
    activity_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(
        select(Activity)
        .options(
            selectinload(Activity.children)
            .selectinload(Activity.children)
            .selectinload(Activity.children)
        )
        .where(Activity.id == activity_id)
    )
    activity = result.scalars().first()
    if not activity:
        not_found("Activity")
    return activity


@router.patch("/{activity_id}", response_model=ActivityRead)
async def update_activity(
    activity_id: int,
    activity_in: ActivityUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    db_activity = await activity_crud.get(activity_id, session)
    if not db_activity:
        not_found("Activity")

    # Self-reference запрет
    if activity_in.parent_id is not None and activity_in.parent_id == activity_id:
        raise HTTPException(status_code=400, detail="Нельзя сделать элемент своим же родителем.")

    apply_patch(db_activity, activity_in)
    await session.commit()
    await session.refresh(db_activity)
    result = await session.execute(
        select(Activity)
        .options(
            selectinload(Activity.children)
            .selectinload(Activity.children)
            .selectinload(Activity.children)
        )
        .where(Activity.id == db_activity.id)
    )
    activity_with_children = result.scalars().first()
    return activity_with_children


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление вид деятельности по ID."""
    db_activity = await activity_crud.get(activity_id, session)
    if not db_activity:
        not_found("Activity")
    await session.delete(db_activity)
    await session.commit()
    return {"ok": True}


def build_activity_tree(activities, max_level=3):
    """
    Оптимизированное построение дерева за O(n) с использованием словаря
    (о боги храни яндекс алгоритмы).
    """
    activity_map = {}
    for act in activities:
        activity_map.setdefault(act.parent_id, []).append(act)

    def build_nodes(parent_id=None, level=1):
        if level > max_level:
            return []

        return [
            ActivityRead(
                id=act.id,
                name=act.name,
                parent_id=act.parent_id,
                level=act.level,
                children=build_nodes(act.id, level + 1)
            ) for act in activity_map.get(parent_id, [])
        ]

    return build_nodes()
