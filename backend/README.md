# VE SaaS Platform - Backend

Production-ready FastAPI backend for the Virtual Employee SaaS Platform.

## 🚀 Features

### Core Functionality
- ✅ **REST API** - Complete API for all platform operations
- ✅ **Authentication** - Supabase Auth with JWT tokens
- ✅ **VE Marketplace** - Browse and hire virtual employees
- ✅ **Task Management** - Create, assign, and track tasks
- ✅ **Messaging System** - Email-like communication with VEs
- ✅ **Billing & Token Tracking** - Comprehensive usage tracking

### Advanced Features (NEW)
- ✅ **Kubernetes Integration** - Deploy and manage VEs on K8s
- ✅ **Agent Gateway** - A2A protocol for agent communication
- ✅ **Redis Queues** - Priority-based background processing
- ✅ **Webhook System** - Agent callbacks and event handling
- ✅ **Enhanced Worker** - Production-grade task processor
- ✅ **Health Monitoring** - Agent and system health checks

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/                    # API endpoints
│   │   ├── auth.py
│   │   ├── billing.py
│   │   ├── customers.py
│   │   ├── marketplace.py
│   │   ├── messages.py
│   │   ├── orchestrator.py
│   │   ├── org_chart.py
│   │   ├── tasks.py
│   │   ├── ves.py
│   │   └── webhooks.py         # NEW
│   │
│   ├── core/                   # Core functionality
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── services/               # Business logic
│   │   ├── agent_gateway_service.py    # NEW
│   │   ├── kubernetes_service.py       # NEW
│   │   ├── redis_queue_service.py      # NEW
│   │   ├── message_service.py
│   │   ├── orchestrator.py
│   │   ├── task_service.py
│   │   └── ve_deployment.py
│   │
│   ├── workers/                # Background workers
│   │   ├── enhanced_worker.py  # NEW
│   │   └── task_worker.py
│   │
│   ├── main.py                 # Application entry
│   └── schemas.py              # Pydantic models
│
├── requirements.txt
├── Dockerfile
├── BACKEND_IMPLEMENTATION.md   # Detailed docs
└── QUICK_REFERENCE.md          # Quick guide
```

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (via Supabase)
- Redis
- Kubernetes cluster (optional for development)

### Setup

1. **Clone and navigate:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Environment variables:**
```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# Database
DATABASE_URL=postgresql://...

# Redis
REDIS_URL=redis://localhost:6379

# Kubernetes (optional)
K8S_API_URL=https://your-k8s-cluster:6443
K8S_NAMESPACE_PREFIX=customer-

# Agent Gateway (optional)
AGENT_GATEWAY_URL=http://localhost:8081

# Security
JWT_SECRET=your-secret-key
WEBHOOK_SECRET=your-webhook-secret
```

## 🚀 Running

### Development

**Start API server:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Start background worker:**
```bash
# In a separate terminal
python -m app.workers.enhanced_worker
```

**Access API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health: http://localhost:8000/health

### Production

**Using Gunicorn:**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Using Docker:**
```bash
docker build -t ve-backend .
docker run -p 8000:8000 --env-file .env ve-backend
```

**Using Docker Compose:**
```bash
# From project root
docker-compose up -d
```

## 📚 API Documentation

### Authentication
```
POST   /api/auth/signup
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
```

### Marketplace
```
GET    /api/marketplace/ves
GET    /api/marketplace/ves/{id}
POST   /api/marketplace/ves/{id}/hire
```

### Tasks
```
GET    /api/tasks
POST   /api/tasks
GET    /api/tasks/{id}
PUT    /api/tasks/{id}
DELETE /api/tasks/{id}
```

### Webhooks (NEW)
```
POST   /api/webhooks/agent-callback
POST   /api/webhooks/token-usage
GET    /api/webhooks/health
```

For complete API documentation, see `/docs` endpoint or `BACKEND_IMPLEMENTATION.md`.

## 🔧 Services

### 1. Kubernetes Service
Manages VE deployment to Kubernetes cluster.

```python
from app.services.kubernetes_service import get_kubernetes_service

k8s = get_kubernetes_service()
await k8s.create_customer_namespace("customer-123")
await k8s.deploy_agent(namespace, agent_name, manifest)
```

### 2. Agent Gateway Service
Handles A2A protocol communication with agents.

```python
from app.services.agent_gateway_service import get_agent_gateway_service

gateway = get_agent_gateway_service()
response = await gateway.invoke_agent(namespace, agent_name, request_data, customer_id)
```

### 3. Redis Queue Service
Manages background task processing with priority queues.

```python
from app.services.redis_queue_service import get_redis_queue_service

redis = await get_redis_queue_service()
await redis.enqueue_task(task_id, customer_id, task_data, priority="high")
```

## 🧪 Testing

### Run Tests
```bash
pytest
```

### Test Individual Services
```bash
# Test Kubernetes
python -c "from app.services.kubernetes_service import get_kubernetes_service; import asyncio; asyncio.run(get_kubernetes_service().create_customer_namespace('test'))"

# Test Redis
redis-cli ping

# Test API
curl http://localhost:8000/health
```

## 📊 Monitoring

### Health Checks
```bash
# API health
curl http://localhost:8000/health

# Webhook health
curl http://localhost:8000/api/webhooks/health
```

### Queue Monitoring
```bash
# Check queue depths
redis-cli LLEN ve:tasks:high
redis-cli LLEN ve:tasks:medium
redis-cli LLEN ve:tasks:low
```

### Agent Monitoring
```bash
# List agents
kubectl get agents --all-namespaces

# Check agent status
kubectl describe agent <name> -n <namespace>
```

## 🔐 Security

- JWT-based authentication
- Webhook HMAC signature verification
- Kubernetes RBAC
- Namespace isolation per customer
- Input validation with Pydantic
- Environment-based configuration

## 📖 Documentation

- **BACKEND_IMPLEMENTATION.md** - Comprehensive implementation guide
- **QUICK_REFERENCE.md** - Quick reference for common tasks
- **BACKEND_TASKS_COMPLETE.md** - Summary of all completed tasks
- **/docs** - Interactive API documentation (Swagger)
- **/redoc** - Alternative API documentation (ReDoc)

## 🐛 Troubleshooting

### Worker not processing tasks
```bash
# Check Redis
redis-cli ping

# Check queue
redis-cli LLEN ve:tasks:high

# Restart worker
python -m app.workers.enhanced_worker
```

### Agent deployment fails
```bash
# Check K8s connection
kubectl cluster-info

# Check namespace
kubectl get namespace customer-<id>

# Check logs
kubectl logs -n <namespace> <pod>
```

### Webhook issues
```bash
# Test webhook
curl -X POST http://localhost:8000/api/webhooks/agent-callback \
  -H "Content-Type: application/json" \
  -d '{"event_type": "task_update", "customer_id": "123", "task_id": "456", "status": "completed"}'
```

## 🚀 Deployment

### Production Checklist
- [ ] Set all environment variables
- [ ] Configure Kubernetes cluster
- [ ] Deploy Agent Gateway
- [ ] Set up Redis cluster
- [ ] Configure Supabase
- [ ] Enable monitoring
- [ ] Set up logging
- [ ] Configure SSL/TLS
- [ ] Enable backups
- [ ] Load test

### Scaling
- **API:** Use multiple Gunicorn workers
- **Worker:** Run multiple worker instances
- **Redis:** Use Redis Cluster
- **K8s:** Enable horizontal pod autoscaling

## 📝 Development

### Adding a New Endpoint
1. Create route in `app/api/`
2. Add schema in `app/schemas.py`
3. Implement business logic in `app/services/`
4. Update tests
5. Update documentation

### Adding a New Service
1. Create service in `app/services/`
2. Add configuration in `app/core/config.py`
3. Update dependencies in `requirements.txt`
4. Add tests
5. Update documentation

## 🤝 Contributing

1. Follow existing code structure
2. Add type hints
3. Write tests
4. Update documentation
5. Use meaningful commit messages

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Support

- Documentation: See `BACKEND_IMPLEMENTATION.md`
- Quick Reference: See `QUICK_REFERENCE.md`
- API Docs: http://localhost:8000/docs
- Issues: Check logs in `logs/` directory

---

**Version:** 1.0.0  
**Status:** Production Ready ✅  
**Last Updated:** 2025-11-25
