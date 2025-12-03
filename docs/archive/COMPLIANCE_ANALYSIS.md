# Admin Frontend Compliance Analysis

**Date:** November 26, 2025  
**Status:** ⚠️ NEEDS ADJUSTMENT

---

## 🚨 CRITICAL FINDING

After re-evaluating against the original scenario and PRD, I've identified a **major misalignment**:

### The Problem

**What I Built (v2.0):**
- Admin browses KAgent agents
- Admin adds pricing/tags to existing agents
- **Assumes agents are created in KAgent Dashboard by platform engineers**

**What the Scenario/PRD Actually Requires:**
- **Platform admins CREATE VEs** using a visual wizard
- VEs are **marketplace templates** that customers hire
- Admins define personality, capabilities, tools, pricing **all in one place**
- The wizard generates agent configurations that get deployed

---

## 📋 Scenario Analysis

### From `ve-saas-user-scenario.md`

**Sarah's Journey (Customer):**
1. Signs up
2. **Browses marketplace** - sees pre-made VE templates
3. **Hires VEs** like "Sarah Johnson - Marketing Manager"
4. VEs are **ready-made templates** with:
   - Defined personality
   - Specific capabilities
   - Pre-configured tools
   - Set pricing

**Key Insight:** VEs in the marketplace are **templates created by platform admins**, not individual KAgent agents.

### From `ve-admin-creator-interface.md`

**Admin's Job:**
1. **Create VE templates** using 6-step wizard:
   - Step 1: Basic Info (name, department, seniority)
   - Step 2: Personality & Backstory
   - Step 3: Capabilities (delegation, decision-making)
   - Step 4: Tools & MCP Servers
   - Step 5: Pricing
   - Step 6: Review & Deploy

2. **Publish to marketplace** - makes template available to customers

3. **When customer hires:**
   - System creates instance from template
   - Deploys to customer's namespace
   - Customizes with customer's name/email

---

## 🔄 Correct Architecture

### Two-Tier System

```
┌─────────────────────────────────────────────────────┐
│           ADMIN CREATES TEMPLATES                    │
│  (VE Creator Wizard - What I archived!)             │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Admin creates:                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ VE Template: "Marketing Manager"             │  │
│  │ - Personality: Strategic, experienced        │  │
│  │ - Can delegate: Yes                          │  │
│  │ - Tools: Analytics, SEO, Content             │  │
│  │ - Pricing: $99/month                         │  │
│  │ - Status: Stable                             │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Saved as: marketplace template in database        │
│                                                     │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│        CUSTOMER HIRES FROM MARKETPLACE               │
│  (User Frontend - Not built yet)                    │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Customer sees:                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │ Sarah Johnson                                │  │
│  │ Marketing Manager                            │  │
│  │ $99/month                                    │  │
│  │ [Hire Now]                                   │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  On hire:                                          │
│  1. Create customer_ves record                     │
│  2. Deploy KAgent Agent to customer namespace      │
│  3. Use template config as base                    │
│  4. Customize with customer's name                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## ❌ What's Wrong with v2.0

### Issue 1: Wrong Source of Truth

**v2.0 Assumption:**
- Agents exist in KAgent first
- Admin just adds metadata

**Reality:**
- Admin creates VE templates first
- Templates define everything (personality, tools, pricing)
- KAgent agents are created **when customers hire**, not before

### Issue 2: Missing Template Creation

**v2.0 Has:**
- Agent Browser (browse existing KAgent agents)
- Marketplace Editor (add pricing to agents)

**v2.0 Missing:**
- **VE Template Creator** - the 6-step wizard!
- Template storage (marketplace_templates table)
- Template → KAgent Agent deployment logic

### Issue 3: Workflow is Backwards

**v2.0 Workflow:**
```
1. Platform engineer creates agent in KAgent Dashboard
2. Admin browses KAgent agents
3. Admin adds pricing/tags
4. Published to marketplace
```

**Correct Workflow:**
```
1. Admin creates VE template in wizard
2. Template saved to database
3. Published to marketplace
4. Customer hires → KAgent agent created from template
```

---

## ✅ What Needs to Change

### Keep from v2.0
- ✅ UI components (Button, Input, Card, etc.)
- ✅ PublishedAgents page (manage templates)
- ✅ KAgent API client (for deployment)
- ✅ Build configuration

### Restore from v1.0
- ✅ **VECreatorWizard** - The 6-step template creator
- ✅ **All step components** (Step1-Step6)
- ✅ **Template-based YAML generation**

### Remove from v2.0
- ❌ AgentBrowser (browsing KAgent agents)
- ❌ MarketplaceEditor (adding metadata to existing agents)

### Add New
- ✅ Template storage logic
- ✅ Template → KAgent deployment on customer hire
- ✅ Template versioning

---

## 🎯 Corrected Admin Frontend Architecture

### Pages

1. **VE Templates** (`/templates`)
   - List all VE templates
   - Create new template button
   - Edit/delete templates
   - Publish/unpublish

2. **VE Creator Wizard** (`/create-template`)
   - 6-step wizard (from v1.0)
   - Creates VE template
   - Saves to database
   - Publishes to marketplace

3. **Playground** (`/playground`)
   - Test VE templates
   - Preview behavior

### Database Schema

```sql
-- VE Templates (created by admins)
CREATE TABLE ve_templates (
    id UUID PRIMARY KEY,
    name VARCHAR NOT NULL,
    department VARCHAR,
    seniority VARCHAR,
    role_definition TEXT,
    backstory TEXT,
    communication_style VARCHAR,
    can_delegate BOOLEAN,
    delegation_scope TEXT[],
    autonomous_budget DECIMAL,
    tools TEXT[],
    mcp_servers JSONB,
    pricing_monthly DECIMAL,
    token_billing VARCHAR,
    status VARCHAR, -- beta, alpha, stable
    published BOOLEAN DEFAULT false,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Customer VE Instances (created when customer hires)
CREATE TABLE customer_ves (
    id UUID PRIMARY KEY,
    customer_id UUID REFERENCES customers(id),
    template_id UUID REFERENCES ve_templates(id),
    persona_name VARCHAR, -- Custom name from customer
    persona_email VARCHAR,
    kagent_agent_name VARCHAR, -- Deployed agent name
    kagent_namespace VARCHAR, -- Customer's K8s namespace
    hired_at TIMESTAMP,
    status VARCHAR
);
```

### Workflow

```
Admin Workflow:
1. Admin opens VE Creator Wizard
2. Fills 6 steps (personality, capabilities, tools, pricing)
3. Reviews generated KAgent YAML
4. Saves as template
5. Publishes to marketplace

Customer Workflow:
1. Customer browses marketplace
2. Sees VE templates (created by admin)
3. Clicks "Hire"
4. Backend:
   a. Creates customer_ves record
   b. Generates KAgent YAML from template
   c. Deploys to customer's namespace
   d. Returns VE instance
```

---

## 🔧 Required Changes

### Immediate Actions

1. **Restore VECreatorWizard from archive**
   ```bash
   mv admin-frontend/src/_archive/VECreatorWizard.tsx admin-frontend/src/pages/
   mv admin-frontend/src/_archive/ve-creator admin-frontend/src/components/
   ```

2. **Remove incorrect pages**
   ```bash
   rm admin-frontend/src/pages/AgentBrowser.tsx
   rm admin-frontend/src/pages/MarketplaceEditor.tsx
   ```

3. **Update routes in App.tsx**
   ```typescript
   <Route path="/templates" element={<VETemplates />} />
   <Route path="/create-template" element={<VECreatorWizard />} />
   <Route path="/playground" element={<Playground />} />
   ```

4. **Rename PublishedAgents → VETemplates**
   - Change to show templates, not agents
   - Add "Create Template" button
   - Edit/delete templates

5. **Update VECreatorWizard**
   - Keep KAgent YAML generation
   - Save to `ve_templates` table (not deploy to KAgent yet)
   - Add "Publish to Marketplace" toggle

---

## 📊 Compliance Checklist

### Scenario Compliance
- [ ] Admin can create VE templates
- [ ] Templates have personality, capabilities, tools, pricing
- [ ] Templates published to marketplace
- [ ] Customers hire from marketplace (user frontend)
- [ ] Hiring creates KAgent agent instance

### PRD Compliance
- [ ] 6-step VE creation wizard
- [ ] Visual interface for non-technical admins
- [ ] YAML generation for KAgent
- [ ] Template management (CRUD)
- [ ] Marketplace publishing

### Architecture Compliance
- [ ] Templates stored in database
- [ ] KAgent agents created on customer hire
- [ ] One template → many customer instances
- [ ] Proper separation: template vs instance

---

## 🎯 Recommendation

**REVERT v2.0 CHANGES** and go back to v1.0 approach with improvements:

### v1.0 (Correct) + Improvements

**Keep:**
- VECreatorWizard (6-step template creator)
- KAgent YAML generation
- Template-based architecture

**Improve:**
- Better template management UI
- Template versioning
- Better YAML preview
- Deployment logic (template → customer instance)

**Add:**
- Template publishing workflow
- Customer hire integration
- Instance management

---

## ✅ Action Plan

1. **Restore v1.0 files from archive**
2. **Update database schema** (templates vs instances)
3. **Fix VECreatorWizard** to save templates
4. **Build template management UI**
5. **Implement hire workflow** (template → KAgent agent)
6. **Test end-to-end**

---

**Status:** ⚠️ **NEEDS CORRECTION**  
**Priority:** 🔴 **HIGH**  
**Impact:** Architecture misalignment with scenario/PRD

The v2.0 refactoring was based on a misunderstanding of the platform's purpose. We need to restore the template-based approach from v1.0.
