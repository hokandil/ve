"""
Resilience Utilities
- Circuit Breaker
- Retry Decorators
"""
import logging
import time
from functools import wraps
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class CircuitBreakerOpenException(Exception):
    pass

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    logger.info("Circuit breaker entering HALF-OPEN state")
                    self.state = "HALF-OPEN"
                else:
                    raise CircuitBreakerOpenException("Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)
                if self.state == "HALF-OPEN":
                    logger.info("Circuit breaker recovering to CLOSED state")
                    self.reset()
                return result
            except Exception as e:
                self.failures += 1
                self.last_failure_time = time.time()
                logger.warning(f"Circuit breaker failure {self.failures}/{self.failure_threshold}")
                
                if self.failures >= self.failure_threshold:
                    logger.error("Circuit breaker OPENED")
                    self.state = "OPEN"
                
                raise e
        return wrapper

    def reset(self):
        self.failures = 0
        self.state = "CLOSED"

# Global circuit breaker for Agent Gateway
agent_gateway_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=30)

# Standard retry policy
standard_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
