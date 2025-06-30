from typing import Optional

from pydantic import BaseModel, Field


class BuildingBase(BaseModel):
    """
    Базовая схема здания (для создания и обновления).
    """
    address: str = Field(..., example="г. Москва, ул. Ленина 1, офис 3")
    latitude: float = Field(..., example=55.7558)
    longitude: float = Field(..., example=37.6176)


class BuildingCreate(BuildingBase):
    """
    Схема для создания здания.
    """
    pass


class BuildingUpdate(BaseModel):
    """
    Схема для обновления здания (частичное обновление).
    """
    address: Optional[str] = Field(
        None, example="г. Москва, ул. Ленина 1, офис 3"
    )
    latitude: Optional[float] = Field(None, example=55.7558)
    longitude: Optional[float] = Field(None, example=37.6176)


class BuildingRead(BuildingBase):
    """
    Схема для чтения здания.
    """
    id: int

    class Config:
        from_attributes = True
