from fastapi import HTTPException
from sqlalchemy.orm import selectinload

from app.models.organization import Organization


def not_found(entity: str = "Object"):
    """Сообщение об ошибке не найдено"""
    raise HTTPException(status_code=404, detail=f"{entity} not found")


def apply_patch(db_obj, update_schema, exclude: set = None):
    """
    Частичное обновление к db_obj по данным из Pydantic-схемы.
    exclude: множество полей, которые не нужно обновлять (например, M2M).
    """
    exclude = exclude or set()
    for field, value in update_schema.dict(
        exclude_unset=True,
        exclude=exclude
    ).items():
        setattr(db_obj, field, value)


def org_with_all_options(query):
    """Добавляет selectinload для всех связей Organization."""
    return query.options(
        selectinload(Organization.building),
        selectinload(Organization.phones),
        selectinload(Organization.activities),
    )


async def get_object_or_404(crud, obj_id, session, entity="Object"):
    """
    Получение объекта по id или вызов 404.
    :param crud: CRUD-класс с методом get
    :param obj_id: идентификатор объекта
    :param session: сессия БД
    :param entity: имя сущности для сообщения об ошибке
    :return: объект или HTTPException 404
    """
    obj = await crud.get(obj_id, session)
    if not obj:
        not_found(entity)
    return obj
