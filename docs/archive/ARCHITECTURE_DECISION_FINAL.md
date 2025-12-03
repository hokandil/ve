# Architecture Decision: Simplified Admin Frontend

**Date:** November 26, 2025  
**Decision:** Use KAgent Dashboard for agent creation, Admin Frontend for marketplace metadata only

---

## 🎯 Final Architecture

### Component Responsibilities

**KAgent Dashboard (External):**
- Create and manage Agents
- Create and manage MCP Servers
- Create and manage Tools
- Agent lifecycle management

**Agent Gateway (External):**
- Authentication & Authorization
- Agent Discovery
- Observability & Monitoring
- Request routing
- Rate limiting

**Admin Frontend (Our Application):**
- **Browse** agents from KAgent (via Agent Gateway)
- **Add marketplace metadata:**
  - Pricing (monthly fee, token billing)
  - Tags & Categories
  - Marketing descriptions
  - Status (beta, alpha, stable)
  - Featured flag
  - Icon/screenshots
- **Publish/Unpublish** to marketplace
- **Manage** marketplace listings

**Backend API:**
- Store marketplace metadata
- Link KAgent agents to marketplace listings
- Serve marketplace data to User Frontend

---

## 🔄 Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Platform Engineer uses KAgent Dashboard             │
│     - Creates Agent "customer-success-manager"          │
│     - Configures tools, MCP servers                     │
│     - Deploys to KAgent cluster                         │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  2. Admin uses Admin Frontend                           │
│     - Browses agents from Agent Gateway                 │
│     - Selects "customer-success-manager"                │
│     - Adds pricing: $99/month                           │
│     - Adds tags: ["customer-success", "manager"]        │
│     - Adds description for marketplace                  │
│     - Publishes to marketplace                          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  3. Backend stores marketplace metadata                 │
│     {                                                   │
│       "kagent_agent_name": "customer-success-manager",  │
│       "pricing_monthly": 99,                            │
│       "tags": ["customer-success", "manager"],          │
│       "published": true                                 │
│     }                                                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  4. Customer browses marketplace (User Frontend)        │
│     - Sees "Customer Success Manager" - $99/month       │
│     - Clicks "Hire"                                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  5. Backend provisions agent instance                   │
│     - Creates customer namespace in KAgent              │
│     - Deploys agent instance from template              │
│     - Configures Agent Gateway auth                     │
└─────────────────────────────────────────────────────────┘
```

---

## 🔌 Integration Points

### Admin Frontend → Agent Gateway

**Endpoints:**
- `GET /api/agents` - List all agents (with auth)
- `GET /api/agents/{name}` - Get agent details
- `GET /api/agents/{name}/status` - Get agent status
- `GET /api/mcp-servers` - List MCP servers
- `GET /api/tools` - List available tools

**Authentication:**
- Admin Frontend authenticates with Agent Gateway
- Uses JWT tokens or API keys
- Agent Gateway validates permissions

### Admin Frontend → Backend

**Endpoints:**
- `GET /api/admin/marketplace/listings` - Get marketplace listings
- `POST /api/admin/marketplace/listings` - Create listing (link agent + metadata)
- `PUT /api/admin/marketplace/listings/{id}` - Update metadata
- `DELETE /api/admin/marketplace/listings/{id}` - Unpublish

---

## 📊 Data Model

### KAgent Agent (Read-only from Agent Gateway)
```yaml
apiVersion: kagent.dev/v1alpha2
kind: Agent
metadata:
  name: customer-success-manager
  namespace: default
spec:
  description: "Manages customer success initiatives"
  type: Declarative
  declarative:
    modelConfig: default-model-config
    systemMessage: "You are a customer success manager..."
  tools:
    - type: McpServer
      mcpServer:
        name: crm-server
```

### Marketplace Listing (Stored in our Backend)
```json
{
  "id": "uuid",
  "kagent_agent_name": "customer-success-manager",
  "kagent_namespace": "default",
  "pricing_monthly": 99,
  "token_billing": "customer_pays",
  "estimated_usage": "medium",
  "tags": ["customer-success", "manager", "b2b"],
  "category": "Customer Success",
  "status": "stable",
  "featured": true,
  "marketing_description": "Strategic customer success management...",
  "icon_url": "https://...",
  "published": true,
  "created_at": "2025-11-26T12:00:00Z",
  "updated_at": "2025-11-26T12:00:00Z"
}
```

---

## ✅ Benefits

1. **Separation of Concerns:**
   - KAgent Dashboard = Agent development
   - Admin Frontend = Marketplace curation
   - Agent Gateway = Runtime operations

2. **Simpler Admin Frontend:**
   - No complex agent creation wizard
   - Just metadata forms
   - Faster development

3. **Leverages Existing Tools:**
   - KAgent Dashboard is purpose-built for agent creation
   - Agent Gateway provides production-grade auth/observability
   - We focus on marketplace features

4. **Easier Maintenance:**
   - Agent schema changes handled by KAgent
   - We only maintain marketplace metadata schema

---

## 🚀 Implementation Plan

1. ✅ Restore v2.0 pages (AgentBrowser, MarketplaceEditor)
2. ✅ Remove VECreatorWizard (archive it)
3. ✅ Update kagentApi to use Agent Gateway endpoints
4. ✅ Add authentication to Agent Gateway calls
5. ✅ Update MarketplaceEditor to save to backend
6. ✅ Test end-to-end flow

---

**Status:** ✅ APPROVED - Proceeding with implementation
