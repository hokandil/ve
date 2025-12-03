#!/bin/bash
# VE SaaS Platform - Development Environment Setup Script

set -e

echo "🚀 Setting up VE SaaS Development Environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create project structure
echo -e "${BLUE}📁 Creating project structure...${NC}"
mkdir -p backend/{app,tests}
mkdir -p frontend/{src,public}
mkdir -p supabase
mkdir -p kubeconfig
mkdir -p agent-gateway-config
mkdir -p kagent-manifests

# Create Supabase init SQL
echo -e "${BLUE}🗄️  Creating Supabase schema...${NC}"
cat > supabase/init.sql << 'EOF'
-- VE SaaS Platform Database Schema

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Customers table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    industry VARCHAR(100),
    company_size VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subscription_status VARCHAR(50) DEFAULT 'active',
    subscription_tier VARCHAR(50) DEFAULT 'starter'
);

-- Virtual Employees (Templates in marketplace)
CREATE TABLE virtual_employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    role VARCHAR(255) NOT NULL,
    department VARCHAR(100) NOT NULL,
    seniority_level VARCHAR(50) NOT NULL CHECK (seniority_level IN ('junior', 'senior', 'manager')),
    description TEXT,
    capabilities JSONB,
    tools JSONB,
    pricing_monthly DECIMAL(10, 2),
    framework VARCHAR(50) DEFAULT 'crewai',
    status VARCHAR(50) DEFAULT 'beta' CHECK (status IN ('beta', 'alpha', 'stable')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Customer VEs (Hired instances)
CREATE TABLE customer_ves (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    ve_id UUID NOT NULL REFERENCES virtual_employees(id),
    persona_name VARCHAR(255) NOT NULL,
    persona_email VARCHAR(255) NOT NULL,
    hired_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    namespace VARCHAR(100) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    position_x INTEGER,
    position_y INTEGER,
    UNIQUE(customer_id, persona_email)
);

-- VE Connections (Org chart relationships)
CREATE TABLE ve_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    from_ve_id UUID NOT NULL REFERENCES customer_ves(id) ON DELETE CASCADE,
    to_ve_id UUID NOT NULL REFERENCES customer_ves(id) ON DELETE CASCADE,
    connection_type VARCHAR(50) NOT NULL CHECK (connection_type IN ('vertical', 'horizontal')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(from_ve_id, to_ve_id)
);

-- Tasks/Conversations
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_by_user BOOLEAN DEFAULT TRUE,
    assigned_to_ve UUID REFERENCES customer_ves(id),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'review', 'completed', 'cancelled')),
    priority VARCHAR(50) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    due_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Messages (Email-like interface)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id UUID REFERENCES tasks(id) ON DELETE CASCADE,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    from_type VARCHAR(50) NOT NULL CHECK (from_type IN ('customer', 've')),
    from_user_id UUID REFERENCES customers(id),
    from_ve_id UUID REFERENCES customer_ves(id),
    to_type VARCHAR(50) NOT NULL CHECK (to_type IN ('customer', 've')),
    to_user_id UUID REFERENCES customers(id),
    to_ve_id UUID REFERENCES customer_ves(id),
    subject VARCHAR(255),
    content TEXT NOT NULL,
    message_type VARCHAR(50) DEFAULT 'email' CHECK (message_type IN ('email', 'chat', 'system')),
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Token Usage (Billing)
CREATE TABLE token_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    ve_id UUID REFERENCES customer_ves(id),
    operation VARCHAR(100) NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    cost DECIMAL(10, 6) NOT NULL,
    model VARCHAR(100),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Company Knowledge Base
CREATE TABLE company_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    content_type VARCHAR(50),
    embeddings VECTOR(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- VE Context/Memory
CREATE TABLE ve_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_ve_id UUID NOT NULL REFERENCES customer_ves(id) ON DELETE CASCADE,
    context_data JSONB NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_customer_ves_customer ON customer_ves(customer_id);
CREATE INDEX idx_tasks_customer ON tasks(customer_id);
CREATE INDEX idx_tasks_assigned ON tasks(assigned_to_ve);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_messages_task ON messages(task_id);
CREATE INDEX idx_messages_customer ON messages(customer_id);
CREATE INDEX idx_token_usage_customer ON token_usage(customer_id);
CREATE INDEX idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX idx_knowledge_customer ON company_knowledge(customer_id);

-- Enable Row Level Security
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_ves ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE company_knowledge ENABLE ROW LEVEL SECURITY;

-- RLS Policies (customers can only see their own data)
CREATE POLICY "Customers can view own data" ON customers
    FOR SELECT USING (auth.uid()::TEXT = id::TEXT);

CREATE POLICY "Customers can view own VEs" ON customer_ves
    FOR SELECT USING (customer_id::TEXT = auth.uid()::TEXT);

CREATE POLICY "Customers can view own tasks" ON tasks
    FOR SELECT USING (customer_id::TEXT = auth.uid()::TEXT);

CREATE POLICY "Customers can view own messages" ON messages
    FOR SELECT USING (customer_id::TEXT = auth.uid()::TEXT);

-- Insert sample marketplace VEs
INSERT INTO virtual_employees (name, role, department, seniority_level, description, capabilities, pricing_monthly, status) VALUES
('Marketing Manager', 'Marketing Manager', 'Marketing', 'manager', 'Strategic marketing leadership and campaign management', '{"delegation": true, "strategy": true, "analytics": true}', 99.00, 'stable'),
('Marketing Senior', 'Senior Marketing Specialist', 'Marketing', 'senior', 'Execute marketing campaigns and content strategy', '{"content_creation": true, "analytics": true, "SEO": true}', 59.00, 'stable'),
('Marketing Junior', 'Junior Content Creator', 'Marketing', 'junior', 'Create marketing content and social media posts', '{"content_creation": true, "social_media": true}', 29.00, 'stable'),
('Customer Support Manager', 'Customer Support Manager', 'Support', 'manager', 'Manage customer support operations', '{"delegation": true, "escalation": true}', 99.00, 'beta'),
('Customer Support Senior', 'Senior Support Specialist', 'Support', 'senior', 'Handle complex customer issues', '{"technical_support": true, "troubleshooting": true}', 59.00, 'beta'),
('Customer Support Junior', 'Junior Support Agent', 'Support', 'junior', 'Handle basic customer inquiries', '{"ticket_management": true, "basic_troubleshooting": true}', 29.00, 'beta');
EOF

# Create Kong configuration
echo -e "${BLUE}🌐 Creating Kong API Gateway config...${NC}"
cat > kong.yml << 'EOF'
_format_version: "2.1"

services:
  - name: supabase-rest
    url: http://supabase-rest:3000
    routes:
      - name: rest-route
        paths:
          - /rest/v1
        strip_path: true

  - name: supabase-auth
    url: http://supabase-auth:9999
    routes:
      - name: auth-route
        paths:
          - /auth/v1
        strip_path: true

  - name: supabase-storage
    url: http://supabase-storage:5000
    routes:
      - name: storage-route
        paths:
          - /storage/v1
        strip_path: true
EOF

# Create backend Dockerfile
echo -e "${BLUE}🐍 Creating Backend Dockerfile...${NC}"
cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

# Create backend requirements
cat > backend/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
supabase==2.3.0
redis==5.0.1
kubernetes==28.1.0
crewai==0.1.0
openai==1.3.0
anthropic==0.7.0
asyncpg==0.29.0
sqlalchemy==2.0.23
alembic==1.13.0
httpx==0.25.2
EOF

# Create frontend Dockerfile
echo -e "${BLUE}⚛️  Creating Frontend Dockerfile...${NC}"
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "start"]
EOF

# Create frontend package.json
cat > frontend/package.json << 'EOF'
{
  "name": "ve-saas-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@supabase/supabase-js": "^2.39.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "reactflow": "^11.10.0",
    "@dnd-kit/core": "^6.1.0",
    "axios": "^1.6.2",
    "date-fns": "^2.30.0",
    "tailwindcss": "^3.3.6",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
EOF

# Create .env.example
cat > .env.example << 'EOF'
# Supabase
SUPABASE_URL=http://localhost:8000
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU

# Database
DATABASE_URL=postgresql://postgres:postgres_password@localhost:5432/postgres

# Redis
REDIS_URL=redis://localhost:6379

# Kubernetes
K8S_API_URL=https://localhost:6443

# Agent Gateway
AGENT_GATEWAY_URL=http://localhost:8081

# JWT
JWT_SECRET=super-secret-jwt-token-with-at-least-32-characters-long

# LLM Providers (Add your keys)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
EOF

echo -e "${GREEN}✅ Project structure created!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run: docker-compose up -d"
echo "3. Access services:"
echo "   - Portainer: http://localhost:9000"
echo "   - Supabase Studio: http://localhost:3001"
echo "   - Backend API: http://localhost:8001"
echo "   - Frontend: http://localhost:3002"
echo "   - n8n: http://localhost:5678 (admin/admin123)"
echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
