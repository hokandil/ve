"""
Circuit Breaker for Intelligent Delegation
Prevents infinite recursion and resource exhaustion
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio


class DelegationCircuitBreaker:
    """
    Circuit breaker to prevent runaway delegation.
    
    Tracks:
    - Delegation depth per workflow
    - Total delegations per customer
    - Delegation rate per agent type
    """
    
    def __init__(self):
        self.workflow_depths: Dict[str, int] = {}
        self.customer_counts: Dict[str, int] = {}
        self.agent_rates: Dict[str, list] = {}
        self.reset_time = datetime.now()
        
        # Thresholds
        self.MAX_DEPTH = 5
        self.MAX_CUSTOMER_DELEGATIONS = 100  # Per hour
        self.MAX_AGENT_RATE = 50  # Per agent per hour
        self.RESET_INTERVAL = timedelta(hours=1)
    
    async def check_and_record(
        self,
        workflow_id: str,
        customer_id: str,
        agent_type: str,
        delegation_depth: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if delegation should be allowed.
        
        Returns:
            (allowed: bool, reason: Optional[str])
        """
        # Reset counters if interval passed
        if datetime.now() - self.reset_time > self.RESET_INTERVAL:
            self._reset_counters()
        
        # Check 1: Depth limit
        if delegation_depth > self.MAX_DEPTH:
            return False, f"Max delegation depth ({self.MAX_DEPTH}) exceeded"
        
        # Check 2: Customer delegation limit
        customer_count = self.customer_counts.get(customer_id, 0)
        if customer_count >= self.MAX_CUSTOMER_DELEGATIONS:
            return False, f"Customer delegation limit ({self.MAX_CUSTOMER_DELEGATIONS}/hour) exceeded"
        
        # Check 3: Agent rate limit
        agent_delegations = self.agent_rates.get(agent_type, [])
        recent_delegations = [
            ts for ts in agent_delegations
            if datetime.now() - ts < self.RESET_INTERVAL
        ]
        if len(recent_delegations) >= self.MAX_AGENT_RATE:
            return False, f"Agent rate limit ({self.MAX_AGENT_RATE}/hour) exceeded for {agent_type}"
        
        # Record delegation
        self.workflow_depths[workflow_id] = delegation_depth
        self.customer_counts[customer_id] = customer_count + 1
        
        if agent_type not in self.agent_rates:
            self.agent_rates[agent_type] = []
        self.agent_rates[agent_type].append(datetime.now())
        
        return True, None
    
    def _reset_counters(self):
        """Reset all counters"""
        self.workflow_depths.clear()
        self.customer_counts.clear()
        self.agent_rates.clear()
        self.reset_time = datetime.now()
    
    def get_stats(self) -> Dict:
        """Get current circuit breaker statistics"""
        return {
            "active_workflows": len(self.workflow_depths),
            "customer_counts": dict(self.customer_counts),
            "agent_rates": {
                agent: len([ts for ts in times if datetime.now() - ts < self.RESET_INTERVAL])
                for agent, times in self.agent_rates.items()
            },
            "reset_time": self.reset_time.isoformat()
        }


# Global circuit breaker instance
_circuit_breaker = DelegationCircuitBreaker()


def get_circuit_breaker() -> DelegationCircuitBreaker:
    """Get the global circuit breaker instance"""
    return _circuit_breaker
