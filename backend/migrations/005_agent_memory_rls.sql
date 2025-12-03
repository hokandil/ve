-- Agent Memory Table with Row-Level Security
-- Stores agent memories with customer isolation enforced at database level

-- Create agent_memory table if not exists
CREATE TABLE IF NOT EXISTS agent_memory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL,
    agent_name TEXT NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    type TEXT DEFAULT 'conversation',
    session_id TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable Row-Level Security
ALTER TABLE agent_memory ENABLE ROW LEVEL SECURITY;

-- Drop existing policy if exists
DROP POLICY IF EXISTS customer_isolation ON agent_memory;

-- Create RLS policy: Users can only access their own customer's data
CREATE POLICY customer_isolation ON agent_memory
    FOR ALL
    USING (customer_id = current_setting('app.current_customer_id', true)::uuid);

-- Create function to set customer context
CREATE OR REPLACE FUNCTION set_customer_context(cust_id uuid)
RETURNS void AS $$
BEGIN
    PERFORM set_config('app.current_customer_id', cust_id::text, false);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Indexes for performance
CREATE INDEX idx_agent_memory_customer ON agent_memory(customer_id, timestamp DESC);
CREATE INDEX idx_agent_memory_agent ON agent_memory(agent_name, customer_id);
CREATE INDEX idx_agent_memory_session ON agent_memory(session_id) WHERE session_id IS NOT NULL;
CREATE INDEX idx_agent_memory_type ON agent_memory(type, customer_id);

-- Add comments
COMMENT ON TABLE agent_memory IS 'Agent memories with RLS enforcement for customer isolation';
COMMENT ON FUNCTION set_customer_context IS 'Sets customer context for RLS - MUST be called before queries';
