-- Enable Row Level Security on critical tables
ALTER TABLE customer_ves ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- Policy for customer_ves: customer_id is UUID type
CREATE POLICY "Users can view their own hired agents"
ON customer_ves
FOR SELECT
USING (auth.uid() = customer_id);

CREATE POLICY "Users can hire agents"
ON customer_ves
FOR INSERT
WITH CHECK (auth.uid() = customer_id);

CREATE POLICY "Users can update their own agents"
ON customer_ves
FOR UPDATE
USING (auth.uid() = customer_id);

CREATE POLICY "Users can unhire their own agents"
ON customer_ves
FOR DELETE
USING (auth.uid() = customer_id);

-- Policy for tasks: customer_id is UUID type
CREATE POLICY "Users can view their own tasks"
ON tasks
FOR SELECT
USING (auth.uid() = customer_id);

CREATE POLICY "Users can create tasks"
ON tasks
FOR INSERT
WITH CHECK (auth.uid() = customer_id);

CREATE POLICY "Users can update their own tasks"
ON tasks
FOR UPDATE
USING (auth.uid() = customer_id);

-- Policy for messages: customer_id is UUID type
CREATE POLICY "Users can view their own messages"
ON messages
FOR SELECT
USING (auth.uid() = customer_id);

CREATE POLICY "Users can send messages"
ON messages
FOR INSERT
WITH CHECK (auth.uid() = customer_id);

-- Service Role Bypass (for backend services)
-- Note: Supabase service_role key bypasses RLS automatically, 
-- but explicit policies for 'service_role' can be added if needed.

-- Note: memories table will be added in a future migration when implemented
