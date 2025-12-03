"""
Test script for backend services
Verifies that all new services can be initialized and mocked correctly
"""
import asyncio
import logging
from unittest.mock import MagicMock, patch
import sys
import os

# Add backend directory to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_services():
    logger.info("🧪 Starting backend service tests...")
    
    # 1. Test Kubernetes Service
    logger.info("Testing Kubernetes Service...")
    with patch("kubernetes.config.load_kube_config"), \
         patch("kubernetes.client.CoreV1Api"), \
         patch("kubernetes.client.CustomObjectsApi"):
        
        from app.services.kubernetes_service import get_kubernetes_service
        k8s = get_kubernetes_service()
        
        # Test namespace creation
        await k8s.create_customer_namespace("test-customer")
        logger.info("✅ Kubernetes Service: Namespace creation test passed")
        
        # Test agent deployment
        await k8s.deploy_agent("test-ns", "test-agent", {})
        logger.info("✅ Kubernetes Service: Agent deployment test passed")

    # 2. Test Agent Gateway Service
    logger.info("Testing Agent Gateway Service...")
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "response": {"message": "ok"}}
        
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        from app.services.agent_gateway_service import get_agent_gateway_service
        gateway = get_agent_gateway_service()
        
        # Test agent invocation
        await gateway.invoke_agent("test-ns", "test-agent", {}, "test-customer")
        logger.info("✅ Agent Gateway Service: Agent invocation test passed")

    # 3. Test Redis Queue Service
    logger.info("Testing Redis Queue Service...")
    with patch("redis.asyncio.from_url") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis.return_value = mock_redis_client
        
        from app.services.redis_queue_service import get_redis_queue_service
        redis_service = await get_redis_queue_service()
        
        # Test enqueue
        await redis_service.enqueue_task("task-1", "cust-1", {}, "high")
        logger.info("✅ Redis Queue Service: Task enqueue test passed")

    logger.info("🎉 All backend service tests passed!")

if __name__ == "__main__":
    asyncio.run(test_services())
