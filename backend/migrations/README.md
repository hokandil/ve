# Database Migrations - README

## Current Status

The database schema has evolved through multiple migrations applied directly via Supabase MCP. The migration files in this directory may not perfectly match the current database state.

**✅ Source of Truth:** `CURRENT_SCHEMA.sql` - This file documents the ACTUAL current state of the database as of 2025-12-03.

## Applied Migrations (via Supabase)

The following migrations have been applied to project `ozbawcpschdsglvvalgu`:

1. `20251125081720` - add_task_fields
2. `20251125091645` - add_message_threading  
3. `20251127020139` - prd_alignment_v2_retry
4. `20251127055608` - 002_indexes_v2
5. `20251128142511` - add_shared_agent_columns
6. `20251128142701` - make_agent_name_nullable
7. `20251203060608` - enable_rls

## Current Schema Overview

### Core Tables

#### 1. `customers`
- Customer/organization accounts
- Subscription management
- **RLS:** Not enabled (admin access only)

#### 2. `virtual_employees` (Marketplace Agents)
- Catalog of available AI agents
- Marketplace metadata (pricing, tags, categories)
- Source tracking (kagent, registry, internal)
- **RLS:** Not enabled (public marketplace)

#### 3. `customer_ves` (Hired Agent Instances)
- Tracks which agents customers have hired
- Personalization (custom names, emails)
- Shared agent routing information
- **RLS:** ✅ Enabled - `auth.uid() = customer_id`

#### 4. `tasks`
- Task management and assignment
- VE assignment tracking
- Task threading support
- **RLS:** ✅ Enabled - `auth.uid() = customer_id`

#### 5. `messages`
- Chat messages between customers and VEs
- Message threading
- Read/unread tracking
- **RLS:** ✅ Enabled - `auth.uid() = customer_id`

#### 6. `token_usage`
- LLM token usage tracking for billing
- Cost calculation
- **RLS:** ✅ Enabled - `auth.uid() = customer_id`

#### 7. `ve_connections`
- Organizational relationships between VEs
- Vertical (manager-subordinate) and horizontal (peer) connections
- **RLS:** Not enabled

## Migration Files in This Directory

### Active/Reference Files
- `CURRENT_SCHEMA.sql` - **SOURCE OF TRUTH** - Current database state
- `003_enable_rls.sql` - RLS policies (applied as migration 20251203060608)

### Legacy/Historical Files
These files represent earlier migration attempts and may not match current schema:
- `001_prd_alignment.sql` - Initial schema alignment
- `002_indexes.sql` - Performance indexes
- `003_create_api_keys_table.sql` - API keys table (may not be applied)
- `004_security_audit_log.sql` - Audit logging (may not be applied)
- `004_update_virtual_employees_table.sql` - Marketplace metadata
- `005_agent_memory_rls.sql` - Memory table RLS (table may not exist)
- `006_shared_agents.sql` - Shared agent columns

## How to Apply New Migrations

### Using Supabase MCP (Recommended)

```python
from mcp import mcp1_apply_migration

# Apply a new migration
mcp1_apply_migration(
    project_id="ozbawcpschdsglvvalgu",
    name="descriptive_migration_name",
    query="""
    -- Your SQL here
    ALTER TABLE ...
    """
)
```

### Manual SQL (Alternative)

1. Connect to Supabase SQL Editor
2. Run your SQL directly
3. Document the change in this README

## Schema Verification

To verify current schema matches `CURRENT_SCHEMA.sql`:

```python
from mcp import mcp1_list_tables

# Get current schema
tables = mcp1_list_tables(
    project_id="ozbawcpschdsglvvalgu",
    schemas=["public"]
)
```

## Important Notes

### 1. Shared Namespace Model
- All agents deploy to `agents-system` Kubernetes namespace
- Network isolation via NetworkPolicies (not in database)
- ServiceAccounts created per customer (not in database)

### 2. RLS Policies
All RLS policies use `auth.uid() = customer_id` for tenant isolation:
- ✅ `customer_ves` - Full CRUD policies
- ✅ `tasks` - SELECT, INSERT, UPDATE policies
- ✅ `messages` - SELECT, INSERT policies
- ✅ `token_usage` - SELECT policy

### 3. Indexes
Performance indexes exist on:
- Foreign keys (customer_id, ve_id, etc.)
- Frequently queried columns (status, created_at, etc.)
- Thread IDs for message threading

### 4. Data Types
- **UUIDs:** All primary keys and foreign keys
- **Timestamps:** `TIMESTAMPTZ` for timezone awareness
- **JSONB:** For flexible metadata storage
- **Arrays:** For tags and screenshots

## Troubleshooting

### Schema Mismatch
If migration files don't match database:
1. Refer to `CURRENT_SCHEMA.sql` as source of truth
2. Check applied migrations list above
3. Use MCP to inspect actual schema

### RLS Issues
If RLS blocking legitimate access:
1. Verify `auth.uid()` is set correctly
2. Check policy definitions in `CURRENT_SCHEMA.sql`
3. Use admin client for testing (bypasses RLS)

### Missing Tables
If a table referenced in old migrations doesn't exist:
1. Check `CURRENT_SCHEMA.sql` for actual tables
2. Table may have been renamed or removed
3. Use `mcp1_list_tables()` to verify

## Future Migrations

When creating new migrations:
1. Use descriptive names (e.g., `add_agent_memory_table`)
2. Apply via MCP for automatic tracking
3. Update `CURRENT_SCHEMA.sql` after applying
4. Document in this README's "Applied Migrations" section

## Contact

For schema questions or migration issues:
- Check `CURRENT_SCHEMA.sql` first
- Review applied migrations list
- Use MCP tools to inspect actual database state
