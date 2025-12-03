# Agent Authentication System

## Overview

The VE SaaS platform now supports **dual authentication**:
1. **User JWT Authentication** - For human users via Supabase Auth
2. **API Key Authentication** - For VE agents and external services

This allows agents running in Kubernetes to authenticate and call backend APIs on behalf of customers.

---

## Authentication Flow

### User Authentication (Existing)
```
User → Login → Supabase Auth → JWT Token → API Request
```

### Agent Authentication (New)
```
Agent → API Key (from env) → API Request with X-API-Key header → Backend validates → Access granted
```

---

## API Key Format

API keys follow this format:
```
vek_<32-character-random-string>
```

Example:
```
vek_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
```

- **Prefix**: `vek_` (Virtual Employee Key)
- **Length**: 35 characters total
- **Storage**: SHA-256 hash stored in database (plain key never stored)
- **Security**: Cryptographically secure random generation

---

## Creating API Keys

### Via API (Recommended)

```bash
# Create an API key for an agent
curl -X POST http://localhost:8000/api/api-keys \
  -H "Authorization: Bearer $USER_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Marketing Manager Agent",
    "key_type": "agent",
    "metadata": {
      "ve_id": "ve-123",
      "role": "marketing_manager"
    }
  }'
```

Response:
```json
{
  "id": "key-uuid",
  "name": "Marketing Manager Agent",
  "key_type": "agent",
  "is_active": true,
  "created_at": "2025-11-26T...",
  "plain_key": "vek_a1b2c3d4...",  // ⚠️ Only shown once!
  "metadata": {
    "ve_id": "ve-123",
    "role": "marketing_manager"
  }
}
```

**⚠️ IMPORTANT**: The `plain_key` is only returned once during creation. Store it securely!

### Via Python Service

```python
from app.services.api_key_service import get_api_key_service

api_key_service = get_api_key_service()

result = await api_key_service.create_api_key(
    customer_id="customer-123",
    name="Senior Developer Agent",
    key_type="agent",
    metadata={"ve_id": "ve-456", "role": "senior_dev"}
)

# Store the plain_key securely
plain_key = result["plain_key"]
```

---

## Using API Keys

### HTTP Header

Agents include the API key in the `X-API-Key` header:

```bash
curl http://localhost:8000/api/knowledge/search \
  -H "X-API-Key: vek_a1b2c3d4..." \
  -H "Content-Type: application/json" \
  -d '{"query": "What is our product?", "limit": 5}'
```

### Python Example (for VE Agents)

```python
import httpx

async def call_backend_api(api_key: str, endpoint: str, data: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"http://backend:8000{endpoint}",
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json"
            },
            json=data
        )
        return response.json()

# Example: Search knowledge base
result = await call_backend_api(
    api_key=os.getenv("VE_API_KEY"),
    endpoint="/api/knowledge/search",
    data={"query": "company policies", "limit": 3}
)
```

---

## Key Types

### `agent` (Default)
- For VE agents running in Kubernetes
- Associated with a specific customer
- Can access customer data and perform actions
- Example: Marketing Manager VE, Senior Developer VE

### `service`
- For external services or integrations
- Can have broader or more restricted permissions
- Example: Monitoring service, backup service

---

## Security Features

### 1. **Hashed Storage**
- Plain keys are **never stored** in the database
- Only SHA-256 hashes are stored
- Even database admins cannot retrieve plain keys

### 2. **Revocation**
- Keys can be revoked instantly
- Revoked keys fail authentication immediately
- No need to rotate secrets across all agents

### 3. **Usage Tracking**
- `last_used_at` timestamp updated on each use
- Helps identify unused or compromised keys

### 4. **Customer Isolation**
- API keys are scoped to a single customer
- Cannot access other customers' data
- Enforced by RLS policies

---

## Managing API Keys

### List All Keys

```bash
GET /api/api-keys
Authorization: Bearer $USER_JWT
```

Response:
```json
[
  {
    "id": "key-1",
    "name": "Marketing Manager Agent",
    "key_type": "agent",
    "is_active": true,
    "created_at": "2025-11-26T...",
    "last_used_at": "2025-11-26T...",
    "metadata": {"ve_id": "ve-123"}
  }
]
```

Note: `plain_key` is **not** included in list responses.

### Revoke a Key

```bash
DELETE /api/api-keys/{key_id}
Authorization: Bearer $USER_JWT
```

---

## Kubernetes Integration

### Setting API Key in VE Deployment

When deploying a VE agent to Kubernetes, inject the API key as an environment variable:

```yaml
apiVersion: kagent.solo.io/v1
kind: Agent
metadata:
  name: marketing-manager
  namespace: customer-abc123
spec:
  env:
    - name: VE_API_KEY
      valueFrom:
        secretKeyRef:
          name: ve-api-keys
          key: marketing-manager-key
```

### Creating Kubernetes Secret

```bash
kubectl create secret generic ve-api-keys \
  --namespace=customer-abc123 \
  --from-literal=marketing-manager-key=vek_a1b2c3d4...
```

---

## Authentication Precedence

The `get_current_user` dependency checks authentication in this order:

1. **API Key** (`X-API-Key` header) - Checked first
2. **JWT Token** (`Authorization: Bearer` header) - Fallback

This means:
- Agents can use API keys
- Users can use JWT tokens
- Both work seamlessly with the same endpoints

---

## Restricting Endpoints to Agents Only

Some endpoints should only be callable by agents (not users). Use the `require_agent_auth` dependency:

```python
from app.core.security import require_agent_auth

@router.post("/internal/agent-action")
async def agent_only_endpoint(
    agent: dict = Depends(require_agent_auth)
):
    """This endpoint requires API key authentication"""
    # agent["key_name"] - Name of the API key
    # agent["key_type"] - "agent" or "service"
    # agent["metadata"] - Custom metadata
    ...
```

---

## Testing

### Create a Test API Key

```bash
# 1. Login as a user to get JWT
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Extract access_token from response
export USER_JWT="eyJ..."

# 2. Create API key
curl -X POST http://localhost:8000/api/api-keys \
  -H "Authorization: Bearer $USER_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Agent", "key_type": "agent"}'

# Extract plain_key from response
export API_KEY="vek_..."
```

### Test API Key Authentication

```bash
# Test with API key
curl http://localhost:8000/api/tasks \
  -H "X-API-Key: $API_KEY"

# Should return tasks for the customer
```

### Test Key Revocation

```bash
# Revoke the key
curl -X DELETE http://localhost:8000/api/api-keys/{key_id} \
  -H "Authorization: Bearer $USER_JWT"

# Try using revoked key (should fail)
curl http://localhost:8000/api/tasks \
  -H "X-API-Key: $API_KEY"

# Should return 401 Unauthorized
```

---

## Database Schema

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY,
    customer_id UUID NOT NULL REFERENCES customers(id),
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_type TEXT NOT NULL DEFAULT 'agent',
    is_active BOOLEAN NOT NULL DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ
);
```

---

## Best Practices

### 1. **One Key Per Agent**
Create a separate API key for each VE agent instance:
```
Marketing Manager → vek_abc123...
Senior Developer → vek_def456...
Junior Developer → vek_ghi789...
```

### 2. **Descriptive Names**
Use clear names that identify the agent:
```
✅ "Marketing Manager - Customer ABC"
✅ "Senior Dev - Project XYZ"
❌ "Key 1"
❌ "Test"
```

### 3. **Store Metadata**
Include useful metadata for tracking:
```json
{
  "ve_id": "ve-123",
  "role": "marketing_manager",
  "deployed_at": "2025-11-26",
  "namespace": "customer-abc123"
}
```

### 4. **Rotate Keys Regularly**
- Create new keys periodically
- Update Kubernetes secrets
- Revoke old keys

### 5. **Monitor Usage**
- Check `last_used_at` timestamps
- Revoke unused keys
- Alert on suspicious patterns

---

## Troubleshooting

### "Invalid API key" Error

**Cause**: Key is revoked, invalid, or doesn't exist

**Solution**:
1. Check if key is active: `GET /api/api-keys`
2. Verify key format: Should start with `vek_`
3. Create a new key if needed

### "No authentication credentials provided"

**Cause**: Neither API key nor JWT token provided

**Solution**:
- Add `X-API-Key` header for agents
- Add `Authorization: Bearer <token>` header for users

### "This endpoint requires agent authentication"

**Cause**: Endpoint requires API key, but JWT was provided

**Solution**:
- Use API key instead of JWT token
- This endpoint is for agents only

---

## Migration Guide

### For Existing Agents

1. **Create API keys** for each deployed agent
2. **Update Kubernetes secrets** with the new keys
3. **Update agent code** to use `X-API-Key` header
4. **Test authentication** before deploying
5. **Monitor logs** for authentication errors

### Example Update

Before:
```python
# Agent used to call APIs without auth (insecure)
response = requests.post("http://backend/api/tasks", json=data)
```

After:
```python
# Agent now uses API key
response = requests.post(
    "http://backend/api/tasks",
    headers={"X-API-Key": os.getenv("VE_API_KEY")},
    json=data
)
```

---

## Summary

✅ **Dual Authentication**: Users (JWT) + Agents (API keys)  
✅ **Secure**: Hashed storage, revocation, usage tracking  
✅ **Flexible**: Metadata, key types, customer isolation  
✅ **Easy Integration**: Simple HTTP header, Kubernetes-ready  
✅ **Production-Ready**: RLS policies, monitoring, best practices  

Agents can now authenticate and call all backend APIs! 🚀
