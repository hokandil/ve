-- Add missing columns to messages table
ALTER TABLE messages ADD COLUMN IF NOT EXISTS to_ve_id UUID;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS from_ve_id UUID;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS subject TEXT;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS thread_id UUID;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS replied_to_id UUID;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS message_type TEXT DEFAULT 'email';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS read BOOLEAN DEFAULT FALSE;

-- Indexes for performance optimization

-- Customer VEs
CREATE INDEX IF NOT EXISTS idx_customer_ves_customer_id ON customer_ves(customer_id);
CREATE INDEX IF NOT EXISTS idx_customer_ves_marketplace_agent_id ON customer_ves(marketplace_agent_id);

-- Messages
CREATE INDEX IF NOT EXISTS idx_messages_customer_id ON messages(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_to_ve_id ON messages(to_ve_id);
CREATE INDEX IF NOT EXISTS idx_messages_from_ve_id ON messages(from_ve_id);

-- Tasks
CREATE INDEX IF NOT EXISTS idx_tasks_customer_id ON tasks(customer_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_ve ON tasks(assigned_to_ve);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Token Usage
CREATE INDEX IF NOT EXISTS idx_token_usage_customer_id ON token_usage(customer_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_ve_id ON token_usage(ve_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_timestamp ON token_usage(timestamp);
