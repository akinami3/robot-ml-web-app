from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import UUID

from app.infrastructure.database.session import Base as DeclarativeBase


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class BaseModel(DeclarativeBase):
    __abstract__ = True
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    created_by = Column(String(length=64), nullable=True)
    updated_by = Column(String(length=64), nullable=True)


Base = DeclarativeBase
