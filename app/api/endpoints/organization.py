from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, union_all, literal 
from sqlalchemy.orm import aliased
from pydantic import BaseModel, Field

from app.schemas.organization import (
    OrganizationRead, OrganizationCreate,
    OrganizationUpdate
)
from app.crud.organization import organization_crud
from app.core.db import get_async_session
from app.models.organization import Organization, organization_activities
from app.models.activity import Activity
from app.models.building import Building
from app.api.utils import org_with_all_options, get_object_or_404

router = APIRouter(prefix="/organizations", tags=["organizations"])


class LocationQuery(BaseModel):
    lat: float = Field(..., description="Широта центра")
    lon: float = Field(..., description="Долгота центра")
    radius: float | None = Field(None, description="Радиус поиска")
    min_lat: float | None = None
    max_lat: float | None = None
    min_lon: float | None = None
    max_lon: float | None = None


async def get_organizations_by_filter(
    session: AsyncSession,
    where,
    limit: int = 100,
    offset: int = 0
):
    result = await session.execute(
        org_with_all_options(
            select(Organization).where(where).offset(offset).limit(limit)
        )
    )
    return result.scalars().all()


async def get_activity_descendants(
    activity_id: int,
    session: AsyncSession,
    max_level: int = 3
):
    """
    Получение id всех потомков activity (включая сам activity_id)
    до max_level уровней через рекурсивный CTE.
    """
    activity_alias = aliased(Activity)
    cte = select(
        Activity.id,
        Activity.parent_id,
        literal(1).label("level")
    ).where(Activity.id == activity_id)
    cte = cte.cte(name="activity_cte", recursive=True)
    cte_alias = aliased(cte)
    cte = cte.union_all(
        select(
            activity_alias.id,
            activity_alias.parent_id,
            (cte_alias.c.level + 1).label("level")
        ).where(
            activity_alias.parent_id == cte_alias.c.id,
            cte_alias.c.level < max_level
        )
    )
    result = await session.execute(select(cte.c.id).distinct())
    return list(result.scalars())


async def _get_by_activity_id(
    activity_id: int,
    session: AsyncSession,
    limit: int,
    offset: int,
    tree: bool = False
):
    if tree:
        ids = await get_activity_descendants(activity_id, session)
    else:
        ids = [activity_id]
    where = organization_activities.c.activity_id.in_(ids)
    result = await session.execute(
        org_with_all_options(
            select(Organization).join(organization_activities).where(where)
            .offset(offset).limit(limit)
        )
    )
    return result.scalars().all()


@router.get("/by_activity/{activity_id}", response_model=List[OrganizationRead])
async def get_organizations_by_activity(
    activity_id: int,
    tree: bool = False,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получение организации по виду деятельности
    (с/без учета вложенности).
    """
    if tree:
        ids = await get_activity_descendants(activity_id, session)
    else:
        ids = [activity_id]

    where = organization_activities.c.activity_id.in_(ids)
    result = await session.execute(
        org_with_all_options(
            select(Organization).join(organization_activities).where(where)
            .offset(offset).limit(limit)
        )
    )
    return result.scalars().all()


@router.post("/", response_model=OrganizationRead)
async def create_organization(
    organization_in: OrganizationCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Создание организации."""
    return await organization_crud.create(organization_in, session)


@router.patch("/{organization_id}", response_model=OrganizationRead)
async def update_organization(
    organization_id: int,
    organization_in: OrganizationUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Частичное обновление организации."""
    db_organization = await get_object_or_404(
        organization_crud, organization_id,
        session, "Organization"
    )
    updated = await organization_crud.update(
        db_organization, organization_in,
        session
    )
    return updated


@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """Удаление организации по ID."""
    db_organization = await get_object_or_404(
        organization_crud, organization_id,
        session, "Organization"
    )
    await session.delete(db_organization)
    await session.commit()
    return {"ok": True}


@router.get(
    "/by_building/{building_id}",
    response_model=List[OrganizationRead]
)
async def get_organizations_by_building(
    building_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """Получение организации по зданию."""
    where = Organization.building_id == building_id
    return await get_organizations_by_filter(session, where, limit, offset)


@router.get("/by_location", response_model=List[OrganizationRead])
async def get_organizations_by_location(
    params: LocationQuery = Depends(),
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """Получение организации по координатам (радиус или прямоугольник)."""
    query = select(Organization).join(Building)
    if params.radius is not None:
        query = query.where(
            ((Building.latitude - params.lat) ** 2 + (
                Building.longitude - params.lon
            ) ** 2) <= (params.radius ** 2)
        )
    elif None not in (
        params.min_lat, params.max_lat,
        params.min_lon, params.max_lon
    ):
        query = query.where(
            and_(
                Building.latitude >= params.min_lat,
                Building.latitude <= params.max_lat,
                Building.longitude >= params.min_lon,
                Building.longitude <= params.max_lon,
            )
        )
    else:
        raise HTTPException(
            status_code=400, detail="Укажите радиус или ограничение"
        )
    result = await session.execute(
        org_with_all_options(query.offset(offset).limit(limit))
    )
    return result.scalars().all()


@router.get("/search", response_model=List[OrganizationRead])
async def search_organizations(
    name: str,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """Поиск организаций по названию с пагинацией."""
    where = Organization.name.ilike(f"%{name}%")
    return await get_organizations_by_filter(session, where, limit, offset)


@router.get(
    "/by_activity_tree/{activity_id}",
    response_model=List[OrganizationRead]
)
async def get_organizations_by_activity_tree(
    activity_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Получение организации по виду деятельности
    с учетом вложенности (до 3 уровней).
    """
    return await _get_by_activity_id(
        activity_id, session,
        limit, offset,
        tree=True
    )
