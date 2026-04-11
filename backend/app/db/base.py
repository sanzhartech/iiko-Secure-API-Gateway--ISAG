import uuid
from typing import Any

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy declarative models.
    """
    # Exclude internal properties from JSON schemas automatically and provide a nice representation
    def dict(self) -> dict[str, Any]:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
