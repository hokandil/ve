-- ============================================================================
-- VE SaaS Platform - Current Database Schema (As-Is State)
-- Generated: 2025-12-03
-- Project: ozbawcpschdsglvvalgu
-- ============================================================================
-- This file documents the ACTUAL current state of the database
-- Use this as the source of truth for schema understanding
-- ============================================================================

-- ============================================================================
-- TABLE: customers
-- Purpose: Store customer/organization information
-- ============================================================================
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT now(),
    subscription_tier VARCHAR(50) DEFAULT 'free',
    subscription_status VARCHAR(50) DEFAULT 'active'
);

-- ============================================================================
-- TABLE: virtual_employees (Marketplace Agents)
-- Purpose: Catalog of available AI agents in the marketplace
-- Note: This is the "marketplace_agents" table (kept as virtual_employees for compatibility)
-- ============================================================================
CREATE TABLE IF NOT EXISTS virtual_employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    department VARCHAR(255) NOT NULL,
    seniority_level VARCHAR(50) CHECK (seniority_level IN ('junior', 'senior', 'manager')),
    description TEXT,
    capabilities JSONB,
    tools JSONB,
    pricing_monthly NUMERIC(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'stable' CHECK (status IN ('stable', 'beta', 'experimental')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Marketplace metadata
    source VARCHAR(100) DEFAULT 'internal',  -- 'kagent', 'registry', 'internal'
    source_id VARCHAR(255),  -- External ID from source system
    token_billing_model VARCHAR(50) DEFAULT 'customer_pays',  -- 'included', 'customer_pays'
    estimated_usage VARCHAR(50) DEFAULT 'medium',  -- 'low', 'medium', 'high'
    tags TEXT[] DEFAULT '{}',
    category VARCHAR(100) DEFAULT 'general',
    featured BOOLEAN DEFAULT false,
    icon_url VARCHAR(500),
    screenshots TEXT[] DEFAULT '{}',
    marketing_description TEXT,
    last_synced_at TIMESTAMP,
    sync_status VARCHAR(50)
);

-- ============================================================================
-- TABLE: customer_ves
-- Purpose: Track which agents customers have hired (instances)
-- RLS: Enabled - customers can only see their own hired agents
-- ============================================================================
CREATE TABLE IF NOT EXISTS customer_ves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    marketplace_agent_id UUID NOT NULL REFERENCES virtual_employees(id) ON DELETE CASCADE,
    
    -- Agent deployment info (legacy Kubernetes fields - now using shared namespace)
    agent_name VARCHAR(255),  -- Nullable - legacy field
    agent_namespace VARCHAR(255),  -- Nullable - legacy field
    
    -- Personalization
    persona_name VARCHAR(255) NOT NULL,  -- Custom name given by customer
    persona_email VARCHAR(255),
    
    -- Shared agent routing
    agent_gateway_route_id VARCHAR(255),  -- Route ID in Agent Gateway
    
    -- Lifecycle
    hired_at TIMESTAMP NOT NULL DEFAULT now(),
    status VARCHAR(50) DEFAULT 'active',
    
    -- Shared agent model (new columns)
    agent_type TEXT,  -- Type of shared agent (e.g., 'marketing-manager')
    agent_gateway_route TEXT,  -- Route path to access shared agent
    
    UNIQUE(customer_id, marketplace_agent_id)
);

-- Enable RLS
ALTER TABLE customer_ves ENABLE ROW LEVEL SECURITY;

-- RLS Policies for customer_ves
CREATE POLICY customer_ves_select ON customer_ves
    FOR SELECT USING (auth.uid() = customer_id);

CREATE POLICY customer_ves_insert ON customer_ves
    FOR INSERT WITH CHECK (auth.uid() = customer_id);

CREATE POLICY customer_ves_update ON customer_ves
    FOR UPDATE USING (auth.uid() = customer_id);

CREATE POLICY customer_ves_delete ON customer_ves
    FOR DELETE USING (auth.uid() = customer_id);

-- ============================================================================
-- TABLE: tasks
-- Purpose: Task management and assignment to VEs
-- RLS: Enabled - customers can only see their own tasks
-- ============================================================================
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')),
    priority VARCHAR(50) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    assigned_to_ve UUID REFERENCES customer_ves(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    due_date TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    
    -- Task metadata
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Task threading
    parent_task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    thread_id UUID
);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policies for tasks
CREATE POLICY tasks_select ON tasks
    FOR SELECT USING (auth.uid() = customer_id);

CREATE POLICY tasks_insert ON tasks
    FOR INSERT WITH CHECK (auth.uid() = customer_id);

CREATE POLICY tasks_update ON tasks
    FOR UPDATE USING (auth.uid() = customer_id);

-- ============================================================================
-- TABLE: messages
-- Purpose: Chat messages between customers and VEs
-- RLS: Enabled - customers can only see their own messages
-- ============================================================================
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    customer_ve_id UUID REFERENCES customer_ves(id) ON DELETE CASCADE,
    
    -- Message direction
    from_type VARCHAR(50) NOT NULL CHECK (from_type IN ('customer', 've', 'system')),
    from_ve_id UUID REFERENCES customer_ves(id) ON DELETE SET NULL,
    to_ve_id UUID REFERENCES customer_ves(id) ON DELETE SET NULL,
    
    -- Content
    subject VARCHAR(255),
    content TEXT NOT NULL,
    
    -- Threading
    thread_id UUID,
    replied_to_id UUID REFERENCES messages(id) ON DELETE SET NULL,
    
    -- Metadata
    read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Enable RLS
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies for messages
CREATE POLICY messages_select ON messages
    FOR SELECT USING (auth.uid() = customer_id);

CREATE POLICY messages_insert ON messages
    FOR INSERT WITH CHECK (auth.uid() = customer_id);

-- ============================================================================
-- TABLE: token_usage
-- Purpose: Track LLM token usage for billing
-- RLS: Enabled - customers can only see their own usage
-- ============================================================================
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    ve_id UUID REFERENCES customer_ves(id) ON DELETE SET NULL,
    operation VARCHAR(255) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost NUMERIC(10, 4) NOT NULL,
    model VARCHAR(100),
    timestamp TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- RLS Policy for token_usage
CREATE POLICY token_usage_select ON token_usage
    FOR SELECT USING (auth.uid() = customer_id);

-- ============================================================================
-- TABLE: ve_connections
-- Purpose: Track organizational relationships between VEs
-- ============================================================================
CREATE TABLE IF NOT EXISTS ve_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    from_ve_id UUID NOT NULL,
    to_ve_id UUID NOT NULL,
    connection_type VARCHAR(50) CHECK (connection_type IN ('vertical', 'horizontal')),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================================
-- TABLE: api_keys (if exists)
-- Purpose: API keys for programmatic access
-- ============================================================================
-- Note: Check if this table exists in your database

-- ============================================================================
-- TABLE: security_audit_log (if exists)
-- Purpose: Security event logging
-- ============================================================================
-- Note: Check if this table exists in your database

-- ============================================================================
-- INDEXES (Performance Optimization)
-- ============================================================================

-- Customer VEs indexes
CREATE INDEX IF NOT EXISTS idx_customer_ves_customer_id ON customer_ves(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_marketplace_agent_id ON customer_ves(marketplace_agent_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_status ON customer_ves(status);

-- Tasks indexes
CREATE INDEX IF NOT EXISTS idx_tasks_customer_id ON tasks(customer_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_ve ON tasks(assigned_to_ve);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at);

-- Messages indexes
CREATE INDEX IF NOT EXISTS idx_messages_customer_id ON messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_customer_ve_id ON messages(customer_ve_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Token usage indexes
CREATE INDEX IF NOT EXISTS idx_token_usage_customer_id ON token_usage(customer_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_ve_id ON token_usage(ve_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp);

-- Virtual employees indexes
CREATE INDEX IF NOT EXISTS idx_virtual_employees_department ON virtual_employees(department);
CREATE INDEX IF NOT EXISTS idx_virtual_employees_seniority_level ON virtual_employees(seniority_level);
CREATE INDEX IF NOT EXISTS idx_virtual_employees_status ON virtual_employees(status);
CREATE INDEX IF NOT EXISTS idx_virtual_employees_source ON virtual_employees(source);

-- ============================================================================
-- APPLIED MIGRATIONS (Historical Record)
-- ============================================================================
-- 20251125081720 - add_task_fields
-- 20251125091645 - add_message_threading
-- 20251127020139 - prd_alignment_v2_retry
-- 20251127055608 - 002_indexes_v2
-- 20251128142511 - add_shared_agent_columns
-- 20251128142701 - make_agent_name_nullable
-- 20251203060608 - enable_rls

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. The 'virtual_employees' table serves as the marketplace catalog
-- 2. The 'customer_ves' table tracks hired instances with personalization
-- 3. RLS is enabled on: customer_ves, tasks, messages, token_usage
-- 4. Shared namespace model: All agents deploy to 'agents-system' namespace
-- 5. Network isolation via Kubernetes NetworkPolicies (not in DB)
-- 6. ServiceAccounts created per customer (not in DB)
