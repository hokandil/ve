from typing import List, Dict, Any, Optional
import httpx
import logging

logger = logging.getLogger(__name__)

class AgentRegistryService:
    """
    Service to interact with the upstream Agent Registry.
    """
    
    def __init__(self):
        self.registry_url = "http://agentregistry:8080" # Mock URL
        
    async def list_artifacts(self) -> List[Dict[str, Any]]:
        """
        List all available artifacts (agents/tools) from the Registry.
        """
        try:
            async with httpx.AsyncClient() as client:
                # Mocking the call for now as we don't have a live registry
                # response = await client.get(f"{self.registry_url}/api/v1/artifacts")
                # response.raise_for_status()
                # return response.json()
                
                return self._get_mock_artifacts()
        except Exception as e:
            logger.error(f"Error fetching from Agent Registry: {e}")
            return self._get_mock_artifacts()

    def _get_mock_artifacts(self) -> List[Dict[str, Any]]:
        """Return mock artifacts simulating a curated registry"""
        return [
            {
                "id": "registry-agent-1",
                "name": "Legal Compliance Auditor",
                "description": "Analyzes contracts for compliance risks",
                "author": "LegalTech AI",
                "version": "2.1.0",
                "downloads": 1540,
                "capabilities": ["contract-analysis", "risk-assessment"],
                "tools": ["pdf-parser", "legal-db-search"]
            },
            {
                "id": "registry-agent-2",
                "name": "Kubernetes Troubleshooter",
                "description": "Diagnoses crashloopbackoff and other pod issues",
                "author": "K8s Experts",
                "version": "1.0.5",
                "downloads": 5200,
                "capabilities": ["log-analysis", "event-correlation"],
                "tools": ["kubectl", "prometheus-query"]
            },
            {
                "id": "registry-agent-3",
                "name": "Social Media Manager",
                "description": "Generates and schedules posts across platforms",
                "author": "MarketingGenius",
                "version": "3.0.1",
                "downloads": 8900,
                "capabilities": ["content-generation", "scheduling"],
                "tools": ["twitter-api", "linkedin-api", "image-gen"]
            }
        ]

agent_registry_service = AgentRegistryService()
