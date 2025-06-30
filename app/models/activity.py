from sqlalchemy import Column, String, Integer, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from app.core.db import Base


class Activity(Base):
    """
    Вид деятельности: поддерживает иерархию (parent/children)
    и связь с организациями.
    """
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    name = Column(
        String, nullable=False
    )
    parent_id = Column(
        Integer, ForeignKey('activities.id'),
        nullable=True, index=True
    )
    level = Column(Integer, nullable=False, default=1)
    parent = relationship(
        'Activity', remote_side='Activity.id',
        backref='children'
    )
    organizations = relationship(
        'Organization', secondary='organization_activities',
        back_populates='activities'
    )
    __table_args__ = (
        CheckConstraint(
            'parent_id IS NULL OR parent_id != id',
            name='check_self_reference'
        ),
    )
