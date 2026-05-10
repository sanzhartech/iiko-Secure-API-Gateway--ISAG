from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
import uuid

# --- Admin User Schemas ---

class AdminLoginRequest(BaseModel):
    username: str
    password: str

# --- Client Management Schemas ---

class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    client_id: str
    roles: list[str]
    scopes: list[str]
    rate_limit: int
    is_active: bool
    last_used_at: datetime | None = None

class ClientCreateRequest(BaseModel):
    client_id: str = Field(..., max_length=128)
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    rate_limit: int = Field(default=10, ge=1)

class ClientCreateResponse(BaseModel):
    client_id: str
    client_secret: str
    roles: list[str]
    scopes: list[str]
    rate_limit: int

class ClientStatusUpdateRequest(BaseModel):
    is_active: bool

class ClientRateLimitUpdateRequest(BaseModel):
    rate_limit: int = Field(..., ge=1)

# --- Kill Switch Schemas ---

class KillSwitchRequest(BaseModel):
    active: bool

class KillSwitchResponse(BaseModel):
    active: bool

# --- Stats Schemas ---

class TimeSeriesDataPoint(BaseModel):
    time: str
    requests: int

class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    timestamp: datetime
    admin_id: str
    action: str
    target_id: str
    ip_address: str | None

class AdminStatsResponse(BaseModel):
    total_requests: int
    error_rate: float
    avg_latency: float
    time_series: list[TimeSeriesDataPoint]
    recent_events: list[AuditLogResponse]
