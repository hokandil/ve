# Virtual Employee (VE) SaaS Platform - UPDATED PRD
## Product Requirements Document v2.0 - Simplified Architecture

**Version:** 2.0 (Simplified Architecture with KAgent + Agent Gateway)  
**Date:** November 26, 2025  
**Target:** Development Team  
**Tech Stack:** React + FastAPI + Supabase + KAgent + Agent Gateway

---

## 🎯 MAJOR ARCHITECTURE CHANGE

### Previous Approach (v1.0):
- Build custom agent creation UI
- Build custom MCP server manager
- Build custom tool manager
- Build custom auth/observability
- Implement CrewAI orchestration from scratch

### New Approach (v2.0):
- **Leverage KAgent Dashboard** for agent/tool/MCP creation
- **Leverage Agent Gateway** for auth, observability, A2A protocol
- **Focus on marketplace & billing** (our unique value)

**Result:** 80% less code, faster time to market, production-ready from day 1

---

## 1. Executive Summary

### 1.1 Product Vision
A SaaS marketplace platform where business owners can hire AI-powered Virtual Employees (VEs) with different expertise levels, organized in a hierarchical structure. Platform focuses on **marketplace, billing, and customer experience** while leveraging best-in-class tools for agent runtime.

### 1.2 Core Value Proposition
- **AI Workforce Marketplace**: Curated VE templates with transparent pricing
- **Simple Hiring Flow**: Browse → Hire → Use (no complex configuration)
- **Enterprise-Grade Runtime**: KAgent + Agent Gateway handle execution
- **Transparent Billing**: Token-based pricing with clear usage tracking

### 1.3 Key Differentiators
- **Simplified UX**: No need to understand agents/tools/MCP (handled by KAgent)
- **Marketplace Focus**: Tags, categories, pricing, featured agents
- **Customer Experience**: Chat interface, task management, billing dashboard
- **Production-Ready**: Leveraging CNCF sandbox projects (KAgent) and Solo.io (Agent Gateway)

---

## 2. Simplified Architecture

### 2.1 Technology Stack

**Frontend (User):**
- React 18+ with TypeScript
- TailwindCSS + HeadlessUI
- React Query (Server State)
- Axios (API Client)

**Frontend (Admin):**
- React 18+ with TypeScript
- Simplified to marketplace metadata management
- Connects to KAgent API for agent browsing

**Backend:**
- FastAPI (Python 3.11+)
- Supabase (PostgreSQL + Auth + Storage)
- Redis (Caching/Queues)
- **KAgent Client** (read agents from KAgent API)
- **Agent Gateway Client** (forward requests to agents)

**Agent Runtime (Managed by KAgent):**
- **KAgent Dashboard**: Agent/tool/MCP creation
- **KAgent Runtime**: Kubernetes-based agent execution
- **Google ADK**: Native agent framework

**Gateway Layer (Managed by Agent Gateway):**
- **Authentication**: JWT, MCP auth
- **Authorization**: RBAC, external authz
- **Protocols**: A2A, MCP, HTTP
- **Observability**: Metrics, tracing, logs
- **Traffic Management**: Rate limiting, retries, timeouts

### 2.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  YOUR PLATFORM (What You Build)          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  USER FRONTEND                                   │  │
│  │  ├─ Marketplace (browse VEs with YOUR pricing)   │  │
│  │  ├─ My Team (hired VEs)                         │  │
│  │  ├─ Chat Interface (interact with VEs)          │  │
│  │  ├─ Task Management                             │  │
│  │  └─ Billing Dashboard                           │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ADMIN FRONTEND (Simplified)                     │  │
│  │  ├─ Browse agents from KAgent                   │  │
│  │  ├─ Add marketplace metadata (pricing, tags)    │  │
│  │  └─ Publish to marketplace                      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  BACKEND (Your Business Logic)                   │  │
│  │  ├─ Marketplace metadata service                │  │
│  │  ├─ Customer management                         │  │
│  │  ├─ Billing & usage tracking                    │  │
│  │  ├─ Customer VE instances                       │  │
│  │  ├─ KAgent API client                           │  │
│  │  └─ Agent Gateway client                        │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│              AGENT GATEWAY (agentgateway.dev)           │
│                   (You Configure, Don't Build)          │
├─────────────────────────────────────────────────────────┤
│  🔐 Authentication & Authorization                      │
│  🔌 A2A + MCP Protocol Support                         │
│  📊 Observability (Metrics, Tracing, Logs)             │
│  🛡️ Traffic Management (Rate Limiting, Retries)        │
│  🔍 Discovery & Routing                                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                KAGENT (kagent.dev)                      │
│              (You Use Dashboard, Don't Build)           │
├─────────────────────────────────────────────────────────┤
│  🎨 KAgent Dashboard (Create agents visually)          │
│  ☸️ Kubernetes Integration (Agent CRDs)                │
│  🤖 Agent Runtime (Google ADK)                         │
│  🔧 Tool & MCP Server Management                       │
└─────────────────────────────────────────────────────────┘
```

---

## 3. What You Build vs What You Get

### ✅ What You GET (Leverage Existing Tools)

#### From KAgent (kagent.dev):
- ✅ Agent creation UI (KAgent Dashboard)
- ✅ MCP server management
- ✅ Tool management
- ✅ Agent runtime & execution (Google ADK)
- ✅ Kubernetes deployment (Agent CRDs)
- ✅ Agent testing tools

#### From Agent Gateway (agentgateway.dev):
- ✅ JWT authentication
- ✅ MCP authentication & authorization
- ✅ A2A (Agent-to-Agent) protocol
- ✅ Rate limiting & quotas
- ✅ Observability (metrics, tracing, logs)
- ✅ Token usage tracking (via webhooks)
- ✅ Discovery & routing
- ✅ Retries, timeouts, circuit breaking

### 🛠️ What You BUILD (Your Unique Value)

#### Admin Frontend (Simplified):
1. **Agent Browser**
   - List agents from KAgent API
   - View agent details
   - Test agent in playground

2. **Marketplace Editor**
   - Add pricing (monthly fee, token billing)
   - Add tags, categories, descriptions
   - Upload icon & screenshots
   - Set featured/recommended status
   - Publish to marketplace

#### User Frontend:
1. **Marketplace**
   - Browse VEs with YOUR pricing/tags
   - Search & filter
   - Agent detail pages
   - Hire/subscribe flow

2. **My Team**
   - List hired VEs
   - VE settings & configuration
   - Org chart (optional)

3. **Chat Interface**
   - Interact with VEs via Agent Gateway
   - Message history
   - Real-time responses

4. **Task Management**
   - Create tasks
   - Assign to VEs
   - Track progress

5. **Billing Dashboard**
   - Token usage tracking
   - Monthly invoices
   - Payment management

#### Backend:
1. **Marketplace Service**
   - Store marketplace metadata (pricing, tags, etc.)
   - Publish/unpublish agents
   - Search & filter logic

2. **Customer VE Service**
   - Hire VE (create customer instance)
   - Configure Agent Gateway routing
   - Manage VE access

3. **Billing Service**
   - Track usage from Agent Gateway webhooks
   - Calculate monthly bills
   - Generate invoices

4. **KAgent Client**
   - Fetch agents from KAgent API
   - Get agent details

5. **Agent Gateway Client**
   - Forward customer requests to agents
   - Handle authentication
   - Process webhooks

---

## 4. Database Schema (Simplified)

### 4.1 Core Tables

**marketplace_agents** (Your metadata for KAgent agents)
```sql
- id (UUID, PK)
- agent_name (VARCHAR) -- Reference to KAgent agent
- agent_namespace (VARCHAR) -- KAgent namespace
- pricing_monthly (DECIMAL)
- token_billing (ENUM: customer_pays, included)
- tags (TEXT[])
- category (VARCHAR)
- featured (BOOLEAN)
- status (ENUM: beta, alpha, stable)
- icon_url (VARCHAR)
- screenshots (TEXT[])
- description (TEXT) -- Marketing description
- created_at, updated_at (TIMESTAMP)
```

**customers**
```sql
- id (UUID, PK)
- email (VARCHAR, UNIQUE)
- company_name (VARCHAR)
- created_at (TIMESTAMP)
- subscription_status (VARCHAR)
```

**customer_ves** (Hired VE instances)
```sql
- id (UUID, PK)
- customer_id (UUID, FK → customers)
- marketplace_agent_id (UUID, FK → marketplace_agents)
- agent_name (VARCHAR) -- KAgent agent name
- agent_namespace (VARCHAR) -- Customer's K8s namespace
- persona_name (VARCHAR) -- Custom name given by customer
- hired_at (TIMESTAMP)
- status (VARCHAR)
- agent_gateway_route_id (VARCHAR) -- Route ID in Agent Gateway
```

**messages** (Chat history)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- customer_ve_id (UUID, FK → customer_ves)
- from_type (ENUM: customer, ve)
- content (TEXT)
- created_at (TIMESTAMP)
```

**tasks**
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- title (VARCHAR)
- description (TEXT)
- assigned_to_ve (UUID, FK → customer_ves)
- status (ENUM: pending, in_progress, completed)
- created_at, updated_at (TIMESTAMP)
```

**token_usage** (From Agent Gateway webhooks)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- customer_ve_id (UUID, FK)
- input_tokens (INTEGER)
- output_tokens (INTEGER)
- total_tokens (INTEGER)
- cost (DECIMAL)
- model (VARCHAR)
- timestamp (TIMESTAMP)
```

---

## 5. API Endpoints (Simplified)

### 5.1 Admin API

```
# Agent Browser
GET    /api/admin/kagent/agents          # List from KAgent
GET    /api/admin/kagent/agents/{name}   # Get details from KAgent

# Marketplace Management
GET    /api/admin/marketplace/agents     # List published agents
POST   /api/admin/marketplace/agents     # Add agent to marketplace
PUT    /api/admin/marketplace/agents/{id} # Update metadata
DELETE /api/admin/marketplace/agents/{id} # Unpublish
```

### 5.2 User API

```
# Marketplace
GET    /api/marketplace/agents           # Browse with YOUR metadata
GET    /api/marketplace/agents/{id}      # Agent details
POST   /api/marketplace/agents/{id}/hire # Hire VE

# My VEs
GET    /api/ves                          # List hired VEs
GET    /api/ves/{id}                     # VE details
DELETE /api/ves/{id}                     # Remove VE

# Chat
POST   /api/ves/{id}/chat                # Send message to VE
GET    /api/ves/{id}/messages            # Get message history

# Tasks
GET    /api/tasks                        # List tasks
POST   /api/tasks                        # Create task
PUT    /api/tasks/{id}                   # Update task

# Billing
GET    /api/billing/usage                # Token usage
GET    /api/billing/invoices             # Invoices
```

### 5.3 Webhooks (From Agent Gateway)

```
POST   /api/webhooks/agent-gateway/usage # Token usage tracking
POST   /api/webhooks/agent-gateway/events # Agent events
```

---

## 6. User Flows

### 6.1 Admin: Publish Agent to Marketplace

```
1. Platform Engineer creates agent in KAgent Dashboard
   └─> Agent deployed to K8s as KAgent CRD

2. Admin opens Admin Frontend
   └─> Clicks "Browse KAgent Agents"
   └─> Fetches agents from KAgent API

3. Admin selects agent "customer-success-manager"
   └─> Clicks "Add to Marketplace"

4. Marketplace Editor form:
   - Monthly Fee: $99
   - Token Billing: Customer Pays
   - Tags: ["customer-success", "b2b"]
   - Category: Customer Success
   - Featured: Yes
   - Icon: Upload image
   - Description: Marketing copy

5. Admin clicks "Publish"
   └─> Saved to marketplace_agents table
   └─> Agent appears in user marketplace
```

### 6.2 Customer: Hire VE

```
1. Customer browses marketplace
   └─> Sees agents with YOUR pricing/tags

2. Customer clicks on "Customer Success Manager"
   └─> Views details, pricing, capabilities

3. Customer clicks "Hire"
   └─> POST /api/marketplace/agents/{id}/hire

4. Backend:
   a) Creates customer_ves record
   b) Configures Agent Gateway:
      - Create route: customer → agent
      - Set up JWT auth
      - Configure rate limits
   c) Returns VE details

5. Customer sees VE in "My Team"
```

### 6.3 Customer: Chat with VE

```
1. Customer opens chat with VE
   └─> Sends message: "Create a marketing campaign for our new product"

2. Frontend:
   └─> POST /api/ves/{ve_id}/chat
   └─> Headers: Authorization: Bearer <customer_jwt>

3. Backend:
   a) Validates customer owns this VE
   b) Forwards to Agent Gateway:
      POST https://agent-gateway/a2a/invoke
      Headers:
        - Authorization: Bearer <customer_jwt>
        - X-Customer-ID: customer-123
        - X-VE-ID: ve-456

4. Agent Gateway:
   ✅ Validates JWT
   ✅ Checks authorization
   ✅ Routes to KAgent agent
   ✅ Tracks token usage
   ✅ Logs request

5. KAgent executes agent
   └─> Uses tools via MCP
   └─> Returns response

6. Agent Gateway:
   └─> Sends webhook to backend with token usage
   └─> POST /api/webhooks/agent-gateway/usage

7. Backend:
   a) Stores token usage in database
   b) Returns response to customer

8. Customer sees response in chat
```

---

## 7. Implementation Phases

### Phase 1: Setup & Integration (Week 1)
**Goal:** Deploy KAgent + Agent Gateway, verify connectivity

**Backend:**
- [ ] Deploy KAgent to Kubernetes
- [ ] Deploy Agent Gateway to Kubernetes
- [ ] Create KAgent API client
- [ ] Create Agent Gateway client
- [ ] Test end-to-end: Create agent in KAgent → Call via Agent Gateway

**Admin Frontend:**
- [ ] Setup project structure
- [ ] Create KAgent API client
- [ ] Build agent browser component

**User Frontend:**
- [ ] Setup project structure
- [ ] Create basic layout

### Phase 2: Marketplace (Week 2)
**Goal:** Admin can publish agents, users can browse

**Backend:**
- [ ] Create marketplace_agents table
- [ ] Implement marketplace API endpoints
- [ ] Build marketplace service

**Admin Frontend:**
- [ ] Build marketplace editor form
- [ ] Implement publish flow
- [ ] Add icon/screenshot upload

**User Frontend:**
- [ ] Build marketplace browse page
- [ ] Implement search & filter
- [ ] Create agent detail page

### Phase 3: Hiring & Chat (Week 3)
**Goal:** Customers can hire VEs and chat with them

**Backend:**
- [ ] Create customer_ves table
- [ ] Implement hire VE endpoint
- [ ] Configure Agent Gateway routing on hire
- [ ] Implement chat endpoint (forward to Agent Gateway)
- [ ] Create webhook handler for token usage

**User Frontend:**
- [ ] Build hire flow
- [ ] Create "My Team" page
- [ ] Build chat interface
- [ ] Implement real-time message updates

### Phase 4: Tasks & Billing (Week 4)
**Goal:** Task management and billing dashboard

**Backend:**
- [ ] Create tasks table
- [ ] Create token_usage table
- [ ] Implement task API endpoints
- [ ] Implement billing API endpoints
- [ ] Build billing calculation logic

**User Frontend:**
- [ ] Build task management page
- [ ] Create billing dashboard
- [ ] Implement usage charts

### Phase 5: Polish & Production (Week 5-6)
**Goal:** Production-ready platform

**All:**
- [ ] Security hardening
- [ ] Performance optimization
- [ ] Error handling
- [ ] Documentation
- [ ] Testing
- [ ] Deployment

---

## 8. Technical Specifications

### 8.1 KAgent Integration

**API Endpoints (KAgent):**
```
GET    https://kagent-api/v1alpha2/agents
GET    https://kagent-api/v1alpha2/agents/{name}
GET    https://kagent-api/v1alpha2/agents/{name}/status
```

**Agent CRD Format:**
```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: customer-success-manager
  namespace: default
spec:
  type: Declarative
  declarative:
    modelConfig: default-model-config
    systemMessage: |
      You are a customer success manager...
  tools:
    - type: McpServer
      mcpServer:
        apiGroup: kagent.dev
        kind: RemoteMCPServer
        name: kagent-tool-server
      toolNames:
        - company_rag
        - customer_db
```

### 8.2 Agent Gateway Integration

**Configuration:**
```yaml
apiVersion: agentgateway.dev/v1
kind: Route
metadata:
  name: customer-123-ve-456
spec:
  match:
    headers:
      - name: X-Customer-ID
        value: "123"
      - name: X-VE-ID
        value: "456"
  backend:
    namespace: customer-123
    agent: customer-success-manager
  auth:
    jwt:
      issuer: your-platform.com
      audience: agent-gateway
  rateLimit:
    requests: 100
    period: 1m
  webhooks:
    - url: https://your-backend.com/api/webhooks/agent-gateway/usage
      events: [token_usage]
```

**API Calls:**
```python
# Forward customer request to agent
response = await agent_gateway_client.invoke_agent(
    customer_id="123",
    ve_id="456",
    message="Create a marketing campaign",
    jwt=customer_jwt
)

# Response includes:
# - agent_response: str
# - token_usage: {input: int, output: int, total: int}
# - latency_ms: int
```

---

## 9. Non-Functional Requirements

### 9.1 Performance
- Page load: < 2s
- API response: < 500ms (excluding agent calls)
- Agent response: < 30s
- Real-time updates: < 1s latency

### 9.2 Security
- All traffic over HTTPS
- JWT authentication (Supabase Auth)
- Agent Gateway handles A2A auth
- Row-Level Security in Supabase
- Input validation on all endpoints

### 9.3 Scalability
- Support 10,000+ customers
- 100,000+ VE instances
- Kubernetes horizontal autoscaling
- Agent Gateway load balancing

### 9.4 Observability
- Agent Gateway metrics (Prometheus)
- Error tracking (Sentry)
- Request tracing (OpenTelemetry via Agent Gateway)
- Token usage tracking

---

## 10. Success Metrics

### 10.1 Platform Metrics
- Number of published agents
- Number of customers
- Number of hired VEs
- Total token usage
- Revenue (MRR)

### 10.2 User Metrics
- Time to first VE hire
- Average VEs per customer
- Chat messages per day
- Task completion rate
- Customer retention rate

---

## 11. Risks & Mitigations

### 11.1 Dependency on External Tools

**Risk:** KAgent or Agent Gateway issues affect platform  
**Mitigation:**
- Use stable versions
- Monitor health endpoints
- Have fallback mechanisms
- Maintain good relationship with Solo.io

### 11.2 Token Cost Management

**Risk:** Unexpected high token usage  
**Mitigation:**
- Set rate limits in Agent Gateway
- Monitor usage in real-time
- Alert on anomalies
- Customer quotas

### 11.3 Agent Quality

**Risk:** Poor agent responses affect customer experience  
**Mitigation:**
- Test agents thoroughly before publishing
- Collect customer feedback
- Iterate on agent prompts
- Version control for agents

---

## 12. Future Enhancements

### 12.1 Phase 2 Features
- Org chart builder (hierarchical VEs)
- VE-to-VE delegation
- Advanced task workflows
- Team collaboration features

### 12.2 Phase 3 Features
- Custom agent creation (via KAgent Dashboard)
- Agent marketplace (user-created agents)
- Integration marketplace (Slack, email, etc.)
- Advanced analytics

---

**Status:** ✅ READY FOR IMPLEMENTATION  
**Architecture:** Simplified with KAgent + Agent Gateway  
**Estimated Timeline:** 5-6 weeks to MVP
