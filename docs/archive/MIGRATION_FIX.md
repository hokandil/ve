# Quick Fix: Apply Migration 006 to Supabase

The hire functionality is failing because the database is missing the new columns from migration `006_shared_agents.sql`.

## Solution

Run this SQL in your **Supabase SQL Editor**:

```sql
-- Update customer_ves table for shared agent architecture
ALTER TABLE customer_ves 
  ADD COLUMN IF NOT EXISTS agent_type TEXT,
  ADD COLUMN IF NOT EXISTS agent_gateway_route TEXT;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_customer_ves_agent_type ON customer_ves(agent_type, customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_route ON customer_ves(agent_gateway_route);

-- Add comments
COMMENT ON COLUMN customer_ves.agent_type IS 'Type of shared agent (e.g., marketing-manager)';
COMMENT ON COLUMN customer_ves.agent_gateway_route IS 'Route path to access shared agent';
```

## Steps

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar
4. Click "New Query"
5. Paste the SQL above
6. Click "Run" or press Ctrl+Enter
7. Refresh the frontend and try hiring again

## What This Does

- Adds `agent_type` column to store the shared agent type (e.g., "marketing-manager", "wellness")
- Adds `agent_gateway_route` column to store the route path (e.g., "/agents/customer-123/wellness")
- Creates indexes for better query performance

After applying this migration, the hire functionality will work correctly!
