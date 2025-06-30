from typing import Optional, List

from pydantic import BaseModel, Field
from typing import TYPE_CHECKING


class ActivityBase(BaseModel):
    name: str = Field(..., example="Молочная продукция")
    parent_id: Optional[int] = Field(None, example=1)
    level: int = Field(..., example=2)


class ActivityCreate(ActivityBase):
    class Config:
        schema_extra = {
            "example": {
                "name": "Молочная продукция",
                "parent_id": None,
                "level": 1
            }
        }


class ActivityUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None


class ActivityRead(ActivityBase):
    id: int
    children: Optional[List['ActivityRead']] = None

    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Молочная продукция",
                "parent_id": None,
                "level": 1,
                "children": [
                    {
                        "id": 2,
                        "name": "Сыры",
                        "parent_id": 1,
                        "level": 2,
                        "children": []
                    }
                ]
            }
        }


if TYPE_CHECKING:
    ActivityRead.update_forward_refs()


class ActivityFlatRead(ActivityBase):
    id: int

    class Config:
        from_attributes = True
