from sqlalchemy import Column, String, Float
from sqlalchemy.orm import relationship
from app.core.db import Base


class Building(Base):
    """
    Здание: содержит адрес, координаты и связанные организации.
    """
    __tablename__ = 'buildings'
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    organizations = relationship('Organization', back_populates='building')
