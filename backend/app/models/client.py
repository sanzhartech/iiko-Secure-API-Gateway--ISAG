import uuid
from datetime import datetime

from sqlalchemy import Boolean, JSON, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class GatewayClient(Base):
    """
    SQLAlchemy model representing a client application utilizing this API Gateway.
    Secrets are stored strongly hashed following Zero-Trust.
    """
    __tablename__ = "gateway_clients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    hashed_secret: Mapped[str] = mapped_column(String(512), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    rate_limit: Mapped[int] = mapped_column(default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
