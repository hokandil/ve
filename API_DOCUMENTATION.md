# VE SaaS Platform - API Documentation

## Overview
The VE SaaS Platform provides a comprehensive API for managing Virtual Employees (AI agents), tasks, billing, and real-time chat interactions.

**Base URL:** `http://localhost:8000/api`  
**Authentication:** Bearer JWT tokens or API Keys  
**Content-Type:** `application/json`

---

## Authentication

### User Authentication (JWT)
```http
POST /api/auth/signup
POST /api/auth/login
```

**Login Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com"
  }
}
```

### API Key Authentication
For agent-to-agent or service-to-service communication:
```http
GET /api/endpoint
X-API-Key: your_api_key_here
```

### Service Token (Internal)
For internal microservices (Delegation Server, MCP Servers):
```http
POST /api/messages/delegate
Authorization: Bearer service_token_here
```

---

## Marketplace API

### List Available VEs
```http
GET /api/marketplace/ves?department=engineering&seniority_level=senior&page=1&page_size=20
```

**Query Parameters:**
- `department` (optional): Filter by department
- `seniority_level` (optional): `junior`, `senior`, `manager`
- `status` (optional): `stable`, `beta`, `experimental`
- `source` (optional): Filter by source (`kagent`, `registry`)
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

**Response:**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Senior DevOps Engineer",
      "role": "DevOps Engineer",
      "department": "Engineering",
      "seniority_level": "senior",
      "pricing_monthly": 2999.99,
      "description": "Expert in Kubernetes, CI/CD, and cloud infrastructure",
      "icon_url": "https://...",
      "tags": ["kubernetes", "docker", "terraform"],
      "source": "kagent"
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

### Get VE Details
```http
GET /api/marketplace/ves/{ve_id}
```

**Response:**
```json
{
  "id": "uuid",
  "name": "Senior DevOps Engineer",
  "role": "DevOps Engineer",
  "department": "Engineering",
  "seniority_level": "senior",
  "pricing_monthly": 2999.99,
  "description": "Detailed description...",
  "capabilities": ["Deploy applications", "Monitor infrastructure"],
  "tools": ["kubectl", "terraform", "ansible"],
  "icon_url": "https://...",
  "screenshots": ["https://..."],
  "tags": ["kubernetes", "docker"],
  "source": "kagent",
  "created_at": "2025-01-01T00:00:00Z"
}
```

---

## Customer VE Management

### Hire a VE
```http
POST /api/customer/ves
Authorization: Bearer {jwt_token}
```

**Request:**
```json
{
  "marketplace_agent_id": "uuid",
  "persona_name": "DevOps Bot",
  "persona_email": "devops@mycompany.com"
}
```

**Response:**
```json
{
  "id": "uuid",
  "customer_id": "uuid",
  "marketplace_agent_id": "uuid",
  "persona_name": "DevOps Bot",
  "persona_email": "devops@mycompany.com",
  "status": "active",
  "hired_at": "2025-01-01T00:00:00Z",
  "agent_gateway_route": "/agents/devops-bot-uuid"
}
```

### List My VEs
```http
GET /api/customer/ves
Authorization: Bearer {jwt_token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "persona_name": "DevOps Bot",
    "persona_email": "devops@mycompany.com",
    "status": "active",
    "hired_at": "2025-01-01T00:00:00Z",
    "ve_details": {
      "name": "Senior DevOps Engineer",
      "role": "DevOps Engineer",
      "department": "Engineering",
      "seniority_level": "senior",
      "pricing_monthly": 2999.99
    }
  }
]
```

### Unhire a VE
```http
DELETE /api/customer/ves/{ve_id}
Authorization: Bearer {jwt_token}
```

**Response:** `204 No Content`

### Update VE Details
```http
PATCH /api/customer/ves/{ve_id}
Authorization: Bearer {jwt_token}
```

**Request:**
```json
{
  "persona_name": "New Name"
}
```

---

## Chat & Messaging

### Send Message (Streaming)
```http
POST /api/messages/ves/{ve_id}/chat
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

**Request:**
```json
{
  "content": "Deploy the new microservice to production",
  "subject": "Deployment Request"
}
```

**Response:** Server-Sent Events (SSE)
```
data: {"type": "thought", "content": "Analyzing deployment requirements..."}

data: {"type": "action", "tool": "kubectl", "input": "apply -f deployment.yaml"}

data: {"type": "result", "content": "Deployment successful"}

data: {"type": "message", "content": "I've deployed the microservice to production. "}

data: {"type": "message", "content": "All pods are running healthy."}

data: [DONE]
```

### Get Chat History
```http
GET /api/messages/ves/{ve_id}/history
Authorization: Bearer {jwt_token}
```

**Response:**
```json
[
  {
    "id": "uuid",
    "from_type": "customer",
    "content": "Deploy the new microservice",
    "created_at": "2025-01-01T10:00:00Z"
  },
  {
    "id": "uuid",
    "from_type": "ve",
    "content": "Deployment successful",
    "created_at": "2025-01-01T10:01:00Z"
  }
]
```

### Delegate Task (Internal)
```http
POST /api/messages/delegate
Authorization: Bearer {service_token}
```

**Request:**
```json
{
  "customer_id": "uuid",
  "target_agent_id": "uuid",
  "task": "Review the deployment logs"
}
```

**Response:**
```json
{
  "status": "success",
  "message_id": "uuid"
}
```

---

## Task Management

### Create Task
```http
POST /api/tasks
Authorization: Bearer {jwt_token}
```

**Request:**
```json
{
  "title": "Deploy new feature",
  "description": "Deploy feature X to production",
  "priority": "high",
  "assigned_to_ve": "uuid"
}
```

**Response:**
```json
{
  "id": "uuid",
  "title": "Deploy new feature",
  "description": "Deploy feature X to production",
  "status": "pending",
  "priority": "high",
  "assigned_to_ve": "uuid",
  "created_at": "2025-01-01T00:00:00Z"
}
```

### List Tasks
```http
GET /api/tasks?status=pending&assigned_to_ve={ve_id}
Authorization: Bearer {jwt_token}
```

### Update Task Status
```http
PATCH /api/tasks/{task_id}
Authorization: Bearer {jwt_token}
```

**Request:**
```json
{
  "status": "completed"
}
```

---

## Billing

### Get Usage Summary
```http
GET /api/billing/usage?start_date=2025-01-01&end_date=2025-01-31
Authorization: Bearer {jwt_token}
```

**Response:**
```json
{
  "period": {
    "start": "2025-01-01",
    "end": "2025-01-31"
  },
  "total_cost": 5999.98,
  "ve_subscriptions": 2999.99,
  "token_usage_cost": 3000.00,
  "breakdown": [
    {
      "ve_id": "uuid",
      "ve_name": "DevOps Bot",
      "monthly_fee": 2999.99,
      "tokens_used": 1500000,
      "token_cost": 1500.00
    }
  ]
}
```

---

## Discovery (KAgent Integration)

### List KAgent Agents
```http
GET /api/discovery/agents
```

**Response:**
```json
{
  "agents": [
    {
      "name": "devops-engineer",
      "namespace": "kagent",
      "type": "Declarative",
      "status": "Ready"
    }
  ]
}
```

### Import Agent from Registry
```http
POST /api/discovery/import
Authorization: Bearer {admin_token}
```

**Request:**
```json
{
  "artifact_id": "registry_artifact_id",
  "name": "Custom Agent",
  "department": "Engineering"
}
```

---

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no body
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

**Error Format:**
```json
{
  "detail": "Error message here"
}
```

**Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Rate Limiting

API requests are rate-limited per customer:
- **Standard tier**: 100 requests/minute
- **Premium tier**: 1000 requests/minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

---

## Webhooks

### Agent Gateway Usage Webhook
```http
POST /api/webhooks/agent-gateway/usage
X-Webhook-Signature: sha256=...
```

**Payload:**
```json
{
  "customer_id": "uuid",
  "agent_id": "uuid",
  "tokens_used": 1500,
  "model": "gpt-4",
  "timestamp": "2025-01-01T10:00:00Z"
}
```

---

## SDK Examples

### Python
```python
import requests

# Login
response = requests.post("http://localhost:8000/api/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
token = response.json()["access_token"]

# List VEs
headers = {"Authorization": f"Bearer {token}"}
ves = requests.get("http://localhost:8000/api/customer/ves", headers=headers).json()

# Chat with VE
import sseclient

response = requests.post(
    f"http://localhost:8000/api/messages/ves/{ve_id}/chat",
    headers=headers,
    json={"content": "Hello!"},
    stream=True
)

client = sseclient.SSEClient(response)
for event in client.events():
    print(event.data)
```

### JavaScript
```javascript
// Login
const response = await fetch('http://localhost:8000/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email: 'user@example.com', password: 'password' })
});
const { access_token } = await response.json();

// Stream chat
const eventSource = new EventSource(
  `http://localhost:8000/api/messages/ves/${veId}/chat`,
  { headers: { 'Authorization': `Bearer ${access_token}` } }
);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(data);
};
```

---

## Security Best Practices

1. **Always use HTTPS in production**
2. **Store JWT tokens securely** (httpOnly cookies or secure storage)
3. **Rotate API keys regularly**
4. **Validate all user input**
5. **Use service tokens only for internal services**
6. **Enable RLS policies on all tables**
7. **Monitor for suspicious activity**

---

## Support

For API support:
- **Documentation**: `/docs` (Swagger UI)
- **Alternative docs**: `/redoc` (ReDoc)
- **GitHub**: https://github.com/hokandil/ve
