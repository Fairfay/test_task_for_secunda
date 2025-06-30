from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.organization import Organization
from app.crud.base import CRUDBase
from app.core.init_db import get_or_create_phone
from app.crud.activity import activity_crud
from app.schemas.organization import OrganizationUpdate


class OrganizationCRUD(CRUDBase):
    """
    Операции CRUD для модели организации,
    включая логику обновления для полей M2M
    """
    def __init__(self):
        super().__init__(Organization)

    async def _update_phones(
        self,
        db_obj: Organization,
        phone_numbers: Optional[list],
        session: AsyncSession
    ):
        db_obj.phones = []
        if phone_numbers is not None:
            for number in phone_numbers:
                phone = await get_or_create_phone(session, number)
                db_obj.phones.append(phone)

    async def _update_activities(
        self,
        db_obj: Organization,
        activity_ids: Optional[list],
        session: AsyncSession
    ):
        db_obj.activities = []
        if activity_ids is not None:
            for activity_id in activity_ids:
                activity = await activity_crud.get(activity_id, session)
                if activity:
                    db_obj.activities.append(activity)

    async def update(
        self,
        db_obj: Organization,
        obj_in: OrganizationUpdate,
        session: AsyncSession,
    ) -> Organization:
        if obj_in.phone_numbers is not None:
            await self._update_phones(db_obj, obj_in.phone_numbers, session)
        if obj_in.activity_ids is not None:
            await self._update_activities(db_obj, obj_in.activity_ids, session)
        for field, value in obj_in.dict(
            exclude_unset=True,
            exclude={"phone_numbers", "activity_ids"}
        ).items():
            setattr(db_obj, field, value)
        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def create(
        self,
        obj_in,
        session: AsyncSession,
        user=None
    ):
        obj_in_data = obj_in.dict(exclude={"phone_numbers", "activity_ids"})
        db_obj = self.model(**obj_in_data, phones=[], activities=[])
        session.add(db_obj)

        # Добавляем телефоны, если есть
        if hasattr(obj_in, "phone_numbers") and obj_in.phone_numbers:
            for number in obj_in.phone_numbers:
                phone = await get_or_create_phone(session, number)
                db_obj.phones.append(phone)
        if hasattr(obj_in, "activity_ids") and obj_in.activity_ids:
            for activity_id in obj_in.activity_ids:
                activity = await activity_crud.get(activity_id, session)
                if activity:
                    db_obj.activities.append(activity)

        await session.commit()
        await session.refresh(db_obj)
        result = await session.execute(
            select(Organization)
            .options(
                selectinload(Organization.building),
                selectinload(Organization.phones),
                selectinload(Organization.activities),
            )
            .where(Organization.id == db_obj.id)
        )
        org_with_relations = result.scalars().first()
        return org_with_relations


organization_crud = OrganizationCRUD()
