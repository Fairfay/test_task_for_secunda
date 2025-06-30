from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.building import BuildingRead
from app.schemas.activity import ActivityFlatRead
from app.schemas.phone import PhoneRead


class OrganizationBase(BaseModel):
    """
    Базовая схема организации (для создания и обновления).
    """
    name: str = Field(..., example="ООО Рога и Копыта")
    building_id: int = Field(..., example=1)
    phone_numbers: List[str] = Field(
        default_factory=list, example=["2-222-222", "3-333-333"]
    )
    activity_ids: List[int] = Field(default_factory=list, example=[1, 2])


class OrganizationCreate(OrganizationBase):
    """
    Схема для создания организации.
    """
    class Config:
        schema_extra = {
            "example": {
                "name": "ООО Рога и Копыта",
                "building_id": 1,
                "phone_numbers": ["2-222-222", "3-333-333"],
                "activity_ids": [1, 2]
            }
        }


class OrganizationUpdate(BaseModel):
    """
    Схема для обновления организации (частичное обновление).
    """
    name: Optional[str] = Field(None, example="ООО Рога и Копыта")
    building_id: Optional[int] = Field(None, example=1)
    phone_numbers: Optional[List[str]] = Field(
        None, example=["2-222-222", "3-333-333"]
    )
    activity_ids: Optional[List[int]] = Field(None, example=[1, 2])


class OrganizationRead(BaseModel):
    """
    Схема для чтения организации с вложенными сущностями.
    """
    id: int
    name: str
    building: BuildingRead
    phones: List[PhoneRead]
    activities: List[ActivityFlatRead]

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "ООО Рога и Копыта",
                "building": {
                    "id": 1,
                    "address": "г. Москва, ул. Ленина 1, офис 3",
                    "latitude": 55.7558,
                    "longitude": 37.6176
                },
                "phones": [
                    {"id": 1, "number": "2-222-222"},
                    {"id": 2, "number": "3-333-333"}
                ],
                "activities": [
                    {"id": 1, "name": "Молочная продукция", "parent_id": None, "level": 1},
                    {"id": 2, "name": "Хлебобулочные изделия", "parent_id": None, "level": 1}
                ]
            }
        }
