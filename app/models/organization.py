from sqlalchemy import Column, String, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from app.core.db import Base

organization_phones = Table(
    'organization_phones',
    Base.metadata,
    Column(
        'organization_id', Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True
    ),
    Column(
        'phone_id', Integer,
        ForeignKey('phones.id', ondelete='CASCADE'), primary_key=True
    ),
    comment="Связь многие-ко-многим между организациями и номерами"
)

organization_activities = Table(
    'organization_activities',
    Base.metadata,
    Column(
        'organization_id', Integer,
        ForeignKey('organizations.id', ondelete='CASCADE'), primary_key=True
    ),
    Column(
        'activity_id', Integer,
        ForeignKey('activities.id', ondelete='CASCADE'), primary_key=True
    ),
    comment="Связь многие-ко-многим между организациями и видами деятельности"
)


class Organization(Base):
    """
    Организация: связывает здание, номера и виды деятельности.
    """
    __tablename__ = 'organizations'
    name = Column(
        String, nullable=False,
        index=True
    )
    building_id = Column(
        Integer, ForeignKey('buildings.id', ondelete='CASCADE'),
        nullable=False
    )
    building = relationship(
        'Building', back_populates='organizations'
    )
    phones = relationship(
        'Phone', secondary=organization_phones,
        back_populates='organizations'
    )
    activities = relationship(
        'Activity', secondary=organization_activities,
        back_populates='organizations'
    )
