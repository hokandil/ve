-- Update customer_ves table for shared agent architecture
-- Migrates from per-customer agent deployment to shared agent routing

-- Add new columns for shared agent architecture
ALTER TABLE customer_ves 
  ADD COLUMN IF NOT EXISTS agent_type TEXT,
  ADD COLUMN IF NOT EXISTS agent_gateway_route TEXT;

-- Migrate existing data
UPDATE customer_ves 
SET agent_type = 'marketing-manager' 
WHERE agent_type IS NULL AND agent_name LIKE '%marketing%';

UPDATE customer_ves 
SET agent_gateway_route = '/agents/' || customer_id || '/' || agent_type
WHERE agent_gateway_route IS NULL AND agent_type IS NOT NULL;

-- Drop old columns (optional - comment out if you want to keep for rollback)
-- ALTER TABLE customer_ves 
--   DROP COLUMN IF EXISTS agent_name,
--   DROP COLUMN IF EXISTS agent_namespace,
--   DROP COLUMN IF EXISTS agent_gateway_route_id;

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_customer_ves_agent_type ON customer_ves(agent_type, customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_route ON customer_ves(agent_gateway_route);

-- Add comments
COMMENT ON COLUMN customer_ves.agent_type IS 'Type of shared agent (e.g., marketing-manager)';
COMMENT ON COLUMN customer_ves.agent_gateway_route IS 'Route path to access shared agent';
