# Virtual Employee (VE) SaaS Platform
## Complete Product Requirements Document for Development

**Version:** 1.1 (Deep Dive Update)
**Date:** November 2025
**Target:** Development Team (Antigravity or similar)
**Tech Stack:** React + FastAPI + Supabase + Kubernetes + CrewAI

---

## 1. Executive Summary

### 1.1 Product Vision
A SaaS marketplace platform where business owners can build and manage their own virtual companies by hiring AI-powered Virtual Employees (VEs) with different expertise levels, organized in a hierarchical structure that mimics real business organizations.

### 1.2 Core Value Proposition
- **AI Workforce as a Service**: Scale business operations without traditional hiring constraints
- **Hierarchical Organization**: Manager → Senior → Junior levels with appropriate capabilities
- **Real Company Experience**: VEs with human personas, email-like communication, Kanban task management
- **Token-Based Billing**: Transparent, pay-per-use pricing model

### 1.3 Key Differentiators
- Multi-agent collaboration with real decision-making (not rigid workflows)
- Namespace-isolated per-customer architecture for security
- Visual org chart builder with drag-and-drop
- Kanban board + Email-like interface for natural task delegation
- Production-grade orchestration with KAgent + Agent Gateway

---

## 2. Architecture Overview

### 2.1 Technology Stack

**Frontend:**
- **Framework**: React 18+ with TypeScript
- **Build Tool**: Vite (recommended for new features) / Create React App (Legacy)
- **Styling**: TailwindCSS + HeadlessUI/RadixUI for accessible components
- **State Management**: React Query (Server State) + Zustand (Client State)
- **Visualization**: ReactFlow (Org Chart)
- **Task Management**: @hello-pangea/dnd (Kanban)
- **API Client**: Axios with Interceptors

**Backend:**
- **API Framework**: FastAPI (Python 3.11+)
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth (JWT)
- **Storage**: Supabase Storage (S3 compatible)
- **Vector DB**: Supabase pgvector
- **Caching/Queues**: Redis

**AI/Agent Runtime (The "Brain"):**
- **Orchestration**: CrewAI (Multi-agent delegation)
- **Runtime**: Kubernetes (K3s) with per-customer namespaces
- **Gateway**: Solo.io / Traefik for A2A (Agent-to-Agent) communication
- **Tooling**: MCP (Model Context Protocol) servers

### 2.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│  ├─ Dashboard                                           │
│  ├─ VE Marketplace                                      │
│  ├─ Org Chart Builder (ReactFlow)                      │
│  ├─ Kanban Board                                        │
│  └─ Email-like Interface                               │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTPS
┌─────────────────────────────────────────────────────────┐
│              FastAPI Backend (Agent Gateway)             │
│  ├─ Authentication & Authorization (Supabase)          │
│  ├─ Customer Management API                            │
│  ├─ VE Marketplace API                                 │
│  ├─ Task & Message API                                 │
│  ├─ Billing & Token Tracking                           │
│  └─ Orchestrator Interface                             │
└─────────────────────────────────────────────────────────┘
                          ↓ A2A Protocol
┌─────────────────────────────────────────────────────────┐
│            Agent Gateway (Solo.io MCP + A2A)            │
│  ├─ MCP Protocol (VE ↔ Tools)                          │
│  ├─ A2A Protocol (VE ↔ VE, Orchestrator ↔ VE)         │
│  ├─ JWT/OBO Token Management                           │
│  ├─ OpenTelemetry Tracing                             │
│  └─ Policy Enforcement & Guardrails                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│         KAgent Runtime (Kubernetes)                      │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Namespace: customer-123                        │   │
│  │  ├─ Shared Orchestrator (Routes requests)      │   │
│  │  ├─ Marketing Manager VE (CrewAI Agent)        │   │
│  │  ├─ Marketing Senior VE (CrewAI Agent)         │   │
│  │  └─ Marketing Junior VE (CrewAI Agent)         │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Namespace: customer-456                        │   │
│  │  ├─ Shared Orchestrator                        │   │
│  │  └─ Support Junior VE                          │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          ↓ MCP
┌─────────────────────────────────────────────────────────┐
│                  Tools & Resources                       │
│  ├─ Supabase (RAG + Vector Search)                     │
│  ├─ Database Queries (via MCP)                         │
│  ├─ External APIs (via MCP)                            │
│  └─ Custom Tools                                        │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Feature Requirements

### 3.1 Design System & Shared Components
**Goal**: Create a cohesive, premium "SaaS" feel.
- **Typography**: Inter / Plus Jakarta Sans
- **Color Palette**: 
  - Primary: Indigo/Violet (SaaS standard)
  - Secondary: Slate/Gray (Neutral)
  - Semantic: Green (Success), Red (Error), Amber (Warning)
- **Core Components**:
  - `Button` (Primary, Secondary, Ghost, Destructive)
  - `Input` / `Textarea` / `Select` (with validation states)
  - `Modal` / `Dialog` (for creation flows)
  - `Card` (for VEs, Tasks)
  - `Badge` (Status indicators)
  - `Avatar` (VE personas)
  - `Toast` (Notifications)

### 3.2 Agent Runtime & Orchestration
**Goal**: The actual execution engine for VEs.
- **Agent Definition**: Each VE role (e.g., "Marketing Manager") maps to a CrewAI agent definition (YAML/Python).
- **Task Routing**:
  1. User creates task in Frontend.
  2. Backend saves to DB (`pending`).
  3. Backend pushes to Redis Queue.
  4. Worker picks up task -> Calls Agent Gateway.
  5. Agent Gateway routes to specific Customer Namespace -> Orchestrator Agent.
  6. Orchestrator Agent delegates to specific VE Agent.
  7. VE Agent executes (using MCP tools) -> Updates DB status.
---

## 3. Database Schema

### 3.1 Core Tables (Supabase PostgreSQL)

**customers**
```sql
- id (UUID, PK)
- company_name (VARCHAR)
- email (VARCHAR, UNIQUE)
- industry (VARCHAR)
- company_size (VARCHAR)
- created_at (TIMESTAMP)
- subscription_status (VARCHAR)
- subscription_tier (VARCHAR)
```

**virtual_employees** (Marketplace templates)
```sql
- id (UUID, PK)
- name (VARCHAR)
- role (VARCHAR)
- department (VARCHAR)
- seniority_level (ENUM: junior, senior, manager)
- description (TEXT)
- capabilities (JSONB)
- tools (JSONB)
- pricing_monthly (DECIMAL)
- framework (VARCHAR, default: 'crewai')
- status (ENUM: beta, alpha, stable)
```

**customer_ves** (Hired VE instances)
```sql
- id (UUID, PK)
- customer_id (UUID, FK → customers)
- ve_id (UUID, FK → virtual_employees)
- persona_name (VARCHAR) -- e.g., "Sarah Johnson"
- persona_email (VARCHAR) -- e.g., "sarah.johnson@acme.veworkforce.io"
- hired_at (TIMESTAMP)
- status (VARCHAR)
- namespace (VARCHAR) -- Kubernetes namespace
- agent_name (VARCHAR) -- K8s agent identifier
- position_x, position_y (INTEGER) -- For org chart canvas
```

**ve_connections** (Org chart relationships)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- from_ve_id (UUID, FK → customer_ves)
- to_ve_id (UUID, FK → customer_ves)
- connection_type (ENUM: vertical, horizontal)
```

**tasks** (Kanban tasks)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- title (VARCHAR)
- description (TEXT)
- created_by_user (BOOLEAN)
- assigned_to_ve (UUID, FK → customer_ves)
- status (ENUM: pending, in_progress, review, completed, cancelled)
- priority (ENUM: low, medium, high, urgent)
- due_date (TIMESTAMP)
- created_at, updated_at, completed_at (TIMESTAMP)
```

**messages** (Email-like interface)
```sql
- id (UUID, PK)
- task_id (UUID, FK → tasks, nullable)
- customer_id (UUID, FK)
- from_type (ENUM: customer, ve)
- from_user_id (UUID, FK → customers, nullable)
- from_ve_id (UUID, FK → customer_ves, nullable)
- to_type (ENUM: customer, ve)
- to_user_id (UUID, FK → customers, nullable)
- to_ve_id (UUID, FK → customer_ves, nullable)
- subject (VARCHAR)
- content (TEXT)
- message_type (ENUM: email, chat, system)
- read (BOOLEAN)
- created_at (TIMESTAMP)
```

**token_usage** (Billing)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- ve_id (UUID, FK → customer_ves, nullable)
- operation (VARCHAR) -- e.g., "orchestrator_routing", "ve_execution"
- input_tokens (INTEGER)
- output_tokens (INTEGER)
- total_tokens (INTEGER)
- cost (DECIMAL)
- model (VARCHAR)
- timestamp (TIMESTAMP)
```

**company_knowledge** (RAG knowledge base)
```sql
- id (UUID, PK)
- customer_id (UUID, FK)
- content (TEXT)
- content_type (VARCHAR)
- embeddings (VECTOR(1536)) -- For RAG
- metadata (JSONB)
- created_at, updated_at (TIMESTAMP)
```

**ve_contexts** (VE memory/state)
```sql
- id (UUID, PK)
- customer_ve_id (UUID, FK → customer_ves)
- context_data (JSONB)
- last_updated (TIMESTAMP)
```

---

## 4. Frontend Requirements

### 4.1 Page Structure

#### 4.1.1 Authentication Pages
- **Login** (`/login`)
  - Email + Password
  - "Sign up" link
  - "Forgot password" link
  - Supabase Auth integration

- **Sign Up** (`/signup`)
  - Email, Password, Company Name
  - Company details form
  - Terms acceptance
  - Auto-login after signup

#### 4.1.2 Main Dashboard (`/dashboard`)

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│  Header: Logo | Search | Notifications | Profile    │
├───────────────┬─────────────────────────────────────┤
│               │                                     │
│  Sidebar:     │  Main Content Area                  │
│  - Dashboard  │                                     │
│  - Marketplace│  (Dynamic content based on route)   │
│  - My Team    │                                     │
│  - Tasks      │                                     │
│  - Messages   │                                     │
│  - Billing    │                                     │
│               │                                     │
└───────────────┴─────────────────────────────────────┘
```

**Dashboard Home View:**
- Overview cards:
  - Total VEs hired
  - Active tasks
  - Token usage this month
  - Pending messages
- Recent activity feed
- Quick actions: "Hire VE", "Create Task"

#### 4.1.3 VE Marketplace (`/marketplace`)

**Features:**
- Grid/List view of available VEs
- Filters:
  - Department (Marketing, Support, Sales, etc.)
  - Seniority (Junior, Senior, Manager)
  - Status (Beta, Alpha, Stable)
  - Price range
- Search functionality
- VE Cards showing:
  - Persona avatar/icon
  - Role and department
  - Seniority level badge
  - Brief description
  - Pricing ($/month)
  - "View Details" button

**VE Detail Modal:**
- Full description
- Capabilities list
- Tools available
- Pricing breakdown
- "Hire" button
- Setup form:
  - Give VE a custom name (or use default)
  - Assign to position on org chart
  - Confirm hiring

#### 4.1.4 My Team - Org Chart Builder (`/team`)

**Interactive Canvas (ReactFlow):**
- Drag-and-drop interface
- VE cards on canvas with:
  - Avatar/icon
  - Name
  - Role
  - Status indicator (active, idle, working)
- Connection lines:
  - Vertical (delegation/management)
  - Horizontal (collaboration)
- Toolbar:
  - "Add VE from Marketplace"
  - Zoom in/out
  - Auto-layout
  - Save changes
- Right-click context menu:
  - Edit VE details
  - Remove VE
  - Create connection
- Real-time activity indicators on VEs

#### 4.1.5 Tasks - Kanban Board (`/tasks`)

**Kanban Columns:**
- To Do
- In Progress
- Review
- Completed

**Task Cards:**
- Title
- Description (truncated)
- Assigned VE avatar/name
- Priority badge
- Due date
- Click to expand full details

**Task Detail View (Modal or Side Panel):**
- Full description
- Assigned VE
- Created by (customer or VE)
- Priority
- Due date
- Status
- Related messages/conversation thread
- Token usage for this task
- Action buttons:
  - Reassign
  - Change status
  - Add comment
  - Delete

**Create Task:**
- Title input
- Description (rich text)
- Assign to VE (dropdown)
- Priority selection
- Due date picker
- "Create Task" button

#### 4.1.6 Messages - Email-like Interface (`/messages`)

**Layout:**
```
┌──────────────┬────────────────────────────────────┐
│  Inbox       │  Message Thread                    │
│              │                                    │
│  [Message 1] │  ┌──────────────────────────────┐ │
│  [Message 2] │  │ From: Sarah (Marketing Mgr)   │ │
│  [Message 3] │  │ To: You                       │ │
│              │  │ Re: Marketing Campaign        │ │
│              │  │                               │ │
│              │  │ [Message Content]             │ │
│              │  └──────────────────────────────┘ │
│              │                                    │
│              │  [Reply Box]                       │
└──────────────┴────────────────────────────────────┘
```

**Inbox (Left Panel):**
- List of message threads
- Each thread shows:
  - VE avatar
  - VE name
  - Subject line
  - Last message preview
  - Timestamp
  - Unread badge
- Filter: All / Unread / From VEs / To VEs

**Message Thread (Right Panel):**
- Professional email-style layout
- Each message shows:
  - From: Name (Role)
  - To: Name
  - Subject
  - Timestamp
  - Message content (formatted text)
  - If delegation: "Delegated to Senior VE Alex"
- Chronological order (newest at bottom)

**Compose/Reply:**
- To: Dropdown (select VE or "work inbox" for orchestrator routing)
- Subject: Input field
- Content: Rich text editor
- "Send" button
- Attachments support (future)

**Key UX Note:**
- Messages are NOT real emails
- System simulates email experience
- All stored in messages table
- Creates tasks automatically from messages

#### 4.1.7 Billing (`/billing`)

**Overview Section:**
- Current month token usage
- Estimated cost
- Usage graph (last 30 days)

**Token Usage Breakdown:**
- Table showing:
  - Date/Time
  - Operation (Orchestrator routing, VE execution, etc.)
  - VE involved
  - Input tokens
  - Output tokens
  - Cost
- Filter by date range, VE
- Export to CSV

**Subscription Section:**
- Current tier
- Monthly VE costs
- Payment method
- Billing history

### 4.2 Component Library

**Reusable Components:**
- VECard (marketplace, org chart, task assignment)
- TaskCard (kanban board)
- MessageThread (email interface)
- TokenUsageChart (billing)
- ActivityFeed (dashboard)
- VEStatusIndicator (real-time status)
- PriorityBadge (tasks)
- SeniorityBadge (VEs)

### 4.3 State Management

**Recommended: Context API + React Query**
- Auth context (Supabase session)
- Customer context (current user data)
- VE context (hired VEs, org structure)
- Task context (kanban state)
- Message context (inbox state)
- React Query for server state caching

### 4.4 Real-time Features

**Supabase Real-time Subscriptions:**
- New messages → Update inbox
- Task status changes → Update kanban
- VE status changes → Update org chart indicators
- Token usage → Update billing dashboard

---

## 5. Backend API Requirements

### 5.1 API Endpoints

#### 5.1.1 Authentication
```
POST   /api/auth/signup
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
POST   /api/auth/refresh
```

#### 5.1.2 Customers
```
GET    /api/customers/me
PUT    /api/customers/me
GET    /api/customers/me/settings
PUT    /api/customers/me/settings
```

#### 5.1.3 VE Marketplace
```
GET    /api/marketplace/ves
GET    /api/marketplace/ves/{ve_id}
POST   /api/marketplace/ves/{ve_id}/hire
```

#### 5.1.4 Customer VEs
```
GET    /api/ves
GET    /api/ves/{customer_ve_id}
PUT    /api/ves/{customer_ve_id}
DELETE /api/ves/{customer_ve_id}
POST   /api/ves/{customer_ve_id}/activate
POST   /api/ves/{customer_ve_id}/deactivate
```

#### 5.1.5 Org Chart
```
GET    /api/org-chart
PUT    /api/org-chart/positions
POST   /api/org-chart/connections
DELETE /api/org-chart/connections/{connection_id}
```

#### 5.1.6 Tasks
```
GET    /api/tasks
POST   /api/tasks
GET    /api/tasks/{task_id}
PUT    /api/tasks/{task_id}
DELETE /api/tasks/{task_id}
PUT    /api/tasks/{task_id}/status
POST   /api/tasks/{task_id}/assign
```

#### 5.1.7 Messages
```
GET    /api/messages
POST   /api/messages
GET    /api/messages/{message_id}
PUT    /api/messages/{message_id}/read
GET    /api/messages/threads/{task_id}
```

#### 5.1.8 Orchestrator
```
POST   /api/orchestrator/route
```
- Receives customer request
- Routes to shared orchestrator
- Orchestrator delegates to appropriate VE via Agent Gateway
- Returns response

#### 5.1.9 Billing
```
GET    /api/billing/usage
GET    /api/billing/usage/breakdown
GET    /api/billing/subscription
```

### 5.2 Orchestrator Logic

**Shared Orchestrator Service:**
```python
class SharedOrchestrator:
    async def route_request(self, customer_id, task_description):
        # 1. Get customer org structure
        org = await get_customer_org(customer_id)
        
        # 2. Analyze task and decide routing
        routing_decision = await llm_analyze(
            task=task_description,
            org_structure=org
        )
        
        # Track orchestrator tokens
        await track_tokens(customer_id, "orchestrator_routing", routing_decision.usage)
        
        # 3. Route to customer's VE via Agent Gateway
        response = await agent_gateway.call_agent(
            namespace=f"customer-{customer_id}",
            agent=routing_decision.target_ve,
            request=task_description,
            customer_id=customer_id  # For token tracking
        )
        
        return response
```

### 5.3 Agent Gateway Integration

**A2A (Agent-to-Agent) Calls:**
- Orchestrator → VE Manager
- VE Manager → VE Senior/Junior
- All authenticated with JWT/OBO tokens

**MCP (Model Context Protocol):**
- VEs access tools:
  - RAG search (Supabase vectors)
  - Database queries (Supabase)
  - External APIs
- All via Agent Gateway for security and observability

### 5.4 Token Tracking

**Every LLM call must:**
1. Track input/output tokens
2. Calculate cost
3. Store in token_usage table
4. Associate with customer_id and ve_id

---

## 6. VE Agent Implementation

### 6.1 VE Agent Structure (CrewAI)

**Example: Marketing Manager VE**
```python
marketing_manager = Agent(
    role='Marketing Manager',
    goal='Lead marketing initiatives and manage team',
    backstory='''You are Sarah Johnson, an experienced marketing manager. 
    You delegate tasks wisely, review work critically, and ensure high-quality output.
    You can assign work to senior and junior team members.''',
    allow_delegation=True,
    tools=[
        query_company_knowledge,
        analyze_market_trends,
        review_content
    ],
    memory=True
)
```

### 6.2 VE Deployment (KAgent)

**Kubernetes Manifest:**
```yaml
apiVersion: kagent.solo.io/v1
kind: Agent
metadata:
  name: marketing-manager
  namespace: customer-123
  labels:
    customer_id: "123"
    ve_type: "marketing-manager"
    tier: "manager"
spec:
  framework: crewai
  config:
    role: "Marketing Manager"
    allow_delegation: true
    tools:
      - query_company_knowledge
      - analyze_market_trends
    memory: true
```

### 6.3 Inter-VE Communication

**Manager delegates to Senior (A2A via Agent Gateway):**
```python
# Manager VE internally calls Senior VE
response = await agent_gateway.call_agent(
    namespace="customer-123",
    agent="marketing-senior",
    request={
        "task": "Research competitors",
        "context": {...}
    },
    from_agent="marketing-manager"
)
```

---

## 7. User Flows

### 7.1 Customer Onboarding Flow

1. Sign up → Create account
2. Welcome screen → Company details
3. Redirect to Marketplace
4. Browse and hire first VE
5. Name VE and place on org chart
6. Dashboard tour
7. Create first task

### 7.2 Task Creation & Delegation Flow

**Via Kanban:**
1. Customer clicks "Create Task"
2. Fills title, description, assigns to VE Manager
3. Task card appears in "To Do"
4. VE Manager analyzes task
5. Manager delegates to Senior VE (internal, via A2A)
6. Senior executes, uses RAG and tools
7. Senior reports back to Manager
8. Manager reviews, approves
9. Manager sends message to customer with result
10. Customer sees message in email interface
11. Task moves to "Completed" in Kanban

**Via Email Interface:**
1. Customer composes message to VE Manager
2. Backend creates task from message
3. Routes to orchestrator
4. Orchestrator routes to Manager VE
5. Same flow as above from step 4

### 7.3 Hiring Additional VEs Flow

1. Customer goes to Marketplace
2. Filters by department/seniority
3. Clicks "View Details" on a VE
4. Modal shows full details and pricing
5. Clicks "Hire"
6. Setup modal:
   - Name VE (or use default)
   - Choose position on org chart
7. Backend:
   - Creates customer_ves record
   - Deploys Agent to Kubernetes namespace
8. VE appears on org chart
9. Customer can connect to other VEs
10. Ready to receive tasks

---

## 8. Non-Functional Requirements

### 8.1 Performance
- Page load time: < 2 seconds
- API response time: < 500ms (excluding LLM calls)
- LLM response time: < 30 seconds
- Real-time updates: < 1 second latency

### 8.2 Security
- Authentication: Supabase Auth (JWT)
- Authorization: Row-Level Security (RLS) in Supabase
- Agent Gateway enforces A2A auth (JWT/OBO tokens)
- HTTPS only
- Input validation on all endpoints
- Rate limiting on API

### 8.3 Scalability
- Support 10,000+ customers
- 100,000+ VE instances across all customers
- 1,000+ concurrent API requests
- Kubernetes horizontal autoscaling

### 8.4 Monitoring & Observability
- OpenTelemetry tracing (Agent Gateway)
- Sentry for error tracking
- Prometheus for metrics
- Grafana dashboards
- Token usage tracking for billing

### 8.5 Accessibility
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader support
- High contrast mode

---

## 9. Admin Creator Portal (Port 3001)

### 9.1 Purpose
Internal tool for platform administrators to:
- Create new VE templates for the marketplace
- Configure VE capabilities and tools
- Manage MCP tool integrations
- Test VE agents before publishing
- Monitor marketplace VE performance

### 9.2 Admin Portal Pages

#### 9.2.1 VE Creator (`/create`)
**Visual Builder Interface:**
- **Basic Information**:
  - VE Name (e.g., "Marketing Manager")
  - Role (e.g., "Marketing Manager")
  - Department (dropdown: Marketing, Sales, Support, etc.)
  - Seniority Level (Junior, Senior, Manager)
  - Description (rich text)
  - Avatar/Icon upload

- **Capabilities Section**:
  - Multi-select capabilities:
    - Content Creation
    - Data Analysis
    - Project Management
    - Customer Communication
    - Research
    - Code Generation
  - Custom capability input

- **Tools Configuration**:
  - Available MCP Tools list (from Tool Manager)
  - Drag-and-drop to assign tools
  - Tool permission settings
  - Custom tool parameters

- **CrewAI Agent Definition**:
  - Code editor for agent configuration
  - Templates dropdown (Marketing, Sales, Support)
  - Syntax highlighting
  - Validation

```yaml
role: "Marketing Manager"
goal: "Lead marketing initiatives and manage team"
backstory: |
  You are Sarah Johnson, an experienced marketing manager.
  You delegate tasks wisely and ensure high-quality output.
allow_delegation: true
tools:
  - query_company_knowledge
  - analyze_market_trends
memory: true
```

- **Pricing**:
  - Monthly base price ($/month)
  - Token multiplier
  - Pricing tier (Starter, Pro, Enterprise)

- **Status**:
  - Beta, Alpha, Stable
  - Visibility (Public/Private)

- **Actions**:
  - Save as Draft
  - Preview
  - Test Agent
  - Publish to Marketplace

#### 9.2.2 VE List (`/`)
**Marketplace VE Management:**
- Table view of all VEs:
  - Name, Role, Department, Seniority
  - Status (Beta/Alpha/Stable)
  - Pricing
  - Active Hires (count)
  - Created Date
  - Actions (Edit, Duplicate, Archive, Delete)

- **Filters**:
  - Department
  - Seniority
  - Status
  - Created Date Range

- **Bulk Actions**:
  - Change Status
  - Update Pricing
  - Archive Selected

- **Analytics per VE**:
  - Total hires
  - Active instances
  - Average token usage
  - Customer satisfaction rating
  - Task completion rate

#### 9.2.3 Tool Manager (`/tools`)
**MCP Tool Integration:**
- **Tool Registry**:
  - List of registered MCP tools
  - Each tool shows:
    - Name
    - Description
    - MCP Server URL
    - Authentication type
    - Status (Active/Inactive)
    - VEs using this tool

- **Add New Tool**:
  - Tool Name
  - MCP Server Endpoint
  - Authentication:
    - None
    - API Key
    - OAuth
  - Configuration (JSON)
  - Test Connection

- **Tool Categories**:
  - Data Access (Database queries, File systems)
  - External APIs (Weather, Stock data, etc.)
  - Custom Tools (Company-specific)

- **Tool Assignment**:
  - View which VEs use each tool
  - Assign/Unassign tools to VEs

#### 9.2.4 Testing Interface (`/test`)
**VE Agent Testing:**
- **Test Workspace**:
  - Select VE to test
  - Mock customer context
  - Input test task
  - Run agent execution
  - View response
  - Token usage display

- **Test Scenarios**:
  - Predefined test cases
  - Save custom test cases
  - Regression testing

- **Debug Console**:
  - Agent logs
  - Tool call traces
  - Performance metrics

### 9.3 Admin API Endpoints

```
POST   /admin/api/ves                # Create VE template
GET    /admin/api/ves                # List all VE templates
GET    /admin/api/ves/{ve_id}        # Get VE details
PUT    /admin/api/ves/{ve_id}        # Update VE template
DELETE /admin/api/ves/{ve_id}        # Delete VE template
POST   /admin/api/ves/{ve_id}/publish # Publish to marketplace

POST   /admin/api/tools              # Register MCP tool
GET    /admin/api/tools              # List all tools
PUT    /admin/api/tools/{tool_id}    # Update tool
DELETE /admin/api/tools/{tool_id}    # Remove tool
POST   /admin/api/tools/{tool_id}/test # Test tool connection

POST   /admin/api/test/execute       # Test VE execution
GET    /admin/api/analytics/ve/{ve_id} # VE performance analytics
```

### 9.4 Admin Portal Authentication
- **Separate Auth**: Not using Supabase Auth (customer-facing)
- **Options**:
  - Simple password protection (dev)
  - Admin user table in Supabase
  - OAuth with Google Workspace
- **Permissions**:
  - Super Admin (full access)
  - VE Creator (create/edit VEs)
  - Analyst (view-only analytics)

---

## 10. Development Phases

### Phase 1: Core Infrastructure (Weeks 1-2)
- Set up Docker development environment
- Supabase database schema
- Authentication system
- Basic FastAPI backend structure
- React app with routing and auth

### Phase 2: VE Marketplace (Weeks 3-4)
- Marketplace UI (browse, filter, search)
- VE detail view and hiring flow
- Backend API for marketplace
- Deploy first VE to Kubernetes (test)

### Phase 3: Org Chart Builder (Weeks 5-6)
- ReactFlow canvas implementation
- Drag-and-drop VE positioning
- Connection creation (vertical/horizontal)
- Save/load org chart state
- Real-time VE status indicators

### Phase 4: Task Management (Weeks 7-8)
- Kanban board UI
- Task CRUD operations
- Task assignment to VEs
- Task detail view
- Status updates

### Phase 5: Email-like Interface (Weeks 9-10)
- Message inbox UI
- Message thread view
- Compose/reply functionality
- Link messages to tasks
- Professional email styling

### Phase 6: Orchestrator & VE Integration (Weeks 11-12)
- Shared orchestrator service
- Agent Gateway integration
- Deploy CrewAI VE agents
- A2A communication (Manager → Senior → Junior)
- MCP tool integration (RAG, DB)

### Phase 7: Billing & Token Tracking (Weeks 13-14)
- Token usage tracking in all LLM calls
- Billing dashboard UI
- Usage breakdown views
- Cost calculations

### Phase 8: Testing & Polish (Weeks 15-16)
- End-to-end testing
- Performance optimization
- Bug fixes
- UI/UX refinements
- Documentation

---

## 10. Acceptance Criteria

### 10.1 MVP Success Criteria
- [x] Customer can sign up and log in
- [x] Customer can browse marketplace and hire VEs
- [x] Customer can build org chart with drag-and-drop
- [x] Customer can create tasks and assign to VEs
- [x] VEs can autonomously delegate to other VEs
- [x] Customer can view task progress in Kanban
- [x] Customer can communicate with VEs via email-like interface
- [x] System tracks all token usage for billing
- [x] Manager VE can review and reassign work
- [x] All customer data is isolated (namespace-based)

### 10.2 Quality Gates
- All API endpoints have tests
- Frontend components have unit tests
- End-to-end tests for critical flows
- Security audit passed
- Performance benchmarks met
- Accessibility standards met

---

## 11. API Documentation Standards

- OpenAPI/Swagger documentation for all endpoints
- Request/response examples
- Error code documentation
- Authentication flow documentation
- Rate limiting documentation

---

## 12. Deployment Instructions

### 12.1 Development Environment
```bash
# Clone repo
git clone <repo-url>
cd ve-saas-platform

# Copy environment variables
cp .env.example .env
# Edit .env with your keys

# Start services
docker-compose up -d

# Access services:
# - Portainer: http://localhost:9000
# - Frontend: http://localhost:3002
# - Backend: http://localhost:8001
# - Supabase: http://localhost:3001
```

### 12.2 Production Deployment
- Kubernetes cluster setup
- Helm charts for all services
- CI/CD pipeline (GitHub Actions)
- Environment-specific configs
- Database migrations strategy
- Monitoring and alerting setup

---

## 13. Future Enhancements (Post-MVP)

- Voice interface for VE communication
- Mobile apps (iOS, Android)
- Advanced analytics dashboard
- Custom VE creation (customer-defined)
- Workflow automation builder
- Integration marketplace (Slack, Teams, etc.)
- White-label solution for enterprises
- Multi-language support
- Advanced RAG with document upload
- VE performance scoring

---

## 14. Questions for Development Team

Before starting, please clarify:

1. **LLM Provider:** Which LLM provider should we use as default? (OpenAI, Anthropic, other?)
2. **Agent Gateway:** Is Solo.io Agent Gateway available, or should we mock it initially?
3. **KAgent:** Can we get access to KAgent Enterprise, or start with open-source version?
4. **Deployment:** What's the target production environment? (GCP, AWS, Azure, on-prem?)
5. **CI/CD:** What's your preferred CI/CD platform?
6. **Monitoring:** What monitoring tools are already in your stack?

---

## 15. Contact & Support

- **Product Owner:** [Your Name]
- **Technical Lead:** [TBD]
- **Repository:** [GitHub URL]
- **Slack Channel:** #ve-saas-platform
- **Documentation:** [Confluence/Notion URL]

---

**Document Status:** Ready for Development  
**Next Steps:** Development team reviews PRD, asks questions, begins Phase 1

