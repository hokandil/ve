# VE SaaS Platform

**AI-Powered Virtual Employee Platform** - Hire, manage, and collaborate with AI agents in a multi-tenant SaaS environment.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL (via Supabase)
- Kubernetes cluster (for agent deployment)

### Local Development

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev  # Runs on http://localhost:5173
```

3. **Admin Frontend Setup**
```bash
cd admin-frontend
npm install
npm run dev  # Runs on http://localhost:5174
```

### Environment Variables

Copy `.env.example` to `.env` and configure:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key
- `JWT_SECRET` - Secret for JWT token signing
- `AGENT_GATEWAY_URL` - Agent Gateway endpoint (optional for local dev)

---

## 📚 Documentation

### Current Documentation
- **[User Scenario](docs/current/ve-saas-user-scenario.md)** - Detailed user journeys and use cases
- **[Quick Start Guide](docs/current/QUICK_START_NO_DOCKER.md)** - Setup without Docker

### Architecture & Planning
See [Artifacts Directory](C:\Users\hokandil\.gemini\antigravity\brain\b8447ca4-298a-4d78-aff8-2325487b4898) for:
- `architecture_decision.md` - Shared agent runtime architecture
- `security_isolation_plan.md` - 5-layer security strategy
- `task.md` - Current implementation progress
- `walkthrough.md` - Latest implementation walkthrough

### Archived Documentation
Historical documentation moved to `docs/archive/`

---

## 🏗️ Architecture

### Current Architecture (Shared Agent Runtime)

```
┌─────────────────────────────────────────────────────────┐
│  Customer Frontend (React)                              │
│  - Marketplace (hire agents)                            │
│  - My Team (manage hired agents)                        │
│  - Chat Interface (communicate with agents)             │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Backend API (FastAPI)                                  │
│  - Authentication (Supabase Auth)                       │
│  - Customer VE Management                               │
│  - Context Enforcement Middleware ✅                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Agent Gateway (kgateway)                               │
│  - Routes requests to agents                            │
│  - Injects customer context                             │
│  - JWT authentication                                   │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  Shared Agent Runtime (KAgent)                          │
│  - Agents deployed once in `agents-system` namespace    │
│  - Context-based isolation (customer_id)                │
│  - Scoped memory per customer ✅                        │
│  - Multi-agent collaboration                            │
└─────────────────────────────────────────────────────────┘
```

**Key Security Features:**
- ✅ Immutable `AgentContext` (Phase 1 complete)
- ✅ Enforced memory scoping by customer
- ✅ Context validation middleware
- ⏳ Database RLS (Phase 2)
- ⏳ Runtime leakage detection (Phase 4)

---

## 🗂️ Project Structure

```
VE/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── agents/         # ✅ Agent framework (Phase 1)
│   │   ├── api/            # API routes
│   │   ├── core/           # Config, database, security
│   │   ├── middleware/     # ✅ Context enforcement
│   │   ├── schemas/        # Pydantic models
│   │   └── services/       # Business logic
│   ├── migrations/         # Database migrations
│   └── tests/
│       └── security/       # ✅ Security isolation tests
├── frontend/               # Customer React app
├── admin-frontend/         # Admin React app
├── docs/
│   ├── current/           # Active documentation
│   └── archive/           # Historical docs
└── supabase/              # Database schema
```

---

## 🧪 Testing

### Run Security Tests
```bash
cd backend
pytest tests/security/test_context_isolation.py -v -m security
```

**Current Status:** ✅ 2/2 critical security tests passing

### Run All Tests
```bash
cd backend
pytest tests/ -v
```

---

## 🔐 Security

### Multi-Tenant Isolation

The platform uses a **5-layer defense strategy** to prevent customer data leakage:

1. **Context Enforcement Middleware** - Validates customer_id on all requests
2. **Framework-Level Scoping** - Agents require immutable `AgentContext`
3. **Database RLS** - Row-level security (Phase 2)
4. **Runtime Monitoring** - Leakage detection (Phase 4)
5. **Security Testing** - Comprehensive test suite

See [`security_isolation_plan.md`](C:\Users\hokandil\.gemini\antigravity\brain\b8447ca4-298a-4d78-aff8-2325487b4898\security_isolation_plan.md) for details.

---

## 📝 Development Status

**Current Phase:** Security Isolation - Phase 1 ✅ Complete

**Next:** Phase 2 - Database Security (RLS implementation)

See [`task.md`](C:\Users\hokandil\.gemini\antigravity\brain\b8447ca4-298a-4d78-aff8-2325487b4898\task.md) for detailed progress.

---

## 🤝 Contributing

This is a private project. For questions or issues, contact the development team.

---

## 📄 License

Proprietary - All rights reserved
