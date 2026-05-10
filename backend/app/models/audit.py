import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class AdminAuditLog(Base):
    """
    SQLAlchemy model representing an action performed by an Administrator.
    """
    __tablename__ = "admin_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    admin_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=True)

class GatewayRequestLog(Base):
    """
    SQLAlchemy model representing an API request processed by the gateway.
    Used for historical statistics in the dashboard.
    """
    __tablename__ = "gateway_request_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    client_id: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[float] = mapped_column(nullable=False)
