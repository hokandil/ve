import asyncio
import logging
from app.services.gateway_config_service import get_gateway_config_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    service = get_gateway_config_service()
    
    logger.info("Creating route and default-deny policy for wellness agent...")
    result = service.create_agent_route("wellness")
    logger.info(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
