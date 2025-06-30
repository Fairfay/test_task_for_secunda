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

router = APIRouter(prefix="/organizations", tags=["Организация"])


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


@router.get(
    "/by_activity/{activity_id}", response_model=List[OrganizationRead],
    summary="Получает организации по виду деятельности"
)
async def get_organizations_by_activity(
    activity_id: int,
    tree: bool = False,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получает список организаций, связанных с определенным видом деятельности.

    ## Параметры
    - **activity_id**: Идентификатор вида деятельности
    - **tree**: Флаг использования иерархии
    (True - с учетом вложенности, False - точное совпадение)
    - **limit**: Максимальное количество возвращаемых записей
    (по умолчанию 100)
    - **offset**: Смещение от начала списка (по умолчанию 0)

    ## Пример ответа
    ```json
    [
        {
            "id": 1,
            "name": "Пример организации",
            "building_id": 5,
            "activities": [
                {
                    "id": 1,
                    "name": "Основная деятельность"
                }
            ]
        }
    ]
    ```
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


@router.post(
    "/", response_model=OrganizationRead,
    summary="Создание новой организации"
)
async def create_organization(
    organization_in: OrganizationCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Создание новой организации в системе.

    ## Тело запроса
    - **name**: Название организации (обязательное поле)
    - **building_id**: Идентификатор здания, где находится организация
    (опционально)
    - **activities**: Список идентификаторов видов деятельности
    (массив из объектов ActivityBase)

    ## Возвращаемое значение
    Возвращает созданную организацию со всеми связанными данными.
    """
    return await organization_crud.create(organization_in, session)


@router.patch(
    "/{organization_id}", response_model=OrganizationRead,
    summary="Частично обновляет данные организации"
)
async def update_organization(
    organization_id: int,
    organization_in: OrganizationUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Частично обновляет информацию о существующей организации.

    ## Параметры
    - **organization_id**: Идентификатор обновляемой организации
    - **name**: Новое название организации (опционально)
    - **building_id**: Новый идентификатор здания (опционально)
    - **activities**: Новый список идентификаторов видов деятельности
    (опционально)

    ## Ошибки
    - **404**: Организация с указанным ID не найдена
    """
    db_organization = await get_object_or_404(
        organization_crud, organization_id,
        session, "Organization"
    )
    updated = await organization_crud.update(
        db_organization, organization_in,
        session
    )
    return updated


@router.delete(
    "/{organization_id}", summary="Удалить организацию по ID"
)
async def delete_organization(
    organization_id: int,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Удаляет организацию из системы.

    ## Параметры
    - **organization_id**: Идентификатор удаляемой организации

    ## Ошибки
    - **404**: Организация с указанным ID не найдена
    """
    db_organization = await get_object_or_404(
        organization_crud, organization_id,
        session, "Organization"
    )
    await session.delete(db_organization)
    await session.commit()
    return {"ok": True}


@router.get(
    "/by_building/{building_id}",
    response_model=List[OrganizationRead],
    summary="Получает организации по зданию"
)
async def get_organizations_by_building(
    building_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Получает список организаций, расположенных в определенном здании.

    ## Параметры
    - **building_id**: Идентификатор здания
    - **limit**: Максимальное количество возвращаемых записей
    (по умолчанию 100)
    - **offset**: Смещение от начала списка (по умолчанию 0)

    ## Пример ответа
    ```json
    [
        {
            "id": 1,
            "name": "Пример организации",
            "building_id": 5,
            "activities": [
                {
                    "id": 1,
                    "name": "Основная деятельность"
                }
            ]
        }
    ]
    ```
    """
    where = Organization.building_id == building_id
    return await get_organizations_by_filter(session, where, limit, offset)


@router.get(
    "/by_location",
    response_model=List[OrganizationRead],
    summary="Получает организации по координатам"
)
async def get_organizations_by_location(
    params: LocationQuery = Depends(),
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session),
):
    """
    Получает список организаций в заданной географической области.

    ## Параметры
    - **lat**: Широта центра поиска
    - **lon**: Долгота центра поиска
    - **radius**: Радиус поиска в градусах
    (если задан, игнорирует параметры min/max)
    - **min_lat/max_lat**: Минимальная и максимальная широта
    - **min_lon/max_lon**: Минимальная и максимальная долгота

    ## Ограничения
    - Должны быть заданы либо **radius**, либо все параметры min/max
    """
    query = select(Organization).join(Building)
    if params.radius is not None:
        query = query.where(
            ((Building.latitude - params.lat) *
             (Building.latitude - params.lat) +
             (Building.longitude - params.lon) *
             (Building.longitude - params.lon)) <=
            (params.radius * params.radius)
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


@router.get(
    "/search", response_model=List[OrganizationRead],
    summary="Поиск организаций по названию"
)
async def search_organizations(
    name: str,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Выполняет поиск организаций по части названия.

    ## Параметры
    - **name**: Строка для поиска в названиях организаций
    - **limit**: Максимальное количество возвращаемых записей
    (по умолчанию 100)
    - **offset**: Смещение от начала списка (по умолчанию 0)

    ## Пример
    Запрос `/organizations/search?name=медицина` вернет все организации,
    содержащие слово "медицина" в названии.
    """
    where = Organization.name.ilike(f"%{name}%")
    return await get_organizations_by_filter(session, where, limit, offset)


@router.get(
    "/by_activity_tree/{activity_id}",
    response_model=List[OrganizationRead],
    summary="Получает организации по дереву видов деятельности"
)
async def get_organizations_by_activity_tree(
    activity_id: int,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_async_session)
):
    """
    Получает организации по всему дереву видов деятельности
    начиная с указанного.

    ## Параметры
    - **activity_id**: Идентификатор корневого вида деятельности
    - **limit**: Максимальное количество возвращаемых записей
    (по умолчанию 100)
    - **offset**: Смещение от начала списка (по умолчанию 0)

    ## Примечание
    Поиск производится до 3 уровней вложенности в дереве видов деятельности.
    """
    return await _get_by_activity_id(
        activity_id, session,
        limit, offset,
        tree=True
    )
