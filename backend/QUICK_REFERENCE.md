# Backend Quick Reference Guide

## 🚀 Quick Start Commands

### Start Backend Services

```bash
# Start API server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start enhanced worker (separate terminal)
python -m app.workers.enhanced_worker

# Or use Docker Compose
docker-compose up -d
```

### API Documentation

```
http://localhost:8000/docs        # Swagger UI
http://localhost:8000/redoc       # ReDoc
http://localhost:8000/health      # Health check
```

---

## 📚 Service Quick Reference

### 1. Kubernetes Service

```python
from app.services.kubernetes_service import get_kubernetes_service

k8s = get_kubernetes_service()

# Create namespace
await k8s.create_customer_namespace("customer-123")

# Deploy agent
await k8s.deploy_agent(
    namespace="customer-customer-123",
    agent_name="marketing-manager",
    agent_manifest={...}
)

# Check status
status = await k8s.get_agent_status("customer-customer-123", "marketing-manager")

# Delete agent
await k8s.delete_agent("customer-customer-123", "marketing-manager")
```

### 2. Agent Gateway Service

```python
from app.services.agent_gateway_service import get_agent_gateway_service

gateway = get_agent_gateway_service()

# Invoke agent
response = await gateway.invoke_agent(
    namespace="customer-customer-123",
    agent_name="marketing-manager",
    request_data={"task": "Create campaign"},
    customer_id="customer-123"
)

# Invoke orchestrator
result = await gateway.invoke_orchestrator(
    customer_id="customer-123",
    task_description="Create marketing campaign",
    context={"budget": 10000}
)

# Delegate task
await gateway.delegate_task(
    customer_id="customer-123",
    from_agent="manager",
    to_agent="senior",
    task_data={"task": "Research"}
)
```

### 3. Redis Queue Service

```python
from app.services.redis_queue_service import get_redis_queue_service

redis = await get_redis_queue_service()

# Enqueue task
await redis.enqueue_task(
    task_id="task-123",
    customer_id="customer-123",
    task_data={"title": "Create campaign"},
    priority="high"  # urgent, high, medium, low
)

# Dequeue task
task = await redis.dequeue_task(priority="high", timeout=5)

# Cache data
await redis.set_cache("key", {"data": "value"}, expire_seconds=3600)
value = await redis.get_cache("key")

# Publish event
await redis.publish_event("channel", {"event": "data"})
```

---

## 🔌 API Endpoints Reference

### Authentication
```
POST   /api/auth/signup          # Sign up new customer
POST   /api/auth/login           # Login
POST   /api/auth/logout          # Logout
GET    /api/auth/me              # Get current user
```

### Marketplace
```
GET    /api/marketplace/ves      # List available VEs
GET    /api/marketplace/ves/{id} # Get VE details
POST   /api/marketplace/ves/{id}/hire  # Hire a VE
```

### Virtual Employees
```
GET    /api/ves                  # List hired VEs
GET    /api/ves/{id}             # Get VE details
DELETE /api/ves/{id}             # Remove VE
```

### Tasks
```
GET    /api/tasks                # List tasks
POST   /api/tasks                # Create task
GET    /api/tasks/{id}           # Get task
PUT    /api/tasks/{id}           # Update task
DELETE /api/tasks/{id}           # Delete task
```

### Messages
```
GET    /api/messages             # List messages
POST   /api/messages             # Send message
PUT    /api/messages/{id}/read   # Mark as read
```

### Orchestrator
```
POST   /api/orchestrator/route   # Route task to VE
```

### Billing
```
GET    /api/billing/usage        # Get token usage
GET    /api/billing/usage/breakdown  # Detailed breakdown
GET    /api/billing/subscription # Subscription info
```

### Webhooks (NEW)
```
POST   /api/webhooks/agent-callback   # Agent callbacks
POST   /api/webhooks/token-usage      # Token tracking
GET    /api/webhooks/health           # Health check
```

---

## 🔔 Webhook Event Examples

### Task Update
```json
POST /api/webhooks/agent-callback
{
  "event_type": "task_update",
  "customer_id": "customer-123",
  "task_id": "task-456",
  "status": "completed",
  "result": "Campaign created successfully"
}
```

### Message Send
```json
POST /api/webhooks/agent-callback
{
  "event_type": "message_send",
  "customer_id": "customer-123",
  "from_ve_id": "ve-456",
  "subject": "Campaign Ready",
  "content": "Your marketing campaign is ready for review"
}
```

### Agent Status
```json
POST /api/webhooks/agent-callback
{
  "event_type": "agent_status",
  "customer_ve_id": "ve-456",
  "status": "active"
}
```

### Task Delegation
```json
POST /api/webhooks/agent-callback
{
  "event_type": "delegation",
  "from_agent_id": "ve-manager",
  "to_agent_id": "ve-senior",
  "task_id": "task-456",
  "reason": "Requires specialized expertise"
}
```

---

## 🧪 Testing Commands

### Test Kubernetes
```bash
# Check if K8s is accessible
kubectl cluster-info

# List namespaces
kubectl get namespaces | grep customer-

# List agents in namespace
kubectl get agents -n customer-customer-123
```

### Test Redis
```bash
# Check Redis connection
redis-cli ping

# Monitor queues
redis-cli LLEN ve:tasks:high
redis-cli LLEN ve:tasks:medium
redis-cli LLEN ve:tasks:low
```

### Test API
```bash
# Health check
curl http://localhost:8000/health

# Create task
curl -X POST http://localhost:8000/api/tasks \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Task",
    "description": "Test description",
    "priority": "high"
  }'

# Test webhook
curl -X POST http://localhost:8000/api/webhooks/agent-callback \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "task_update",
    "customer_id": "123",
    "task_id": "456",
    "status": "completed"
  }'
```

---

## 🔧 Configuration Quick Reference

### Required Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://localhost:6379

# Kubernetes
K8S_API_URL=https://your-k8s-cluster:6443
K8S_NAMESPACE_PREFIX=customer-

# Agent Gateway
AGENT_GATEWAY_URL=http://localhost:8081

# Webhooks
WEBHOOK_SECRET=your-secure-secret

# JWT
JWT_SECRET=your-jwt-secret

# LLM (optional)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📊 Monitoring Commands

### Check Worker Status
```bash
# View worker logs
tail -f logs/worker.log

# Check if worker is running
ps aux | grep enhanced_worker
```

### Monitor Queues
```bash
# Queue depths
redis-cli LLEN ve:tasks:urgent
redis-cli LLEN ve:tasks:high
redis-cli LLEN ve:tasks:medium
redis-cli LLEN ve:tasks:low
```

### Check Agent Health
```bash
# List all agents
kubectl get agents --all-namespaces

# Check specific agent
kubectl describe agent marketing-manager -n customer-customer-123

# View agent logs
kubectl logs -n customer-customer-123 -l agent=marketing-manager
```

---

## 🐛 Troubleshooting

### Common Issues

**Issue: Worker not processing tasks**
```bash
# Check Redis connection
redis-cli ping

# Check queue depth
redis-cli LLEN ve:tasks:high

# Restart worker
pkill -f enhanced_worker
python -m app.workers.enhanced_worker
```

**Issue: Agent deployment fails**
```bash
# Check K8s connection
kubectl cluster-info

# Check namespace exists
kubectl get namespace customer-customer-123

# Check agent status
kubectl get agents -n customer-customer-123
```

**Issue: Webhook not working**
```bash
# Check webhook endpoint
curl http://localhost:8000/api/webhooks/health

# Test webhook manually
curl -X POST http://localhost:8000/api/webhooks/agent-callback \
  -H "Content-Type: application/json" \
  -d '{"event_type": "task_update", ...}'
```

---

## 🔐 Security Checklist

- [ ] Set strong `WEBHOOK_SECRET` in production
- [ ] Use HTTPS for all API endpoints
- [ ] Enable K8s RBAC
- [ ] Rotate JWT secrets regularly
- [ ] Enable Redis password authentication
- [ ] Use network policies in K8s
- [ ] Enable API rate limiting
- [ ] Monitor webhook signature failures

---

## 📈 Performance Tips

1. **Use Redis caching** for frequently accessed data
2. **Set appropriate task priorities** for optimal processing
3. **Monitor queue depths** to prevent backlog
4. **Scale workers** based on queue size
5. **Use K8s autoscaling** for agent pods
6. **Enable connection pooling** for database
7. **Implement request caching** for API responses

---

## 🎯 Production Deployment Checklist

- [ ] Set all environment variables
- [ ] Configure Kubernetes cluster
- [ ] Deploy Agent Gateway
- [ ] Set up Redis cluster
- [ ] Configure Supabase project
- [ ] Set up monitoring (Prometheus/Grafana)
- [ ] Configure logging (ELK/CloudWatch)
- [ ] Set up alerting
- [ ] Enable backups
- [ ] Configure SSL/TLS
- [ ] Set up CI/CD pipeline
- [ ] Load test the system

---

## 📞 Support

For issues or questions:
1. Check logs: `tail -f logs/app.log`
2. Review documentation: `BACKEND_IMPLEMENTATION.md`
3. Test services individually
4. Check environment variables

---

**Last Updated:** 2025-11-25
**Version:** 1.0.0
**Status:** Production Ready ✅
