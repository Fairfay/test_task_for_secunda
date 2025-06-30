from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.core.db import Base


class Phone(Base):
    """
    Телефон: уникальный номер, связь с организациями.
    """
    __tablename__ = 'phones'
    number = Column(
        String, nullable=False,
        unique=True
    )
    organizations = relationship(
        'Organization', secondary='organization_phones',
        back_populates='phones'
    )
