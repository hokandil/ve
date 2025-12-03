# VE SaaS Platform - Architecture Quick Reference
## Post Agent Gateway Integration

---

## 🏗️ System Architecture

### High-Level Overview
```
Customer → Frontend → Backend API → Agent Gateway → KAgent Agents
                          ↓
                      Supabase DB
```

### Detailed Flow
```
┌─────────────────────────────────────────────────────────────┐
│                    CUSTOMER LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Customer Frontend (React)                                   │
│  - Marketplace (browse/hire agents)                          │
│  - My Team (manage hired agents)                             │
│  - Chat (interact with agents)                               │
│  - Tasks, Billing, Org Chart                                 │
│  Port: 3001                                                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────┴────────────────────────────────────────┐
│                    ADMIN LAYER                               │
├─────────────────────────────────────────────────────────────┤
│  Admin Frontend (React)                                      │
│  - VE Creator Wizard (6-step agent creation)                 │
│  - Agent Browser (discover from KAgent)                      │
│  - Marketplace Editor (pricing, metadata)                    │
│  - Agent Management (delete, monitor)                        │
│  Port: 3000                                                  │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/REST
┌────────────────────┴────────────────────────────────────────┐
│                    BACKEND API LAYER                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Backend                                             │
│  Port: 8000                                                  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  API Endpoints:                                       │  │
│  │  - /api/auth/* (signup, login, logout)               │  │
│  │  - /api/marketplace/* (browse, hire)                 │  │
│  │  - /api/customer/ves/* (my team, unhire)             │  │
│  │  - /api/messages/* (chat)                            │  │
│  │  - /api/discovery/* (import, delete agents)          │  │
│  │  - /api/tasks/* (task management)                    │  │
│  │  - /api/billing/* (usage, invoices)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Services:                                            │  │
│  │  - gateway_config_service (RBAC management)           │  │
│  │  - agent_gateway_service (A2A protocol)               │  │
│  │  - kagent_service (agent discovery)                   │  │
│  │  - marketplace_service (agent catalog)                │  │
│  │  - customer_ve_service (hire/unhire)                  │  │
│  │  - message_service (chat history)                     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────┬────────────────────────────┬────────────────────────┘
         │                            │
         │                            │
┌────────┴──────┐            ┌────────┴──────────────────────┐
│   Supabase    │            │    Agent Gateway (kgateway)   │
│   Database    │            │    Port: 8080 (port-forward)  │
│               │            │                               │
│  Tables:      │            │  ┌─────────────────────────┐  │
│  - customers  │            │  │  TrafficPolicy (RBAC)   │  │
│  - virtual_   │            │  │  - CEL expressions      │  │
│    employees  │            │  │  - Customer allow-list  │  │
│  - customer_  │            │  │  - Deny by default      │  │
│    ves        │            │  └─────────────────────────┘  │
│  - messages   │            │                               │
│  - tasks      │            │  ┌─────────────────────────┐  │
│  - token_     │            │  │  HTTPRoute (Routing)    │  │
│    usage      │            │  │  - Hostname-based       │  │
│               │            │  │  - {agent}.local        │  │
│  Features:    │            │  │  - Backend refs         │  │
│  - Auth       │            │  └─────────────────────────┘  │
│  - RLS        │            │                               │
│  - Storage    │            │  Protocol: A2A (Agent-to-     │
│               │            │  Agent) with JSON-RPC 2.0     │
└───────────────┘            └────────┬──────────────────────┘
                                      │
                             ┌────────┴──────────────────────┐
                             │   KAgent Agents (Kubernetes)  │
                             │                               │
                             │  Deployed Agents:             │
                             │  - wellness.default           │
                             │  - agent-two.default          │
                             │  - ...                        │
                             │                               │
                             │  Each agent:                  │
                             │  - Service (ClusterIP)        │
                             │  - Deployment                 │
                             │  - Agent CRD (v1alpha2)       │
                             └───────────────────────────────┘
```

---

## 🔐 Security Architecture (RBAC)

### TrafficPolicy Lifecycle

```
1. AGENT IMPORT (Admin)
   ├─> Create HTTPRoute (agent-{name})
   └─> Create TrafficPolicy (rbac-{name})
       └─> CEL: request.headers['X-Customer-ID'] == 'deny-all-default'
       └─> allowed_customers: []

2. CUSTOMER HIRES
   └─> Update TrafficPolicy
       └─> CEL: request.headers['X-Customer-ID'] in ['customer-uuid']
       └─> allowed_customers: ['customer-uuid']

3. SECOND CUSTOMER HIRES
   └─> Update TrafficPolicy
       └─> CEL: request.headers['X-Customer-ID'] in ['uuid1', 'uuid2']
       └─> allowed_customers: ['uuid1', 'uuid2']

4. CUSTOMER UNHIRES
   └─> Update TrafficPolicy
       └─> Remove customer from list
       └─> If empty: revert to deny-all (don't delete)

5. AGENT DELETE (Admin)
   ├─> Delete TrafficPolicy
   └─> Delete HTTPRoute
```

### Request Flow with RBAC

```
Customer Chat Request
    ↓
Backend receives request with customer JWT
    ↓
Extract customer_id from JWT
    ↓
Add X-Customer-ID header to request
    ↓
Forward to Agent Gateway (Host: {agent}.local)
    ↓
Agent Gateway checks TrafficPolicy
    ├─> CEL expression evaluates X-Customer-ID
    ├─> If in allowed list → ALLOW (200)
    └─> If not in list → DENY (403)
    ↓
If allowed: Route to KAgent agent
    ↓
Agent processes request (A2A protocol)
    ↓
Response streamed back via SSE
```

---

## 📡 Communication Protocols

### A2A (Agent-to-Agent) Protocol

**Method:** `message/stream`  
**Transport:** Server-Sent Events (SSE)  
**Format:** JSON-RPC 2.0

**Request Example:**
```json
{
  "jsonrpc": "2.0",
  "method": "message/stream",
  "params": {
    "message": {
      "kind": "message",
      "messageId": "msg-123",
      "role": "user",
      "parts": [
        {
          "kind": "text",
          "text": "Hello, how can you help me?"
        }
      ],
      "contextId": "ctx-customer-123",
      "metadata": {
        "displaySource": "user"
      }
    },
    "metadata": {}
  },
  "id": "req-customer-123"
}
```

**Response (SSE Stream):**
```
data: {"result":{"status":{"message":{"role":"agent","parts":[{"kind":"text","text":"I can help you with..."}]}}}}

data: {"result":{"final":true}}
```

---

## 🗄️ Database Schema

### Key Tables

**customers**
- `id` (UUID, PK)
- `email`, `company_name`
- `created_at`, `updated_at`

**virtual_employees** (Marketplace Agents)
- `id` (UUID, PK)
- `name`, `role`, `department`, `seniority_level`
- `description`, `pricing_monthly`
- `source` ('kagent'), `source_id` (agent name)
- `kagent_namespace`, `kagent_version`
- `status` ('stable', 'beta', 'deprecated')

**customer_ves** (Hired Agents)
- `id` (UUID, PK)
- `customer_id` (FK → customers)
- `marketplace_agent_id` (FK → virtual_employees)
- `agent_type` (agent name for routing)
- `agent_gateway_route` (route path)
- `persona_name`, `persona_email`
- `status` ('active', 'paused')
- `hired_at`

**messages**
- `id` (UUID, PK)
- `customer_id` (FK → customers)
- `from_ve_id`, `to_ve_id` (FK → customer_ves)
- `content`, `from_type` ('customer', 've')
- `thread_id`, `created_at`

**token_usage**
- `id` (UUID, PK)
- `customer_id` (FK → customers)
- `ve_id` (FK → customer_ves)
- `prompt_tokens`, `completion_tokens`, `total_tokens`
- `cost_usd`, `created_at`

---

## 🔧 Key Services

### gateway_config_service.py
**Purpose:** Manage Agent Gateway RBAC  
**Methods:**
- `create_agent_route(agent_type)` - Create HTTPRoute + deny-all TrafficPolicy
- `grant_customer_access(agent_type, customer_id)` - Add customer to allow-list
- `revoke_customer_access(agent_type, customer_id)` - Remove customer, revert to deny-all
- `delete_agent_route(agent_type)` - Delete HTTPRoute + TrafficPolicy

### agent_gateway_service.py
**Purpose:** Communicate with agents via Agent Gateway  
**Methods:**
- `invoke_agent(customer_id, agent_type, message)` - Send message, get response
- Uses A2A protocol with SSE
- Adds `X-Customer-ID` header for RBAC
- Parses SSE events for streaming responses

### kagent_service.py
**Purpose:** Discover and manage KAgent agents  
**Methods:**
- `list_agents(namespace)` - List available agents
- `get_agent(agent_id, namespace)` - Get agent details

---

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/signup` - Create account
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Marketplace (Customer)
- `GET /api/marketplace/ves` - Browse agents
- `GET /api/marketplace/ves/{id}` - Agent details

### Customer VEs
- `POST /api/customer/ves` - Hire agent
- `GET /api/customer/ves` - List hired agents
- `DELETE /api/customer/ves/{id}` - Unhire agent

### Messages (Chat)
- `POST /api/messages/ves/{id}/chat` - Send message
- `GET /api/messages/ves/{id}/history` - Get history

### Discovery (Admin)
- `GET /api/discovery/agents` - List KAgent agents
- `POST /api/discovery/import/agent/{id}` - Import to marketplace
- `DELETE /api/discovery/agents/{id}` - Delete agent

---

## 🚀 Deployment

### Development
```bash
# Backend
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Customer Frontend
cd frontend
npm start  # Port 3001

# Admin Frontend
cd admin-frontend
npm start  # Port 3000

# Port Forwards (Kubernetes)
kubectl port-forward svc/agent-gateway -n kgateway-system 8080:8080
kubectl port-forward svc/kagent-ui -n kagent 8082:8080
kubectl port-forward svc/kagent-controller -n kagent 8083:8083
```

### Environment Variables
```bash
# Backend (.env)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
SUPABASE_SERVICE_KEY=xxx
ENVIRONMENT=development  # or production
```

---

## 📊 Current Status

### ✅ Completed
- Backend API (all endpoints)
- Customer Frontend (marketplace, team, chat)
- Admin Frontend (VE creator, agent browser)
- Agent Gateway RBAC (core implementation)
- Database schema with RLS
- Authentication with Supabase

### 🟡 In Progress
- Multi-customer RBAC testing
- Delete agent protection
- Admin delete UI
- Automated tests

### ⏳ Planned
- SSE streaming chat
- KAgent deployment
- Agent health monitoring
- Production deployment

---

**Last Updated:** November 30, 2025  
**Architecture Version:** 3.0 (Agent Gateway Native)
