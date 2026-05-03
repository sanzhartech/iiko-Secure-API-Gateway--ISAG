from typing import Annotated
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.engine import get_db_session
from app.models.client import GatewayClient
from app.models.audit import AdminAuditLog
from app.schemas.admin import (
    ClientResponse,
    ClientCreateRequest,
    ClientCreateResponse,
    ClientStatusUpdateRequest,
    AdminStatsResponse,
    AuditLogResponse,
)
from app.core.hashing import get_password_hash
from app.schemas.token import TokenClaims
from app.security.jwt_validator import get_current_user_claims
from app.core.logging import get_logger

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)

# --- Dependency ---

def get_current_admin(claims: Annotated[TokenClaims, Depends(get_current_user_claims)]) -> TokenClaims:
    """
    Ensure the current authenticated user/client has the 'admin' role.
    """
    if "admin" not in claims.roles:
        logger.warning("admin_access_denied", sub=claims.sub, roles=claims.roles)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return claims

# --- Endpoints ---

@router.get("/clients", response_model=list[ClientResponse])
async def get_clients(
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> list[GatewayClient]:
    """List all registered GatewayClients."""
    result = await db.execute(select(GatewayClient))
    return list(result.scalars().all())


@router.post("/clients", response_model=ClientCreateResponse)
async def create_client(
    request: Request,
    body: ClientCreateRequest,
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> ClientCreateResponse:
    """Create a new client with a generated strong secret."""
    # Check if exists
    result = await db.execute(select(GatewayClient).where(GatewayClient.client_id == body.client_id))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Client ID already exists.")

    raw_secret = secrets.token_urlsafe(32)
    hashed_secret = get_password_hash(raw_secret)

    new_client = GatewayClient(
        client_id=body.client_id,
        hashed_secret=hashed_secret,
        roles=body.roles,
        scopes=body.scopes,
        rate_limit=body.rate_limit,
        is_active=True
    )
    db.add(new_client)

    # Audit Log
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    audit_log = AdminAuditLog(
        admin_id=admin.sub,
        action="CLIENT_CREATED",
        target_id=body.client_id,
        ip_address=client_ip
    )
    db.add(audit_log)

    await db.commit()

    logger.info("admin_created_client", admin=admin.sub, new_client_id=body.client_id)

    return ClientCreateResponse(
        client_id=body.client_id,
        client_secret=raw_secret,
        roles=body.roles,
        scopes=body.scopes,
        rate_limit=body.rate_limit
    )


@router.patch("/clients/{client_uuid}/status", response_model=ClientResponse)
async def update_client_status(
    request: Request,
    client_uuid: uuid.UUID,
    body: ClientStatusUpdateRequest,
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> GatewayClient:
    """Toggle client active/revoked status."""
    result = await db.execute(select(GatewayClient).where(GatewayClient.id == client_uuid))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    client.is_active = body.is_active

    # Audit Log
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    action = "CLIENT_ACTIVATED" if body.is_active else "CLIENT_REVOKED"
    audit_log = AdminAuditLog(
        admin_id=admin.sub,
        action=action,
        target_id=str(client_uuid),
        ip_address=client_ip
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(client)

    logger.info("admin_updated_client_status", admin=admin.sub, target_client=str(client_uuid), is_active=body.is_active)
    
    return client

@router.post("/clients/{client_uuid}/rotate-secret", response_model=ClientCreateResponse)
async def rotate_client_secret(
    request: Request,
    client_uuid: uuid.UUID,
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> ClientCreateResponse:
    """Rotate the client secret for a GatewayClient."""
    result = await db.execute(select(GatewayClient).where(GatewayClient.id == client_uuid))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    raw_secret = secrets.token_urlsafe(32)
    hashed_secret = get_password_hash(raw_secret)

    client.hashed_secret = hashed_secret

    # Audit Log
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    audit_log = AdminAuditLog(
        admin_id=admin.sub,
        action="SECRET_ROTATED",
        target_id=client.client_id,
        ip_address=client_ip
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(client)

    logger.info("admin_rotated_client_secret", admin=admin.sub, target_client=client.client_id)

    return ClientCreateResponse(
        client_id=client.client_id,
        client_secret=raw_secret,
        roles=client.roles,
        scopes=client.scopes,
        rate_limit=client.rate_limit
    )

@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    admin: Annotated[TokenClaims, Depends(get_current_admin)]
) -> AdminStatsResponse:
    """
    Parse Prometheus /metrics internally and return a JSON digest.
    (This is a simplified mock implementation for the Admin UI dashboard.
    In production, you would parse the prometheus_client text payload).
    """
    from prometheus_client import REGISTRY
    
    total_requests = 0
    blocked_requests = 0
    total_latency = 0.0
    latency_count = 0

    for metric in REGISTRY.collect():
        if metric.name == "isag_requests_total":
            for sample in metric.samples:
                total_requests += sample.value
        elif metric.name == "isag_blocked_requests_total":
            for sample in metric.samples:
                blocked_requests += sample.value
        elif metric.name == "isag_request_latency_seconds":
            for sample in metric.samples:
                if sample.name == "isag_request_latency_seconds_sum":
                    total_latency += sample.value
                elif sample.name == "isag_request_latency_seconds_count":
                    latency_count += sample.value

    error_rate = (blocked_requests / total_requests) if total_requests > 0 else 0.0
    avg_latency = (total_latency / latency_count) if latency_count > 0 else 0.0

    # Mock time series for the last 6 hours
    import datetime
    now = datetime.datetime.now()
    time_series = []
    base_requests = total_requests // 6 if total_requests > 0 else 100
    for i in range(5, -1, -1):
        dt = now - datetime.timedelta(hours=i)
        import random
        time_series.append({
            "time": dt.strftime("%H:00"),
            "requests": int(base_requests * random.uniform(0.5, 1.5))
        })

    # Fetch 5 recent events
    events_query = select(AdminAuditLog).order_by(AdminAuditLog.timestamp.desc()).limit(5)
    events_result = await db.execute(events_query)
    recent_events = list(events_result.scalars().all())

    return AdminStatsResponse(
        total_requests=int(total_requests),
        error_rate=round(error_rate, 4),
        avg_latency=round(avg_latency, 4),
        time_series=time_series,
        recent_events=recent_events
    )

@router.get("/logs", response_model=list[AuditLogResponse])
async def get_audit_logs(
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    limit: int = 50,
    offset: int = 0
) -> list[AdminAuditLog]:
    """Retrieve paginated audit logs."""
    query = select(AdminAuditLog).order_by(AdminAuditLog.timestamp.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())
