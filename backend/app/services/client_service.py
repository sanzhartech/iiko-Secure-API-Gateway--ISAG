from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import GatewayClient


async def get_client_by_id(db: AsyncSession, client_id: str) -> GatewayClient | None:
    """
    Retrieve an active GatewayClient strictly by its exact client_id.
    """
    stmt = select(GatewayClient).where(GatewayClient.client_id == client_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
