"""
Database migration script to align with PRD v2.0 schema.

This script will:
1. Add new columns to virtual_employees table for marketplace metadata
2. Create customer_ves table for hired VE instances
3. Update tasks table schema
4. Create messages table for chat history

Run this after backing up your database!
"""

-- Add marketplace metadata columns to virtual_employees
ALTER TABLE virtual_employees
ADD COLUMN IF NOT EXISTS source VARCHAR(50) DEFAULT 'custom',
ADD COLUMN IF NOT EXISTS source_id VARCHAR(255),
ADD COLUMN IF NOT EXISTS kagent_namespace VARCHAR(255),
ADD COLUMN IF NOT EXISTS kagent_version VARCHAR(50),
ADD COLUMN IF NOT EXISTS token_billing VARCHAR(50) DEFAULT 'customer_pays',
ADD COLUMN IF NOT EXISTS estimated_usage VARCHAR(50) DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'general',
ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS icon_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS screenshots TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS marketing_description TEXT,
ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS sync_status VARCHAR(50);

-- Create customer_ves table (hired VE instances)
CREATE TABLE IF NOT EXISTS customer_ves (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    marketplace_agent_id UUID NOT NULL REFERENCES virtual_employees(id) ON DELETE CASCADE,
    agent_name VARCHAR(255) NOT NULL,
    agent_namespace VARCHAR(255),
    persona_name VARCHAR(255) NOT NULL,
    persona_email VARCHAR(255),
    agent_gateway_route_id VARCHAR(255),
    hired_at TIMESTAMP NOT NULL DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for customer_ves
CREATE INDEX IF NOT EXISTS idx_customer_ves_customer_id ON customer_ves(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_marketplace_agent_id ON customer_ves(marketplace_agent_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_status ON customer_ves(status);

-- Update tasks table to reference customer_ves
ALTER TABLE tasks
ADD COLUMN IF NOT EXISTS assigned_to_ve UUID REFERENCES customer_ves(id) ON DELETE SET NULL;

-- Create messages table for chat history
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    customer_ve_id UUID NOT NULL REFERENCES customer_ves(id) ON DELETE CASCADE,
    from_type VARCHAR(20) NOT NULL CHECK (from_type IN ('customer', 've')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for messages
CREATE INDEX IF NOT EXISTS idx_messages_customer_id ON messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_customer_ve_id ON messages(customer_ve_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at DESC);

-- Add comments for documentation
COMMENT ON TABLE customer_ves IS 'Hired VE instances - links customers to marketplace agents';
COMMENT ON TABLE messages IS 'Chat message history between customers and their VEs';
COMMENT ON COLUMN virtual_employees.source IS 'Source of agent: kagent, custom';
COMMENT ON COLUMN virtual_employees.source_id IS 'ID in source system (e.g., KAgent agent name)';
COMMENT ON COLUMN customer_ves.agent_gateway_route_id IS 'Route ID in Agent Gateway for this customer-VE pair';

-- Migration complete
SELECT 'Migration completed successfully!' as status;
