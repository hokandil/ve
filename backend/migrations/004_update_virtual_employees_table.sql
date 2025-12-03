-- Migration: Update virtual_employees table for marketplace metadata
-- Date: 2025-11-26

-- Add new columns to virtual_employees table
ALTER TABLE virtual_employees
ADD COLUMN IF NOT EXISTS namespace TEXT DEFAULT 'default',
ADD COLUMN IF NOT EXISTS token_billing TEXT DEFAULT 'customer_pays',
ADD COLUMN IF NOT EXISTS estimated_usage TEXT DEFAULT 'medium',
ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS category TEXT,
ADD COLUMN IF NOT EXISTS featured BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS icon_url TEXT,
ADD COLUMN IF NOT EXISTS screenshots TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS marketing_description TEXT;

-- Add check constraints
ALTER TABLE virtual_employees
ADD CONSTRAINT check_token_billing CHECK (token_billing IN ('customer_pays', 'included')),
ADD CONSTRAINT check_estimated_usage CHECK (estimated_usage IN ('light', 'medium', 'heavy'));

-- Create index on category and tags for faster filtering
CREATE INDEX IF NOT EXISTS idx_ve_category ON virtual_employees(category);
CREATE INDEX IF NOT EXISTS idx_ve_featured ON virtual_employees(featured) WHERE featured = true;
CREATE INDEX IF NOT EXISTS idx_ve_tags ON virtual_employees USING GIN(tags);

-- Comment on columns
COMMENT ON COLUMN virtual_employees.namespace IS 'Kubernetes namespace where the agent template resides';
COMMENT ON COLUMN virtual_employees.token_billing IS 'Billing model for tokens: customer_pays or included';
COMMENT ON COLUMN virtual_employees.estimated_usage IS 'Estimated token usage level: light, medium, heavy';
COMMENT ON COLUMN virtual_employees.tags IS 'Searchable tags for the marketplace';
