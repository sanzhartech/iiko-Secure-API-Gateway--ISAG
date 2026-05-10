from typing import Annotated
import uuid
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.engine import get_db_session
from app.models.client import GatewayClient
from app.models.audit import AdminAuditLog, GatewayRequestLog
from app.schemas.admin import (
    ClientResponse,
    ClientCreateRequest,
    ClientCreateResponse,
    ClientStatusUpdateRequest,
    ClientRateLimitUpdateRequest,
    AdminStatsResponse,
    AuditLogResponse,
    KillSwitchRequest,
    KillSwitchResponse,
)
from app.core.hashing import get_password_hash
from app.core.network import get_client_ip  # [Sec-3] Centralized safe IP extraction
from app.core.config import Settings, get_settings
from app.core.redis import get_redis
import redis.asyncio as redis
from app.schemas.token import TokenClaims
from app.security.jwt_validator import get_current_claims
from app.core.logging import get_logger

router = APIRouter(prefix="/admin", tags=["Admin"])
logger = get_logger(__name__)

# --- Dependency ---

def get_current_admin(claims: Annotated[TokenClaims, Depends(get_current_claims)]) -> TokenClaims:
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
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

    # [Sec-3] Use centralized safe IP extraction — ignores X-Forwarded-For
    # unless the direct peer is in TRUSTED_PROXY_CIDRS.
    client_ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GatewayClient:
    """Toggle client active/revoked status."""
    result = await db.execute(select(GatewayClient).where(GatewayClient.id == client_uuid))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    client.is_active = body.is_active

    # [Sec-3] Safe IP extraction via centralized helper
    client_ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
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
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ClientCreateResponse:
    """Rotate the client secret for a GatewayClient."""
    result = await db.execute(select(GatewayClient).where(GatewayClient.id == client_uuid))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    raw_secret = secrets.token_urlsafe(32)
    hashed_secret = get_password_hash(raw_secret)

    client.hashed_secret = hashed_secret

    # [Sec-3] Safe IP extraction via centralized helper
    client_ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
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

@router.patch("/clients/{client_uuid}/rate-limit", response_model=ClientResponse)
async def update_client_rate_limit(
    request: Request,
    client_uuid: uuid.UUID,
    body: ClientRateLimitUpdateRequest,
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> GatewayClient:
    """Update client rate limit."""
    result = await db.execute(select(GatewayClient).where(GatewayClient.id == client_uuid))
    client = result.scalars().first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    client.rate_limit = body.rate_limit

    client_ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
    audit_log = AdminAuditLog(
        admin_id=admin.sub,
        action="RATE_LIMIT_UPDATED",
        target_id=str(client_uuid),
        ip_address=client_ip
    )
    db.add(audit_log)

    await db.commit()
    await db.refresh(client)

    logger.info("admin_updated_client_rate_limit", admin=admin.sub, target_client=str(client_uuid), rate_limit=body.rate_limit)
    
    return client

@router.get("/kill-switch", response_model=KillSwitchResponse)
async def get_kill_switch_status(
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
) -> KillSwitchResponse:
    """Get the current status of the global kill switch."""
    val = await redis_client.get("isag:global_block")
    return KillSwitchResponse(active=(val == "1"))

@router.post("/kill-switch", response_model=KillSwitchResponse)
async def set_kill_switch_status(
    request: Request,
    body: KillSwitchRequest,
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_settings)],
    redis_client: Annotated[redis.Redis, Depends(get_redis)]
) -> KillSwitchResponse:
    """Activate or deactivate the global kill switch."""
    if body.active:
        await redis_client.set("isag:global_block", "1")
    else:
        await redis_client.delete("isag:global_block")

    client_ip = get_client_ip(request, trusted_cidrs=settings.trusted_proxy_cidrs_list)
    audit_log = AdminAuditLog(
        admin_id=admin.sub,
        action="KILL_SWITCH_ACTIVATED" if body.active else "KILL_SWITCH_DEACTIVATED",
        target_id="SYSTEM",
        ip_address=client_ip
    )
    db.add(audit_log)
    await db.commit()

    logger.warning("admin_toggled_kill_switch", admin=admin.sub, active=body.active)
    
    return KillSwitchResponse(active=body.active)

@router.get("/stats", response_model=AdminStatsResponse)
async def get_stats(
    admin: Annotated[TokenClaims, Depends(get_current_admin)],
    db: Annotated[AsyncSession, Depends(get_db_session)]
) -> AdminStatsResponse:
    """
    Parse Prometheus /metrics internally and return a JSON digest.
    Also fetches real time-series data from the database.
    """
    from prometheus_client import REGISTRY
    from sqlalchemy import func
    import datetime
    
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

    # Fetch real time-series data from GatewayRequestLog for the last 6 hours
    now = datetime.datetime.now(datetime.timezone.utc)
    six_hours_ago = now - datetime.timedelta(hours=6)
    
    time_series = []
    
    try:
        # Group by hour and count requests
        query = select(
            func.strftime('%H:00', GatewayRequestLog.timestamp).label("hour"),
            func.count().label("requests")
        ).where(
            GatewayRequestLog.timestamp >= six_hours_ago
        ).group_by("hour").order_by("hour")
        
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Build dictionary for existing data
        db_data = {row.hour: row.requests for row in rows}
        
        # Ensure we have exactly 6 hours of data in order
        for i in range(5, -1, -1):
            dt = now - datetime.timedelta(hours=i)
            hour_str = dt.strftime("%H:00")
            time_series.append({
                "time": hour_str,
                "requests": db_data.get(hour_str, 0)
            })
    except Exception as e:
        logger.error("stats_timeseries_db_error", error=str(e))
        # Fallback to zero if db fails
        for i in range(5, -1, -1):
            dt = now - datetime.timedelta(hours=i)
            time_series.append({
                "time": dt.strftime("%H:00"),
                "requests": 0
            })

    # Fetch 5 recent events (with fallback)
    recent_events = []
    try:
        events_query = select(AdminAuditLog).order_by(AdminAuditLog.timestamp.desc()).limit(5)
        events_result = await db.execute(events_query)
        recent_events = list(events_result.scalars().all())
    except Exception as e:
        logger.error("stats_events_db_error", error=str(e))
        # Continue with empty events to avoid crashing the whole dashboard

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
