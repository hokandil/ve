# Backend Implementation - Complete Guide

## 🎯 Overview

The VE SaaS Platform backend is a production-ready FastAPI application that provides:

- **REST API** for all platform operations
- **Kubernetes Integration** for VE deployment and management
- **Agent Gateway Integration** for A2A (Agent-to-Agent) communication
- **Redis Queue System** for background task processing
- **Webhook Support** for agent callbacks
- **Comprehensive Token Tracking** for billing
- **Real-time Updates** via Supabase subscriptions

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                    # API route handlers
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── billing.py         # Billing and token usage
│   │   ├── customers.py       # Customer management
│   │   ├── marketplace.py     # VE marketplace
│   │   ├── messages.py        # Messaging system
│   │   ├── orchestrator.py    # Task orchestration
│   │   ├── org_chart.py       # Organization chart
│   │   ├── tasks.py           # Task management
│   │   ├── ves.py             # Virtual employee management
│   │   └── webhooks.py        # Webhook handlers (NEW)
│   │
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Configuration settings
│   │   ├── database.py        # Supabase client
│   │   └── security.py        # Authentication & authorization
│   │
│   ├── services/               # Business logic services
│   │   ├── agent_gateway_service.py    # Agent Gateway integration (NEW)
│   │   ├── kubernetes_service.py       # K8s cluster management (NEW)
│   │   ├── message_service.py          # Message handling
│   │   ├── mock_orchestrator.py        # Mock orchestrator for testing
│   │   ├── orchestrator.py             # Real orchestrator (ENHANCED)
│   │   ├── redis_queue_service.py      # Redis queue management (NEW)
│   │   ├── task_service.py             # Task operations
│   │   └── ve_deployment.py            # VE deployment (ENHANCED)
│   │
│   ├── workers/                # Background workers
│   │   ├── enhanced_worker.py  # Production worker (NEW)
│   │   └── task_worker.py      # Simple worker for testing
│   │
│   ├── main.py                 # FastAPI application entry point
│   └── schemas.py              # Pydantic models (ENHANCED)
│
├── requirements.txt            # Python dependencies (UPDATED)
├── Dockerfile                  # Docker configuration
└── README.md                   # This file
```

## 🚀 New Backend Features

### 1. Kubernetes Service (`kubernetes_service.py`)

**Purpose:** Manages Kubernetes cluster operations for VE deployment

**Key Features:**
- ✅ Create customer-specific namespaces
- ✅ Deploy KAgent agents to Kubernetes
- ✅ Update and delete agents
- ✅ Monitor agent health and status
- ✅ Resource quotas and network policies
- ✅ Graceful fallback when K8s is unavailable

**Usage:**
```python
from app.services.kubernetes_service import get_kubernetes_service

k8s = get_kubernetes_service()

# Create namespace for customer
await k8s.create_customer_namespace(customer_id)

# Deploy agent
await k8s.deploy_agent(namespace, agent_name, manifest)

# Check agent status
status = await k8s.get_agent_status(namespace, agent_name)
```

### 2. Agent Gateway Service (`agent_gateway_service.py`)

**Purpose:** Handles A2A protocol communication with Agent Gateway

**Key Features:**
- ✅ Invoke agents via A2A protocol
- ✅ Call orchestrator for task routing
- ✅ Delegate tasks between agents
- ✅ Query MCP tools
- ✅ Automatic token usage tracking
- ✅ Mock responses for development

**Usage:**
```python
from app.services.agent_gateway_service import get_agent_gateway_service

gateway = get_agent_gateway_service()

# Invoke an agent
response = await gateway.invoke_agent(
    namespace="customer-123",
    agent_name="marketing-manager",
    request_data={"task": "Create campaign"},
    customer_id="123"
)

# Delegate task
await gateway.delegate_task(
    customer_id="123",
    from_agent="manager",
    to_agent="senior",
    task_data={"task": "Research competitors"}
)
```

### 3. Redis Queue Service (`redis_queue_service.py`)

**Purpose:** Background task processing and caching

**Key Features:**
- ✅ Priority-based task queues (urgent, high, medium, low)
- ✅ Message queuing
- ✅ Webhook event queuing
- ✅ Caching with expiration
- ✅ Pub/Sub event distribution
- ✅ Graceful degradation when Redis unavailable

**Usage:**
```python
from app.services.redis_queue_service import get_redis_queue_service

redis = await get_redis_queue_service()

# Enqueue task
await redis.enqueue_task(task_id, customer_id, task_data, priority="high")

# Dequeue task
task = await redis.dequeue_task(priority="high")

# Cache data
await redis.set_cache("key", {"data": "value"}, expire_seconds=3600)
```

### 4. Webhook API (`webhooks.py`)

**Purpose:** Handle callbacks from VE agents and external systems

**Endpoints:**
- `POST /api/webhooks/agent-callback` - Agent status updates, task completions, delegations
- `POST /api/webhooks/token-usage` - Token usage reporting
- `GET /api/webhooks/health` - Health check

**Webhook Events:**
- `task_update` - Task status changed
- `message_send` - Agent sent message to customer
- `agent_status` - Agent status changed
- `delegation` - Task delegated to another agent
- `error` - Agent error occurred
- `token_usage` - Token usage report

**Security:**
- HMAC signature verification
- Customer ID validation
- Rate limiting (recommended)

### 5. Enhanced Worker (`enhanced_worker.py`)

**Purpose:** Production-grade background task processor

**Features:**
- ✅ Multi-priority task processing
- ✅ Agent Gateway integration
- ✅ Kubernetes health monitoring
- ✅ Webhook event processing
- ✅ Automatic retries and error handling
- ✅ Graceful shutdown

**Running:**
```bash
# Development
python -m app.workers.enhanced_worker

# Production (with supervisor/systemd)
uvicorn app.workers.enhanced_worker:main
```

## 🔧 Configuration

### Environment Variables

Add to `.env`:

```bash
# Existing variables...

# Kubernetes
K8S_API_URL=https://your-k8s-cluster:6443
K8S_NAMESPACE_PREFIX=customer-

# Agent Gateway
AGENT_GATEWAY_URL=http://localhost:8081

# Webhooks
WEBHOOK_SECRET=your-secure-webhook-secret-here

# Redis
REDIS_URL=redis://localhost:6379

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## 📊 API Endpoints

### New Webhook Endpoints

```
POST   /api/webhooks/agent-callback
POST   /api/webhooks/token-usage
GET    /api/webhooks/health
```

### Enhanced Existing Endpoints

All existing endpoints now support:
- Better error handling
- Token usage tracking
- Redis caching
- Background processing

## 🔄 Task Processing Flow

### Complete Flow (with all new services):

1. **Customer creates task** (Frontend → API)
   ```
   POST /api/tasks
   ```

2. **API creates task in DB** (Supabase)
   ```
   tasks table: status = "pending"
   ```

3. **Task enqueued to Redis** (by priority)
   ```
   Redis queue: ve:tasks:high
   ```

4. **Worker picks up task**
   ```
   Enhanced Worker dequeues from Redis
   ```

5. **Worker calls Orchestrator** (via Agent Gateway)
   ```
   Agent Gateway → Orchestrator Agent
   Orchestrator analyzes and routes
   ```

6. **Orchestrator delegates to VE** (A2A protocol)
   ```
   Orchestrator → Marketing Manager VE
   ```

7. **VE executes task** (using MCP tools)
   ```
   VE uses tools, queries knowledge base
   ```

8. **VE reports completion** (webhook callback)
   ```
   POST /api/webhooks/agent-callback
   {
     "event_type": "task_update",
     "task_id": "...",
     "status": "completed",
     "result": "..."
   }
   ```

9. **Webhook handler updates DB**
   ```
   tasks table: status = "completed"
   messages table: new message to customer
   ```

10. **Customer sees result** (real-time via Supabase)
    ```
    Frontend receives real-time update
    ```

## 🧪 Testing

### Test Kubernetes Integration

```python
# Test namespace creation
from app.services.kubernetes_service import get_kubernetes_service

k8s = get_kubernetes_service()
success = await k8s.create_customer_namespace("test-customer-123")
print(f"Namespace created: {success}")
```

### Test Agent Gateway

```python
# Test agent invocation
from app.services.agent_gateway_service import get_agent_gateway_service

gateway = get_agent_gateway_service()
response = await gateway.invoke_agent(
    namespace="customer-test",
    agent_name="test-agent",
    request_data={"test": "data"},
    customer_id="test"
)
print(response)
```

### Test Redis Queue

```python
# Test task queuing
from app.services.redis_queue_service import get_redis_queue_service

redis = await get_redis_queue_service()
await redis.enqueue_task("task-1", "customer-1", {"data": "test"}, "high")
task = await redis.dequeue_task("high")
print(task)
```

### Test Webhooks

```bash
# Test webhook endpoint
curl -X POST http://localhost:8000/api/webhooks/agent-callback \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "task_update",
    "customer_id": "123",
    "task_id": "456",
    "status": "completed",
    "result": "Task completed successfully"
  }'
```

## 🚀 Deployment

### Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run worker (separate terminal)
python -m app.workers.enhanced_worker
```

### Production

```bash
# Using Docker Compose
docker-compose up -d

# Or manually with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Run worker with supervisor
supervisorctl start ve-worker
```

### Kubernetes Deployment

```yaml
# Deploy backend to K8s
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ve-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: ve-backend:latest
        env:
        - name: K8S_API_URL
          value: "https://kubernetes.default.svc"
```

## 📈 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Webhook health
curl http://localhost:8000/api/webhooks/health
```

### Metrics to Monitor

- Task queue depth (Redis)
- Task processing time
- Agent invocation success rate
- Token usage per customer
- Webhook delivery success rate
- Kubernetes agent health

### Logging

All services use structured logging:

```python
logger.info(f"Task {task_id} processed successfully")
logger.error(f"Failed to invoke agent: {error}")
```

## 🔐 Security

### Implemented Security Features

1. **Webhook Signature Verification**
   - HMAC-SHA256 signatures
   - Prevents unauthorized callbacks

2. **Kubernetes RBAC**
   - Service accounts for API
   - Namespace isolation per customer

3. **Agent Gateway Authentication**
   - JWT tokens for A2A calls
   - Customer ID validation

4. **Rate Limiting** (recommended)
   - Use Redis for rate limiting
   - Implement per-customer limits

## 📝 Next Steps

### Recommended Enhancements

1. **WebSocket Support**
   - Real-time task updates
   - Live agent status

2. **Advanced Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - OpenTelemetry tracing

3. **Batch Operations**
   - Bulk task creation
   - Batch VE deployment

4. **Advanced Caching**
   - Cache VE templates
   - Cache customer org structures

5. **API Rate Limiting**
   - Per-customer limits
   - Per-endpoint limits

## 🎉 Summary

The backend now includes:

✅ **Kubernetes Service** - Full K8s integration for VE deployment
✅ **Agent Gateway Service** - A2A protocol for agent communication  
✅ **Redis Queue Service** - Background task processing with priorities
✅ **Webhook API** - Agent callback handling
✅ **Enhanced Worker** - Production-grade task processor
✅ **Token Tracking** - Comprehensive billing support
✅ **Error Handling** - Graceful degradation and retries
✅ **Documentation** - Complete implementation guide

**All backend tasks are now complete and production-ready!** 🚀
