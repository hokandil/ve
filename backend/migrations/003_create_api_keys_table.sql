-- Migration: Create API Keys table for agent authentication
-- Date: 2025-11-26

-- Create api_keys table
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_type TEXT NOT NULL DEFAULT 'agent', -- 'agent' or 'service'
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    
    CONSTRAINT api_keys_key_type_check CHECK (key_type IN ('agent', 'service'))
);

-- Create indexes
CREATE INDEX idx_api_keys_customer_id ON api_keys(customer_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash) WHERE is_active = true;
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Enable RLS
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- RLS Policies
-- Customers can only see their own API keys
CREATE POLICY api_keys_select_policy ON api_keys
    FOR SELECT
    USING (customer_id = auth.uid());

-- Customers can only insert their own API keys
CREATE POLICY api_keys_insert_policy ON api_keys
    FOR INSERT
    WITH CHECK (customer_id = auth.uid());

-- Customers can only update their own API keys
CREATE POLICY api_keys_update_policy ON api_keys
    FOR UPDATE
    USING (customer_id = auth.uid());

-- Customers can only delete their own API keys
CREATE POLICY api_keys_delete_policy ON api_keys
    FOR DELETE
    USING (customer_id = auth.uid());

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON api_keys TO service_role;

-- Add comment
COMMENT ON TABLE api_keys IS 'API keys for agent and service authentication';
COMMENT ON COLUMN api_keys.key_hash IS 'SHA-256 hash of the API key';
COMMENT ON COLUMN api_keys.key_type IS 'Type of key: agent (for VE agents) or service (for external services)';
COMMENT ON COLUMN api_keys.metadata IS 'Additional metadata about the key (e.g., permissions, scope)';
