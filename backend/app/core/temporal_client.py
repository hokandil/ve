"""
Temporal Client Factory
"""
from temporalio.client import Client
from app.core.config import settings

async def get_temporal_client() -> Client:
    """
    Connect to Temporal Server and return a client.
    """
    return await Client.connect(
        settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE,
    )
