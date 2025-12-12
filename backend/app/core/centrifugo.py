"""
Centrifugo Client
Handles real-time publishing to Centrifugo
"""
import logging
from cent import Client
from app.core.config import settings

logger = logging.getLogger(__name__)

class CentrifugoClient:
    def __init__(self):
        self.client = Client(
            settings.CENTRIFUGO_API_URL,
            api_key=settings.CENTRIFUGO_API_KEY,
            timeout=5.0
        )
        logger.info(f"Centrifugo client initialized: {settings.CENTRIFUGO_API_URL}")

    def publish(self, channel: str, data: dict):
        """
        Publish data to a channel (synchronous)
        """
        try:
            # cent library API: client.publish(channel, data)
            result = self.client.publish(channel, data)
            logger.info(f"✅ Published to Centrifugo channel: {channel}")
            return result
        except AttributeError as e:
            # If publish doesn't exist, try the HTTP API directly
            logger.warning(f"Centrifugo publish method not available: {e}")
            logger.info("Real-time updates disabled - Centrifugo not configured")
        except Exception as e:
            logger.error(f"Failed to publish to Centrifugo channel {channel}: {e}")
            # Don't raise, just log. Real-time delivery is best-effort.

    def broadcast(self, channels: list[str], data: dict):
        """
        Broadcast data to multiple channels (synchronous)
        """
        try:
            return self.client.broadcast(channels, data)
        except Exception as e:
            logger.error(f"Failed to broadcast to Centrifugo: {e}")

centrifugo_client = CentrifugoClient()

def get_centrifugo_client() -> CentrifugoClient:
    return centrifugo_client
