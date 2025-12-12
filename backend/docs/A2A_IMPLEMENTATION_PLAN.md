# 🚀 A2A IMPLEMENTATION PLAN: Production Roadmap

**This document outlines the step-by-step plan to make the Agent-to-Agent system production-ready, addressing gaps, implementing missing features, and ensuring security & compliance.**

---

## 📊 CURRENT PRODUCTION READINESS: 65%

### Status Breakdown

| Component | Status | Score | Gap |
|-----------|--------|-------|-----|
| Core Functionality | ✅ WORKING | 95% | Minor JSON parsing fragility |
| Real-time Updates | ✅ WORKING | 95% | Occasional Centrifugo latency |
| User Approval Workflow | ✅ WORKING | 90% | UI could show more context |
| Multi-tenant Isolation | ✅ WORKING | 85% | Kubernetes policy untested |
| Agent Gateway Routing | ✅ WORKING | 85% | Error handling could improve |
| Leakage Detection | ✅ WORKING | 80% | Detector internals unclear |
| Authorization | ⚠️ PARTIAL | 40% | RBAC not implemented |
| Audit Logging | ❌ MISSING | 0% | No audit tables |
| Rate Limiting | ❌ MISSING | 0% | No protection |
| Metrics & Observability | ❌ MISSING | 0% | No tracing/metrics |
| Distributed Tracing | ⚠️ PARTIAL | 30% | OpenObserv configured but not instrumented |
| Decision Persistence | ❌ MISSING | 0% | Lost after workflow completes |

**Overall Readiness:** 65% (Core working, critical gaps in observability & audit)

---

## 🎯 GO/NO-GO CRITERIA FOR PRODUCTION

### Must Have (Blocking Launch)
- ✅ Core A2A delegation functionality working
- ❌ Audit logging table created + decisions persisted
- ❌ Rate limiting implemented (basic)
- ❌ Authorization verification tested
- ❌ Error messages improved for users
- ❌ Leakage detector internals verified

### Should Have (Before Launch)
- ❌ Prometheus metrics integrated
- ❌ Jaeger tracing instrumented
- ❌ RBAC role matrix defined
- ❌ Decision analysis dashboard
- ❌ Performance benchmarks documented

### Nice to Have (Post-Launch)
- ⭕ Agent skill-based filtering
- ⭕ ML-based routing optimization
- ⭕ Delegation pattern analysis
- ⭕ Cost optimization suggestions

---

## 📋 WEEK 1: CRITICAL PATH (Must Complete)

### Priority 1: Audit Logging Infrastructure
**Deadline:** End of Day 3  
**Owner:** Backend Lead  
**Effort:** 8-10 hours

#### 1.1 Create Database Tables

```sql
-- Migration: 001_create_audit_tables.sql

CREATE TABLE agent_delegation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR NOT NULL,
    customer_id VARCHAR NOT NULL,
    delegation_depth INT NOT NULL,
    
    -- Decision details
    agent_type VARCHAR NOT NULL,
    agent_ve_id VARCHAR,
    decision_action VARCHAR NOT NULL,  -- 'handle', 'delegate', 'parallel', 'ask_clarification'
    delegated_to_type VARCHAR,
    confidence_score FLOAT,
    decision_reason TEXT,
    
    -- Execution
    execution_time_seconds FLOAT,
    status VARCHAR,  -- 'pending', 'in_progress', 'completed', 'failed'
    result_summary TEXT,
    error_message TEXT,
    
    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    
    -- Indexes
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (customer_id) REFERENCES customers(id)
);

CREATE INDEX idx_delegation_customer ON agent_delegation_logs(customer_id);
CREATE INDEX idx_delegation_task ON agent_delegation_logs(task_id);
CREATE INDEX idx_delegation_agent ON agent_delegation_logs(agent_type);
CREATE INDEX idx_delegation_date ON agent_delegation_logs(created_at DESC);
CREATE INDEX idx_delegation_status ON agent_delegation_logs(status);

-- Table for tracking authorization checks
CREATE TABLE agent_authorization_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR NOT NULL,
    agent_ve_id VARCHAR NOT NULL,
    target_agent_type VARCHAR NOT NULL,
    action VARCHAR NOT NULL,  -- 'invoke', 'delegate_to', 'access_context'
    authorized BOOLEAN,
    authorization_reason VARCHAR,
    denied_reason TEXT,
    request_headers JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_auth_customer ON agent_authorization_logs(customer_id);
CREATE INDEX idx_auth_agent ON agent_authorization_logs(agent_ve_id);
CREATE INDEX idx_auth_authorized ON agent_authorization_logs(authorized);
CREATE INDEX idx_auth_date ON agent_authorization_logs(created_at DESC);

-- Table for leakage detection events
CREATE TABLE leakage_detection_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id VARCHAR NOT NULL,
    customer_id VARCHAR NOT NULL,
    agent_type VARCHAR NOT NULL,
    agent_ve_id VARCHAR,
    
    -- Detection
    severity VARCHAR NOT NULL,  -- 'info', 'warning', 'high', 'critical'
    detection_type VARCHAR,  -- 'credential_leak', 'pii_leak', 'unauthorized_access', etc
    detected_content_preview TEXT,  -- First 500 chars of problematic content
    confidence FLOAT,
    
    -- Action
    action_taken VARCHAR,  -- 'blocked', 'redacted', 'flagged', 'allowed'
    redacted_response TEXT,
    
    -- Metadata
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_leakage_customer ON leakage_detection_logs(customer_id);
CREATE INDEX idx_leakage_severity ON leakage_detection_logs(severity);
CREATE INDEX idx_leakage_date ON leakage_detection_logs(created_at DESC);
CREATE INDEX idx_leakage_blocked ON leakage_detection_logs(action_taken);
```

**Apply Migration:**
```bash
# In backend directory
python -m alembic upgrade head

# Verify tables created
psql -d supabase_db -c "\dt agent_*"
```

**Reality Check:**
- ✅ Tables created with proper indexes
- ✅ Foreign keys maintain referential integrity
- ✅ customer_id in all tables for multi-tenant queries
- ✅ Timestamps for audit trail

#### 1.2 Update Workflow to Persist Decisions

**File:** `backend/app/temporal/workflows.py`

```python
# BEFORE: Decisions only in memory
self._delegation_status["decisions_made"].append({
    "agent": "marketing-manager",
    "action": "delegate",
    "confidence": 0.92
    # ... lost when workflow ends
})

# AFTER: Decisions persisted to database
await workflow.execute_activity(
    save_delegation_decision_activity,
    args=[
        task_id=task_id,
        customer_id=customer_id,
        delegation_depth=current_depth,
        agent_type=current_agent_type,
        decision_action=decision["action"],
        delegated_to=decision.get("delegated_to"),
        confidence=decision["confidence"],
        reason=decision["reason"],
        execution_time=execution_time
    ]
)
```

**Create Activity:**

```python
# backend/app/temporal/activities/delegation_activities.py

@activity.defn
async def save_delegation_decision_activity(
    task_id: str,
    customer_id: str,
    delegation_depth: int,
    agent_type: str,
    decision_action: str,
    delegated_to: Optional[str],
    confidence: float,
    reason: str,
    execution_time: float
) -> dict:
    """
    Persist delegation decision to audit log
    """
    from app.db import supabase
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        result = supabase.table("agent_delegation_logs").insert({
            "task_id": task_id,
            "customer_id": customer_id,
            "delegation_depth": delegation_depth,
            "agent_type": agent_type,
            "decision_action": decision_action,
            "delegated_to_type": delegated_to,
            "confidence_score": confidence,
            "decision_reason": reason,
            "execution_time_seconds": execution_time,
            "status": "completed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }).execute()
        
        logger.info(f"Decision logged: {agent_type} -> {decision_action} (confidence: {confidence})")
        return {"success": True, "log_id": result.data[0]["id"]}
        
    except Exception as e:
        logger.error(f"Failed to log decision: {str(e)}")
        # Don't block workflow on logging failure
        return {"success": False, "error": str(e)}
```

**Workflow Integration:**

```python
# In IntelligentDelegationWorkflow.run()

# After each agent makes a decision
decision = await invoke_agent(...)  # Get decision

# Immediately persist it
await workflow.execute_activity(
    save_delegation_decision_activity,
    args=[
        task_id, customer_id, delegation_depth,
        current_agent_type, decision["action"],
        decision.get("delegated_to"), decision["confidence"],
        decision["reason"], time.time() - start_time
    ]
)
```

**Testing:**
```python
# backend/tests/test_delegation_logging.py

import pytest
from app.temporal.activities.delegation_activities import save_delegation_decision_activity

@pytest.mark.asyncio
async def test_decision_persisted_to_database():
    """Test that delegation decisions are saved to audit log"""
    
    # Execute activity
    result = await save_delegation_decision_activity(
        task_id="task-123",
        customer_id="techcorp",
        delegation_depth=0,
        agent_type="marketing-manager",
        decision_action="delegate",
        delegated_to="copywriter",
        confidence=0.92,
        reason="Test delegation",
        execution_time=45.2
    )
    
    # Verify result
    assert result["success"] == True
    
    # Verify database entry
    from app.db import supabase
    records = supabase.table("agent_delegation_logs").select(
        "*"
    ).eq("task_id", "task-123").execute()
    
    assert len(records.data) == 1
    assert records.data[0]["agent_type"] == "marketing-manager"
    assert records.data[0]["decision_action"] == "delegate"
    assert records.data[0]["confidence_score"] == 0.92
```

**Deployment:**
```bash
cd backend

# Run migration
alembic upgrade head

# Verify
sql "SELECT COUNT(*) FROM agent_delegation_logs" # Should be 0

# Deploy code
git commit -am "feat: Add decision persistence to audit logs"
git push origin main

# Verify in prod
sql "SELECT * FROM agent_delegation_logs LIMIT 1" # Should have records after first task
```

**Verification Checklist:**
- [ ] Tables created in database
- [ ] Indexes created for performance
- [ ] Activity function tested locally
- [ ] Workflow calls activity after each decision
- [ ] Tests passing (all 3 test cases)
- [ ] Deployed to staging
- [ ] Data appearing in audit logs

---

### Priority 2: Rate Limiting
**Deadline:** End of Day 4  
**Owner:** Backend Lead  
**Effort:** 6-8 hours

#### 2.1 Implement Rate Limiting

```python
# backend/app/core/rate_limiter.py

from redis import Redis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DelegationRateLimiter:
    """
    Rate limiter for agent delegation to prevent abuse
    
    Limits:
    - Per customer: 1000 tasks/day
    - Per agent: 100 invocations/hour
    - Per delegation pair: 50 delegations/hour
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def check_customer_limit(self, customer_id: str) -> tuple[bool, str]:
        """Check if customer exceeded daily task limit"""
        key = f"rate:customer:{customer_id}:tasks:daily"
        current = await self.redis.incr(key)
        
        # Set expiry on first creation
        if current == 1:
            await self.redis.expire(key, 86400)  # 1 day
        
        limit = 1000  # Tasks per day
        if current > limit:
            return False, f"Customer {customer_id} exceeded {limit} tasks/day limit. Current: {current}"
        
        return True, f"{limit - current} tasks remaining today"
    
    async def check_agent_limit(self, agent_type: str) -> tuple[bool, str]:
        """Check if agent exceeded invocation limit"""
        key = f"rate:agent:{agent_type}:invocations:hourly"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 3600)  # 1 hour
        
        limit = 100  # Invocations per hour
        if current > limit:
            return False, f"Agent {agent_type} exceeded {limit} invocations/hour. Current: {current}"
        
        return True, f"{limit - current} invocations remaining this hour"
    
    async def check_delegation_pair_limit(
        self,
        from_agent: str,
        to_agent: str,
        customer_id: str
    ) -> tuple[bool, str]:
        """Check if delegation pair exceeded hourly limit"""
        key = f"rate:delegation:{customer_id}:{from_agent}->{to_agent}:hourly"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 3600)  # 1 hour
        
        limit = 50  # Delegations per hour
        if current > limit:
            return (
                False,
                f"Delegation {from_agent}->{to_agent} "
                f"exceeded {limit} times/hour. Current: {current}"
            )
        
        return True, f"{limit - current} delegations remaining this hour"
    
    async def apply_limits(
        self,
        customer_id: str,
        current_agent_type: str,
        delegated_to_agent: Optional[str] = None
    ) -> tuple[bool, str]:
        """Apply all rate limits and return if allowed"""
        
        # Check customer limit
        allowed, msg = await self.check_customer_limit(customer_id)
        if not allowed:
            logger.warning(f"Rate limit hit: {msg}")
            return False, msg
        
        # Check agent limit
        allowed, msg = await self.check_agent_limit(current_agent_type)
        if not allowed:
            logger.warning(f"Rate limit hit: {msg}")
            return False, msg
        
        # Check delegation pair limit (if delegating)
        if delegated_to_agent:
            allowed, msg = await self.check_delegation_pair_limit(
                current_agent_type,
                delegated_to_agent,
                customer_id
            )
            if not allowed:
                logger.warning(f"Rate limit hit: {msg}")
                return False, msg
        
        return True, "All rate limits passed"
```

#### 2.2 Integrate into Workflow

```python
# backend/app/temporal/workflows.py

from app.core.rate_limiter import DelegationRateLimiter
from redis import Redis

class IntelligentDelegationWorkflow:
    
    def __init__(self):
        self.rate_limiter = DelegationRateLimiter(
            Redis.from_url(settings.REDIS_URL)
        )
    
    @workflow.run
    async def run(self, params: dict) -> dict:
        customer_id = params["customer_id"]
        current_agent_type = params["current_agent_type"]
        delegation_depth = params["delegation_depth"]
        
        # Check rate limits at start
        allowed, msg = await self.rate_limiter.apply_limits(
            customer_id=customer_id,
            current_agent_type=current_agent_type,
            delegated_to_agent=None  # Not delegating yet
        )
        
        if not allowed:
            return {
                "error": "Rate limit exceeded",
                "message": msg,
                "status": "rate_limited"
            }
        
        # Get decision from agent
        decision = await invoke_agent(...)
        
        # If delegating, check delegation pair limit
        if decision["action"] == "delegate":
            allowed, msg = await self.rate_limiter.apply_limits(
                customer_id=customer_id,
                current_agent_type=current_agent_type,
                delegated_to_agent=decision.get("delegated_to")
            )
            
            if not allowed:
                return {
                    "error": "Rate limit exceeded for delegation",
                    "message": msg,
                    "status": "rate_limited"
                }
```

#### 2.3 API Endpoint Rate Limiting

```python
# backend/app/routes/tasks.py

from fastapi import HTTPException, status
from app.core.rate_limiter import DelegationRateLimiter
from redis import Redis

rate_limiter = DelegationRateLimiter(Redis.from_url(settings.REDIS_URL))

@router.post("/tasks")
@require_auth
async def create_task(request: CreateTaskRequest, user: User):
    """Create a new task (rate limited)"""
    
    customer_id = user.customer_id
    
    # Check rate limit
    allowed, msg = await rate_limiter.check_customer_limit(customer_id)
    if not allowed:
        raise HTTPException(
            status_code=429,  # Too Many Requests
            detail=msg
        )
    
    # Create task
    task = await create_task_in_db(request, customer_id)
    
    # Start workflow
    await start_orchestrator_workflow(task)
    
    return {"task_id": task["id"], "status": "created"}
```

**Testing:**
```python
# backend/tests/test_rate_limiting.py

@pytest.mark.asyncio
async def test_customer_rate_limit_enforced():
    """Test that customer daily limit is enforced"""
    limiter = DelegationRateLimiter(redis_test_client)
    
    # Simulate 1001 tasks (limit is 1000)
    for i in range(1001):
        allowed, msg = await limiter.check_customer_limit("techcorp")
        if i < 1000:
            assert allowed == True
        else:
            assert allowed == False
            assert "exceeded" in msg

@pytest.mark.asyncio
async def test_agent_rate_limit_enforced():
    """Test that agent hourly limit is enforced"""
    limiter = DelegationRateLimiter(redis_test_client)
    
    # Simulate 101 invocations (limit is 100)
    for i in range(101):
        allowed, msg = await limiter.check_agent_limit("copywriter")
        if i < 100:
            assert allowed == True
        else:
            assert allowed == False
```

**Deployment:**
```bash
cd backend

# Deploy code
git commit -am "feat: Add rate limiting to prevent abuse"
git push origin main

# Verify Redis is working
redis-cli ping
# Should output: PONG

# Test rate limiting
pytest tests/test_rate_limiting.py -v
```

---

### Priority 3: Authorization Verification
**Deadline:** End of Day 5  
**Owner:** Security Lead  
**Effort:** 10-12 hours

#### 3.1 Create Authorization Test Suite

```python
# backend/tests/integration/test_authorization.py

import pytest
from app.core.agent_gateway import AgentGatewayService

class TestMultiTenantIsolation:
    """
    Verify multi-tenant authorization across all layers
    """
    
    @pytest.fixture
    async def gateway_service(self):
        return AgentGatewayService()
    
    @pytest.mark.asyncio
    async def test_customer_cannot_access_other_customer_agents(
        self,
        gateway_service
    ):
        """
        Verify that TechCorp cannot invoke AccmeCorp's agents
        """
        
        # Setup
        techcorp_customer_id = "techcorp"
        acmecorp_customer_id = "acmecorp"
        
        # Try to invoke AccmeCorp agent as TechCorp
        with pytest.raises(AuthorizationError):
            await gateway_service.invoke_agent(
                customer_id=techcorp_customer_id,
                agent_type="acmecorp-private-agent",  # AccmeCorp's agent
                message="Trying to access private data"
            )
    
    @pytest.mark.asyncio
    async def test_headers_include_customer_id(self, gateway_service):
        """
        Verify that X-Customer-ID header is set on all requests
        """
        
        # Spy on HTTP calls
        call_log = []
        
        async def mock_post(url, headers, **kwargs):
            call_log.append({"url": url, "headers": headers})
            return {"jsonrpc": "2.0", "result": {}}
        
        gateway_service._http_client.post = mock_post
        
        # Make request
        await gateway_service.invoke_agent(
            customer_id="techcorp",
            agent_type="copywriter",
            message="Test message"
        )
        
        # Verify header
        assert len(call_log) > 0
        assert call_log[0]["headers"]["X-Customer-ID"] == "techcorp"
    
    @pytest.mark.asyncio
    async def test_context_isolation_in_agent_response(self):
        """
        Verify that agents only see their customer's context
        """
        
        from app.db import supabase
        
        # Create two customers with agents
        techcorp_agents = supabase.table("customer_ves").select(
            "*"
        ).eq("customer_id", "techcorp").execute()
        
        acmecorp_agents = supabase.table("customer_ves").select(
            "*"
        ).eq("customer_id", "acmecorp").execute()
        
        # Verify isolation
        assert len(techcorp_agents.data) > 0
        assert len(acmecorp_agents.data) > 0
        
        for agent in techcorp_agents.data:
            assert agent["customer_id"] == "techcorp"
            assert "acmecorp" not in str(agent)
        
        for agent in acmecorp_agents.data:
            assert agent["customer_id"] == "acmecorp"
            assert "techcorp" not in str(agent)
    
    @pytest.mark.asyncio
    async def test_leakage_detection_prevents_data_exposure(self):
        """
        Verify that leakage detector blocks unauthorized data access
        """
        
        from app.security.leakage_detector import leakage_detector
        
        # Simulate agent response with leaked data
        malicious_response = """
        Customer data for AccmeCorp:
        API Key: sk-1234567890
        Database URL: postgresql://user:pass@db.internal
        """
        
        alerts = leakage_detector.scan(
            content=malicious_response,
            customer_id="techcorp",
            metadata={"agent_type": "copywriter"}
        )
        
        # Should detect leakage
        assert len(alerts) > 0
        assert any(alert.severity in ["high", "critical"] for alert in alerts)

class TestRBAC:
    """
    Test role-based access control
    """
    
    @pytest.mark.asyncio
    async def test_agent_cannot_delegate_to_higher_seniority(
        self
    ):
        """
        Verify that specialists cannot delegate to managers
        """
        
        # TODO: Implement when RBAC added
        pass
    
    @pytest.mark.asyncio
    async def test_agent_can_delegate_to_specialist(
        self
    ):
        """
        Verify that managers can delegate to specialists
        """
        
        # TODO: Implement when RBAC added
        pass
```

**Run Tests:**
```bash
cd backend

pytest tests/integration/test_authorization.py -v

# Expected output:
# test_customer_cannot_access_other_customer_agents PASSED
# test_headers_include_customer_id PASSED
# test_context_isolation_in_agent_response PASSED
# test_leakage_detection_prevents_data_exposure PASSED
# ======================== 4 passed ========================
```

#### 3.2 Document Authorization Architecture

```markdown
# Authorization Architecture

## Multi-Tenant Isolation

### Layer 1: API Authentication
- JWT token contains customer_id
- All API endpoints extract customer_id from token
- No cross-customer access allowed

### Layer 2: Workflow Parameter
- customer_id flows through entire workflow
- Child workflows receive parent's customer_id
- No cross-tenant data mixing

### Layer 3: Database Queries
- All queries filter by customer_id
- Supabase row-level security enforces this
- Database blocks any cross-tenant reads

### Layer 4: Agent Gateway Headers
- X-Customer-ID header on all requests
- Kubernetes NetworkPolicy validates header
- Untrusted header rejected

### Layer 5: Leakage Detection
- Scans agent responses for unauthorized data
- Blocks responses containing other customer's data
- Critical security checkpoint

## Testing Verification
- Unit tests: Individual layer isolation
- Integration tests: Cross-layer scenarios
- End-to-end tests: Real workflow execution
- Chaos tests: Attempted boundary violations
```

**Verification Checklist:**
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Architecture diagram added
- [ ] Kubernetes policies reviewed
- [ ] Leakage detector internals verified
- [ ] Security team sign-off

---

### Priority 4: Error Handling & User Messages
**Deadline:** End of Day 6  
**Owner:** Backend Lead  
**Effort:** 6-8 hours

#### 4.1 Improve Error Messages

```python
# backend/app/core/error_messages.py

class TaskError(Exception):
    """Base exception for task-related errors"""
    
    def __init__(self, user_message: str, internal_message: str, error_code: str):
        self.user_message = user_message  # Safe for user
        self.internal_message = internal_message  # For logs
        self.error_code = error_code  # For debugging
        super().__init__(internal_message)

class AgentInvocationError(TaskError):
    pass

class DelegationFailedError(TaskError):
    pass

class RateLimitExceededError(TaskError):
    pass

class LeakageDetectedError(TaskError):
    pass

# Error message mappings
ERROR_MESSAGES = {
    "agent_timeout": {
        "user": "The agent took too long to respond. Please try again.",
        "internal": "Agent invocation timed out after 60s",
        "code": "AGENT_TIMEOUT"
    },
    "invalid_json": {
        "user": "Agent returned invalid response format. Please try again.",
        "internal": "Agent response failed JSON parsing",
        "code": "INVALID_JSON"
    },
    "rate_limit": {
        "user": "Too many requests. Please wait before trying again.",
        "internal": "Rate limit exceeded for customer:agent pair",
        "code": "RATE_LIMIT_EXCEEDED"
    },
    "authorization_failed": {
        "user": "You don't have permission to access this agent.",
        "internal": "Authorization check failed for customer:agent access",
        "code": "AUTH_FAILED"
    },
    "leakage_detected": {
        "user": "Security check blocked the response. Please contact support.",
        "internal": "Potential data leakage detected in agent response",
        "code": "LEAKAGE_DETECTED"
    },
    "max_depth_exceeded": {
        "user": "Task became too complex. Breaking down into simpler subtasks recommended.",
        "internal": "Delegation depth exceeded maximum (5)",
        "code": "MAX_DEPTH_EXCEEDED"
    },
    "agent_unavailable": {
        "user": "The selected agent is currently unavailable. Try another agent.",
        "internal": "Agent pod not responding to health check",
        "code": "AGENT_UNAVAILABLE"
    }
}

def get_error_message(error_type: str) -> dict:
    """Get user-safe and internal error messages"""
    if error_type not in ERROR_MESSAGES:
        return ERROR_MESSAGES["agent_timeout"]  # Safe default
    return ERROR_MESSAGES[error_type]
```

#### 4.2 Update Workflow Exception Handling

```python
# backend/app/temporal/workflows.py

from app.core.error_messages import (
    get_error_message,
    TaskError,
    RateLimitExceededError
)

class IntelligentDelegationWorkflow:
    
    @workflow.run
    async def run(self, params: dict) -> dict:
        try:
            # Check rate limits
            allowed, msg = await self.rate_limiter.apply_limits(...)
            if not allowed:
                error_info = get_error_message("rate_limit")
                raise RateLimitExceededError(
                    user_message=error_info["user"],
                    internal_message=error_info["internal"],
                    error_code=error_info["code"]
                )
            
            # Invoke agent
            try:
                decision = await invoke_agent(...)
            except TimeoutError as e:
                error_info = get_error_message("agent_timeout")
                await update_task_status_activity(
                    task_id=task_id,
                    status="failed",
                    progress_message=error_info["user"]
                )
                raise
            except JSONDecodeError as e:
                error_info = get_error_message("invalid_json")
                await update_task_status_activity(
                    task_id=task_id,
                    status="failed",
                    progress_message=error_info["user"]
                )
                raise
            
            # Check leakage
            alerts = leakage_detector.scan(response)
            if any(alert.severity in ["high", "critical"] for alert in alerts):
                error_info = get_error_message("leakage_detected")
                raise LeakageDetectedError(
                    user_message=error_info["user"],
                    internal_message=error_info["internal"],
                    error_code=error_info["code"]
                )
            
            # ... rest of workflow
            
        except TaskError as e:
            # Log error for debugging
            logging.error(f"TaskError: {e.internal_message}")
            
            # Return user-safe error to UI
            return {
                "error": True,
                "user_message": e.user_message,
                "error_code": e.error_code
            }
        except Exception as e:
            # Unexpected error
            logging.error(f"Unexpected error: {str(e)}", exc_info=True)
            return {
                "error": True,
                "user_message": "An unexpected error occurred. Please contact support.",
                "error_code": "INTERNAL_ERROR"
            }
```

#### 4.3 Update API Response Handlers

```python
# backend/app/routes/tasks.py

from fastapi.responses import JSONResponse

@router.post("/tasks/{task_id}/execute")
@require_auth
async def execute_task(
    task_id: str,
    user: User
):
    """Execute a task and handle errors gracefully"""
    
    try:
        task = await get_task(task_id, user.customer_id)
        
        # Start workflow
        workflow_id = await start_orchestrator_workflow(task)
        
        return {
            "success": True,
            "task_id": task_id,
            "workflow_id": workflow_id,
            "status": "started",
            "message": "Task execution started. You'll be notified of updates."
        }
        
    except RateLimitExceededError as e:
        return JSONResponse(
            status_code=429,
            content={
                "success": False,
                "error": e.error_code,
                "message": e.user_message,
                "details": e.internal_message  # Only in logs, not API
            }
        )
    except AuthorizationError as e:
        return JSONResponse(
            status_code=403,
            content={
                "success": False,
                "error": "AUTH_FAILED",
                "message": "You don't have permission to perform this action."
            }
        )
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again later."
            }
        )
```

---

## 📋 WEEK 2: HIGH PRIORITY

### Priority 5: Prometheus Metrics Integration
**Deadline:** End of Day 10  
**Owner:** DevOps/Backend Lead  
**Effort:** 8-10 hours

**Key Metrics to Track:**
```python
# backend/app/core/metrics.py

from prometheus_client import Counter, Histogram, Gauge

# Counters
task_created = Counter(
    'a2a_tasks_created_total',
    'Total tasks created',
    ['customer_id', 'priority']
)

delegation_decisions = Counter(
    'a2a_delegations_total',
    'Total delegation decisions',
    ['agent_from', 'agent_to', 'decision_action', 'result']
)

rate_limit_hits = Counter(
    'a2a_rate_limit_hits_total',
    'Rate limit hits',
    ['limit_type', 'customer_id']
)

leakage_detected = Counter(
    'a2a_leakage_detected_total',
    'Leakage detection events',
    ['severity', 'customer_id']
)

# Histograms
task_duration = Histogram(
    'a2a_task_duration_seconds',
    'Task execution duration',
    ['agent_count', 'delegation_depth'],
    buckets=(5, 10, 30, 60, 300, 600, 1800)
)

agent_response_time = Histogram(
    'a2a_agent_response_time_seconds',
    'Agent response time',
    ['agent_type'],
    buckets=(1, 5, 10, 30, 60)
)

# Gauges
active_workflows = Gauge(
    'a2a_active_workflows',
    'Active delegation workflows',
    ['customer_id']
)

agent_availability = Gauge(
    'a2a_agent_availability',
    'Agent availability status',
    ['agent_type', 'customer_id']
)
```

---

## 📋 WEEK 3: NICE TO HAVE

### Priority 6: Jaeger Distributed Tracing
**Deadline:** End of Day 14  
**Owner:** DevOps/Backend Lead  
**Effort:** 10-12 hours

### Priority 7: RBAC Implementation
**Deadline:** End of Day 14  
**Owner:** Backend Lead  
**Effort:** 12-15 hours

### Priority 8: Decision Analysis Dashboard
**Deadline:** End of Week 3  
**Owner:** Frontend/DevOps Lead  
**Effort:** 10-15 hours

---

## 🚀 DEPLOYMENT STRATEGY

### Stage 1: Staging (Week 1)
```bash
# Deploy to staging environment
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# Automated deployment
# k8s deployment applies new image tag

# Run test suite
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Load testing
locust -f tests/load/locustfile.py --headless -u 100 -r 5

# Performance benchmarks
# Average task duration: < 10 minutes
# Agent response time p99: < 30s
# Error rate: < 0.1%
```

### Stage 2: Canary (Week 2)
```bash
# Deploy to 10% of production
git tag v1.0.0-rc2
git push origin v1.0.0-rc2

# Istio canary traffic split:
# v0.9.0: 90% traffic
# v1.0.0-rc2: 10% traffic

# Monitor metrics
# - Error rates
# - Response times
# - Rate limit hits
# - Delegation success rate

# If healthy for 24 hours, proceed to full rollout
```

### Stage 3: Production (Week 3)
```bash
# Full production deployment
git tag v1.0.0
git push origin v1.0.0

# Automated canary rollout
# v0.9.0 → v1.0.0: 10% -> 50% -> 90% -> 100%
# Over 2 hours with metrics monitoring

# Keep v0.9.0 ready for instant rollback if needed
```

---

## 📊 SUCCESS CRITERIA

### By End of Week 1
- ✅ Audit logging fully functional
- ✅ Rate limiting enforced
- ✅ Authorization tests passing
- ✅ Error messages user-friendly
- 🎯 Readiness: 85%

### By End of Week 2
- ✅ Prometheus metrics integrated
- ✅ Jaeger tracing working
- ✅ Dashboard deployed
- ✅ Performance benchmarks met
- 🎯 Readiness: 95%

### By End of Week 3
- ✅ RBAC implemented
- ✅ Load testing passed
- ✅ Documentation complete
- ✅ Team trained on operations
- 🎯 Readiness: 100% - LAUNCH READY

---

## 📝 RISK MITIGATION

### Risk 1: Data Loss During Migration
**Probability:** Low  
**Impact:** Critical  
**Mitigation:**
- Backup database before migrations
- Test migrations on staging first
- Rollback scripts prepared

### Risk 2: Performance Degradation
**Probability:** Medium  
**Impact:** High  
**Mitigation:**
- Add database indexes upfront
- Load testing before production
- Rate limiting prevents cascading failures

### Risk 3: Security Vulnerability
**Probability:** Low  
**Impact:** Critical  
**Mitigation:**
- Security team reviews all auth code
- Automated leakage detection
- Penetration testing in staging

### Risk 4: Team Capacity
**Probability:** High  
**Impact:** Medium  
**Mitigation:**
- Parallel workstreams (logging, rate limit, auth)
- Clear ownership and deadlines
- Daily standup to unblock issues

---

## 👥 TEAM ASSIGNMENTS

| Task | Owner | Duration | Status |
|------|-------|----------|--------|
| Audit Logging | Backend Lead | 3 days | ⏳ Not Started |
| Rate Limiting | Backend Dev | 2 days | ⏳ Not Started |
| Auth Verification | Security Lead | 3 days | ⏳ Not Started |
| Error Handling | Backend Dev | 2 days | ⏳ Not Started |
| Metrics Integration | DevOps | 3 days | ⏳ Not Started |
| Jaeger Tracing | DevOps | 3 days | ⏳ Not Started |
| RBAC Implementation | Backend Lead | 4 days | ⏳ Not Started |
| Dashboard | Frontend Dev | 3 days | ⏳ Not Started |
| Testing | QA | 5 days | ⏳ Not Started |
| Documentation | Tech Writer | 3 days | ⏳ Not Started |

---

## 📋 LAUNCH CHECKLIST

- [ ] All code reviewed and merged
- [ ] Test coverage > 80%
- [ ] Security audit passed
- [ ] Performance benchmarks met
- [ ] Load testing passed
- [ ] Staging validation complete
- [ ] Disaster recovery plan ready
- [ ] On-call runbook prepared
- [ ] Customer communication drafted
- [ ] Monitoring dashboards live
- [ ] Team trained
- [ ] Executive sign-off obtained

---

## 🎯 SUCCESS METRICS (Post-Launch)

**Target Metrics (Month 1):**
- Task success rate: > 95%
- Average task duration: < 8 minutes
- Agent response time p99: < 25s
- Error rate: < 0.5%
- Customer satisfaction: > 4.5/5
- Support tickets: < 5/week
- Delegation depth average: 1.5
- Rate limit hits: < 1%
- Leakage detections: 0 (critical)

---

## 📞 SUPPORT & ESCALATION

**During Launch Week:**
- 24/7 on-call rotation
- Incident response < 15 minutes
- Executive escalation path defined
- Customer support team briefed

**Contact Info:**
- Slack: #a2a-production
- PagerDuty: A2A-on-call
- Incident Commander: [TBD]
- Executive Sponsor: [TBD]

---

**Document Version:** 1.0  
**Last Updated:** December 12, 2025  
**Next Review:** December 19, 2025  
**Status:** Ready for Development
