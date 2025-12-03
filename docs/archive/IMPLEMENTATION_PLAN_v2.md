# Implementation Plan - VE SaaS Platform v2.0
## Detailed Task Breakdown by Component

**Version:** 2.0 (Simplified Architecture)  
**Date:** November 26, 2025  
**Timeline:** 5-6 weeks to MVP

---

## 📋 Table of Contents
1. [Phase 1: Setup & Integration](#phase-1-setup--integration-week-1)
2. [Phase 2: Marketplace](#phase-2-marketplace-week-2)
3. [Phase 3: Hiring & Chat](#phase-3-hiring--chat-week-3)
4. [Phase 4: Tasks & Billing](#phase-4-tasks--billing-week-4)
5. [Phase 5: Polish & Production](#phase-5-polish--production-week-5-6)

---

## Phase 1: Setup & Integration (Week 1)

### 🎯 Goal
Deploy KAgent + Agent Gateway, establish connectivity, verify end-to-end flow

### Backend Tasks

#### 1.1 Infrastructure Setup
- [ ] **Deploy KAgent to Kubernetes**
  - Install KAgent using Helm chart
  - Configure default ModelConfig
  - Verify KAgent dashboard is accessible
  - Create test namespace
  - **Files:** `infrastructure/kagent/values.yaml`, `infrastructure/kagent/deploy.sh`

- [ ] **Deploy Agent Gateway to Kubernetes**
  - Install Agent Gateway using Helm chart
  - Configure listeners (HTTP, TLS)
  - Set up JWT authentication
  - Configure webhooks endpoint
  - **Files:** `infrastructure/agent-gateway/values.yaml`, `infrastructure/agent-gateway/deploy.sh`

#### 1.2 API Clients
- [ ] **Create KAgent API Client**
  - Implement `KAgentClient` class
  - Methods: `list_agents()`, `get_agent()`, `get_agent_status()`
  - Handle authentication
  - Error handling
  - **Files:** `backend/app/services/kagent_client.py`

- [ ] **Create Agent Gateway Client**
  - Implement `AgentGatewayClient` class
  - Methods: `invoke_agent()`, `create_route()`, `delete_route()`
  - JWT token management
  - Webhook signature verification
  - **Files:** `backend/app/services/agent_gateway_client.py`

#### 1.3 Database Setup
- [ ] **Create Supabase Project**
  - Set up new Supabase project
  - Configure authentication
  - Enable Row-Level Security
  - **Files:** `backend/supabase/config.sql`

- [ ] **Create Initial Schema**
  - Create `customers` table
  - Create `marketplace_agents` table
  - Create `customer_ves` table
  - Create `messages` table
  - Create `tasks` table
  - Create `token_usage` table
  - **Files:** `backend/supabase/migrations/001_initial_schema.sql`

#### 1.4 Testing
- [ ] **End-to-End Test**
  - Create test agent in KAgent Dashboard
  - Call agent via Agent Gateway
  - Verify response
  - Check token usage webhook
  - **Files:** `backend/tests/test_integration.py`

### Admin Frontend Tasks

#### 1.5 Project Setup
- [ ] **Initialize React Project**
  - Create React app with TypeScript
  - Install dependencies (React Query, Axios, TailwindCSS)
  - Configure TailwindCSS
  - Set up routing
  - **Files:** `admin-frontend/package.json`, `admin-frontend/tailwind.config.js`

- [ ] **Create API Client**
  - Implement Axios client with interceptors
  - Configure base URL
  - Add authentication headers
  - **Files:** `admin-frontend/src/services/api.ts`

- [ ] **Create KAgent API Client**
  - Implement `kagentApi.ts`
  - Methods: `listAgents()`, `getAgent()`
  - **Files:** `admin-frontend/src/services/kagentApi.ts`

#### 1.6 Basic Components
- [ ] **Create Layout Components**
  - Header with navigation
  - Sidebar
  - Main content area
  - **Files:** `admin-frontend/src/components/Layout.tsx`

- [ ] **Create UI Components**
  - Button, Input, Card, Badge
  - Modal, Toast
  - Loading spinner
  - **Files:** `admin-frontend/src/components/ui/`

### User Frontend Tasks

#### 1.7 Project Setup
- [ ] **Initialize React Project**
  - Create React app with TypeScript
  - Install dependencies
  - Configure TailwindCSS
  - Set up routing
  - **Files:** `user-frontend/package.json`, `user-frontend/tailwind.config.js`

- [ ] **Create API Client**
  - Implement Axios client
  - Configure authentication
  - **Files:** `user-frontend/src/services/api.ts`

- [ ] **Create Layout**
  - Header, sidebar, main content
  - Navigation menu
  - **Files:** `user-frontend/src/components/Layout.tsx`

---

## Phase 2: Marketplace (Week 2)

### 🎯 Goal
Admin can publish agents to marketplace, users can browse

### Backend Tasks

#### 2.1 Marketplace Service
- [ ] **Create Marketplace Service**
  - Implement `MarketplaceService` class
  - Methods: `add_agent()`, `update_agent()`, `delete_agent()`, `list_agents()`, `get_agent()`
  - Validation logic
  - **Files:** `backend/app/services/marketplace_service.py`

#### 2.2 API Endpoints
- [ ] **Admin Marketplace API**
  - `GET /api/admin/kagent/agents` - List from KAgent
  - `GET /api/admin/kagent/agents/{name}` - Get details
  - `POST /api/admin/marketplace/agents` - Add to marketplace
  - `PUT /api/admin/marketplace/agents/{id}` - Update metadata
  - `DELETE /api/admin/marketplace/agents/{id}` - Unpublish
  - **Files:** `backend/app/api/admin/marketplace.py`

- [ ] **User Marketplace API**
  - `GET /api/marketplace/agents` - Browse with metadata
  - `GET /api/marketplace/agents/{id}` - Agent details
  - **Files:** `backend/app/api/marketplace.py`

#### 2.3 File Upload
- [ ] **Implement Icon/Screenshot Upload**
  - Supabase Storage integration
  - Image validation
  - URL generation
  - **Files:** `backend/app/services/storage_service.py`

### Admin Frontend Tasks

#### 2.4 Agent Browser
- [ ] **Create Agent Browser Page**
  - Fetch agents from KAgent API
  - Display in table/grid
  - "Add to Marketplace" button
  - **Files:** `admin-frontend/src/pages/AgentBrowser.tsx`

- [ ] **Create Agent Browser Components**
  - AgentCard component
  - AgentTable component
  - **Files:** `admin-frontend/src/components/AgentCard.tsx`

#### 2.5 Marketplace Editor
- [ ] **Create Marketplace Editor Page**
  - Form for pricing, tags, description
  - Icon/screenshot upload
  - Preview
  - Publish button
  - **Files:** `admin-frontend/src/pages/MarketplaceEditor.tsx`

- [ ] **Create Form Components**
  - PricingForm component
  - TagsInput component
  - ImageUpload component
  - **Files:** `admin-frontend/src/components/marketplace/`

#### 2.6 Published Agents View
- [ ] **Create Published Agents Page**
  - List published agents
  - Edit/unpublish actions
  - **Files:** `admin-frontend/src/pages/PublishedAgents.tsx`

### User Frontend Tasks

#### 2.7 Marketplace Browse
- [ ] **Create Marketplace Page**
  - Grid view of agents
  - Search bar
  - Filter sidebar (category, tags, price)
  - **Files:** `user-frontend/src/pages/Marketplace.tsx`

- [ ] **Create Marketplace Components**
  - AgentCard component
  - SearchBar component
  - FilterSidebar component
  - **Files:** `user-frontend/src/components/marketplace/`

#### 2.8 Agent Detail
- [ ] **Create Agent Detail Page**
  - Agent information
  - Pricing details
  - Capabilities list
  - "Hire" button
  - **Files:** `user-frontend/src/pages/AgentDetail.tsx`

---

## Phase 3: Hiring & Chat (Week 3)

### 🎯 Goal
Customers can hire VEs and chat with them

### Backend Tasks

#### 3.1 Customer VE Service
- [ ] **Create Customer VE Service**
  - Implement `CustomerVEService` class
  - Methods: `hire_ve()`, `list_ves()`, `get_ve()`, `delete_ve()`
  - **Files:** `backend/app/services/customer_ve_service.py`

#### 3.2 Agent Gateway Integration
- [ ] **Implement Route Creation**
  - Create route in Agent Gateway on VE hire
  - Configure JWT auth
  - Set rate limits
  - **Files:** `backend/app/services/agent_gateway_client.py` (extend)

- [ ] **Implement Chat Forwarding**
  - Forward customer messages to Agent Gateway
  - Handle responses
  - Store message history
  - **Files:** `backend/app/services/chat_service.py`

#### 3.3 Webhook Handler
- [ ] **Create Webhook Endpoint**
  - `POST /api/webhooks/agent-gateway/usage` - Token usage
  - `POST /api/webhooks/agent-gateway/events` - Agent events
  - Signature verification
  - **Files:** `backend/app/api/webhooks.py`

- [ ] **Implement Token Usage Tracking**
  - Store token usage in database
  - Associate with customer and VE
  - Calculate cost
  - **Files:** `backend/app/services/billing_service.py`

#### 3.4 API Endpoints
- [ ] **Hire VE Endpoint**
  - `POST /api/marketplace/agents/{id}/hire`
  - Create customer_ves record
  - Configure Agent Gateway
  - Return VE details
  - **Files:** `backend/app/api/marketplace.py` (extend)

- [ ] **My VEs Endpoints**
  - `GET /api/ves` - List hired VEs
  - `GET /api/ves/{id}` - VE details
  - `DELETE /api/ves/{id}` - Remove VE
  - **Files:** `backend/app/api/ves.py`

- [ ] **Chat Endpoints**
  - `POST /api/ves/{id}/chat` - Send message
  - `GET /api/ves/{id}/messages` - Get history
  - **Files:** `backend/app/api/chat.py`

### User Frontend Tasks

#### 3.5 Hire Flow
- [ ] **Create Hire Modal**
  - Confirm hiring
  - Custom VE name input
  - Pricing confirmation
  - **Files:** `user-frontend/src/components/HireModal.tsx`

- [ ] **Implement Hire Logic**
  - Call hire API
  - Handle success/error
  - Redirect to My Team
  - **Files:** `user-frontend/src/hooks/useHireVE.ts`

#### 3.6 My Team Page
- [ ] **Create My Team Page**
  - List hired VEs
  - VE cards with status
  - "Chat" button
  - "Remove" button
  - **Files:** `user-frontend/src/pages/MyTeam.tsx`

- [ ] **Create VE Card Component**
  - VE info display
  - Status indicator
  - Action buttons
  - **Files:** `user-frontend/src/components/VECard.tsx`

#### 3.7 Chat Interface
- [ ] **Create Chat Page**
  - Message list
  - Input box
  - Send button
  - Real-time updates
  - **Files:** `user-frontend/src/pages/Chat.tsx`

- [ ] **Create Chat Components**
  - MessageList component
  - MessageBubble component
  - ChatInput component
  - **Files:** `user-frontend/src/components/chat/`

- [ ] **Implement Chat Logic**
  - Send message API call
  - Fetch message history
  - Real-time updates (polling or WebSocket)
  - **Files:** `user-frontend/src/hooks/useChat.ts`

---

## Phase 4: Tasks & Billing (Week 4)

### 🎯 Goal
Task management and billing dashboard

### Backend Tasks

#### 4.1 Task Service
- [ ] **Create Task Service**
  - Implement `TaskService` class
  - Methods: `create_task()`, `list_tasks()`, `update_task()`, `delete_task()`
  - **Files:** `backend/app/services/task_service.py`

#### 4.2 Task API
- [ ] **Create Task Endpoints**
  - `GET /api/tasks` - List tasks
  - `POST /api/tasks` - Create task
  - `GET /api/tasks/{id}` - Task details
  - `PUT /api/tasks/{id}` - Update task
  - `DELETE /api/tasks/{id}` - Delete task
  - **Files:** `backend/app/api/tasks.py`

#### 4.3 Billing Service
- [ ] **Extend Billing Service**
  - Calculate monthly usage
  - Generate invoices
  - Usage breakdown by VE
  - **Files:** `backend/app/services/billing_service.py` (extend)

#### 4.4 Billing API
- [ ] **Create Billing Endpoints**
  - `GET /api/billing/usage` - Current usage
  - `GET /api/billing/usage/breakdown` - Detailed breakdown
  - `GET /api/billing/invoices` - Invoice history
  - **Files:** `backend/app/api/billing.py`

### User Frontend Tasks

#### 4.5 Task Management
- [ ] **Create Tasks Page**
  - Task list view
  - Create task button
  - Filter/sort options
  - **Files:** `user-frontend/src/pages/Tasks.tsx`

- [ ] **Create Task Components**
  - TaskList component
  - TaskCard component
  - CreateTaskModal component
  - **Files:** `user-frontend/src/components/tasks/`

- [ ] **Implement Task Logic**
  - Create task API call
  - Update task status
  - Delete task
  - **Files:** `user-frontend/src/hooks/useTasks.ts`

#### 4.6 Billing Dashboard
- [ ] **Create Billing Page**
  - Usage overview cards
  - Usage chart
  - Breakdown table
  - **Files:** `user-frontend/src/pages/Billing.tsx`

- [ ] **Create Billing Components**
  - UsageChart component
  - UsageTable component
  - InvoiceList component
  - **Files:** `user-frontend/src/components/billing/`

- [ ] **Implement Billing Logic**
  - Fetch usage data
  - Calculate totals
  - Export functionality
  - **Files:** `user-frontend/src/hooks/useBilling.ts`

---

## Phase 5: Polish & Production (Week 5-6)

### 🎯 Goal
Production-ready platform

### Backend Tasks

#### 5.1 Security
- [ ] **Implement Rate Limiting**
  - Add rate limiting middleware
  - Configure limits per endpoint
  - **Files:** `backend/app/middleware/rate_limit.py`

- [ ] **Add Input Validation**
  - Pydantic models for all endpoints
  - Sanitize user input
  - **Files:** `backend/app/models/` (all files)

- [ ] **Security Audit**
  - Review authentication flow
  - Check authorization logic
  - Test SQL injection prevention
  - **Files:** `backend/SECURITY_AUDIT.md`

#### 5.2 Error Handling
- [ ] **Implement Global Error Handler**
  - Catch all exceptions
  - Return proper error responses
  - Log errors
  - **Files:** `backend/app/middleware/error_handler.py`

- [ ] **Add Sentry Integration**
  - Configure Sentry
  - Add error tracking
  - **Files:** `backend/app/core/sentry.py`

#### 5.3 Performance
- [ ] **Add Caching**
  - Redis caching for marketplace agents
  - Cache invalidation strategy
  - **Files:** `backend/app/services/cache_service.py`

- [ ] **Optimize Database Queries**
  - Add indexes
  - Optimize N+1 queries
  - **Files:** `backend/supabase/migrations/002_indexes.sql`

#### 5.4 Testing
- [ ] **Write Unit Tests**
  - Test all services
  - Test API endpoints
  - **Files:** `backend/tests/unit/`

- [ ] **Write Integration Tests**
  - Test end-to-end flows
  - Test KAgent integration
  - Test Agent Gateway integration
  - **Files:** `backend/tests/integration/`

#### 5.5 Documentation
- [ ] **API Documentation**
  - OpenAPI/Swagger docs
  - Endpoint descriptions
  - Example requests/responses
  - **Files:** `backend/docs/api.md`

- [ ] **Deployment Guide**
  - Infrastructure setup
  - Environment variables
  - Deployment steps
  - **Files:** `backend/docs/deployment.md`

### Admin Frontend Tasks

#### 5.6 Polish
- [ ] **Add Loading States**
  - Loading spinners
  - Skeleton screens
  - **Files:** `admin-frontend/src/components/Loading.tsx`

- [ ] **Add Error States**
  - Error messages
  - Retry buttons
  - **Files:** `admin-frontend/src/components/Error.tsx`

- [ ] **Improve UX**
  - Add tooltips
  - Add help text
  - Improve form validation
  - **Files:** Various components

#### 5.7 Testing
- [ ] **Write Component Tests**
  - Test all components
  - Test user interactions
  - **Files:** `admin-frontend/src/__tests__/`

- [ ] **E2E Tests**
  - Test publish flow
  - **Files:** `admin-frontend/e2e/`

### User Frontend Tasks

#### 5.8 Polish
- [ ] **Add Loading States**
  - Loading spinners
  - Skeleton screens
  - **Files:** `user-frontend/src/components/Loading.tsx`

- [ ] **Add Error States**
  - Error messages
  - Retry buttons
  - **Files:** `user-frontend/src/components/Error.tsx`

- [ ] **Improve UX**
  - Add onboarding tour
  - Add empty states
  - Improve mobile responsiveness
  - **Files:** Various components

#### 5.9 Testing
- [ ] **Write Component Tests**
  - Test all components
  - **Files:** `user-frontend/src/__tests__/`

- [ ] **E2E Tests**
  - Test hire flow
  - Test chat flow
  - Test task flow
  - **Files:** `user-frontend/e2e/`

### DevOps Tasks

#### 5.10 Deployment
- [ ] **Set Up CI/CD**
  - GitHub Actions workflows
  - Automated testing
  - Automated deployment
  - **Files:** `.github/workflows/`

- [ ] **Configure Production Environment**
  - Set up production Kubernetes cluster
  - Configure domain and SSL
  - Set up monitoring
  - **Files:** `infrastructure/production/`

- [ ] **Deploy to Production**
  - Deploy backend
  - Deploy frontends
  - Verify all services
  - **Files:** `infrastructure/deploy.sh`

#### 5.11 Monitoring
- [ ] **Set Up Monitoring**
  - Prometheus for metrics
  - Grafana dashboards
  - Alerts
  - **Files:** `infrastructure/monitoring/`

- [ ] **Set Up Logging**
  - Centralized logging
  - Log aggregation
  - **Files:** `infrastructure/logging/`

---

## 📊 Summary by Component

### Backend (Total: ~60 tasks)
- Infrastructure: 4 tasks
- API Clients: 2 tasks
- Database: 2 tasks
- Services: 8 tasks
- API Endpoints: 15 tasks
- Webhooks: 2 tasks
- Security: 3 tasks
- Error Handling: 2 tasks
- Performance: 2 tasks
- Testing: 2 tasks
- Documentation: 2 tasks

### Admin Frontend (Total: ~25 tasks)
- Setup: 3 tasks
- Components: 10 tasks
- Pages: 5 tasks
- Polish: 3 tasks
- Testing: 2 tasks

### User Frontend (Total: ~30 tasks)
- Setup: 3 tasks
- Components: 12 tasks
- Pages: 6 tasks
- Polish: 3 tasks
- Testing: 2 tasks

### DevOps (Total: ~5 tasks)
- CI/CD: 1 task
- Deployment: 2 tasks
- Monitoring: 2 tasks

**Total Tasks: ~120**

---

## 🎯 Critical Path

The following tasks are on the critical path and must be completed in order:

1. Deploy KAgent + Agent Gateway
2. Create API clients
3. Create database schema
4. Implement marketplace service
5. Build admin marketplace editor
6. Build user marketplace browse
7. Implement hire VE flow
8. Implement chat functionality
9. Add billing tracking
10. Deploy to production

---

## ✅ Definition of Done

Each task is considered done when:
- [ ] Code is written and reviewed
- [ ] Unit tests pass
- [ ] Integration tests pass (if applicable)
- [ ] Documentation is updated
- [ ] Code is merged to main branch
- [ ] Feature is deployed to staging
- [ ] Feature is tested in staging
- [ ] Product owner approves

---

**Status:** ✅ READY TO START  
**Estimated Effort:** 5-6 weeks with 2-3 developers  
**Next Step:** Begin Phase 1 - Setup & Integration
