"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class SeniorityLevel(str, Enum):
    JUNIOR = "junior"
    SENIOR = "senior"
    MANAGER = "manager"

class VEStatus(str, Enum):
    BETA = "beta"
    ALPHA = "alpha"
    STABLE = "stable"

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ConnectionType(str, Enum):
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

class MessageType(str, Enum):
    EMAIL = "email"
    CHAT = "chat"
    SYSTEM = "system"

# Auth Schemas
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    company_name: str
    industry: Optional[str] = None
    company_size: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Customer Schemas
class CustomerBase(BaseModel):
    company_name: str
    email: EmailStr
    industry: Optional[str] = None
    company_size: Optional[str] = None

class CustomerResponse(CustomerBase):
    id: str
    created_at: datetime
    subscription_status: str
    subscription_tier: str

# VE Marketplace Schemas
class VirtualEmployeeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=50)
    seniority_level: SeniorityLevel
    description: Optional[str] = Field(None, max_length=1000)
    capabilities: Optional[Dict[str, Any]] = None
    tools: Optional[Dict[str, Any]] = None
    pricing_monthly: float = Field(..., ge=0)
    framework: str = "crewai"
    status: VEStatus = VEStatus.BETA
    # New fields
    source: str = "custom"
    source_id: Optional[str] = None
    kagent_namespace: Optional[str] = None
    kagent_version: Optional[str] = None
    token_billing: str = "customer_pays"
    estimated_usage: str = "medium"
    tags: List[str] = []
    category: Optional[str] = None
    featured: bool = False
    icon_url: Optional[str] = None
    screenshots: List[str] = []
    marketing_description: Optional[str] = None

class VirtualEmployeeCreate(VirtualEmployeeBase):
    pass

class VirtualEmployeeUpdate(BaseModel):
    pricing_monthly: Optional[float] = Field(None, ge=0)
    token_billing: Optional[str] = None
    estimated_usage: Optional[str] = None
    tags: Optional[List[str]] = None
    category: Optional[str] = None
    featured: Optional[bool] = None
    icon_url: Optional[str] = None
    screenshots: Optional[List[str]] = None
    marketing_description: Optional[str] = None
    seniority_level: Optional[SeniorityLevel] = None

class VirtualEmployeeResponse(VirtualEmployeeBase):
    id: str
    created_at: datetime
    updated_at: datetime

class VirtualEmployeeListResponse(BaseModel):
    items: List[VirtualEmployeeResponse]
    total: int
    page: int
    page_size: int

# Customer VE Schemas
class HireVERequest(BaseModel):
    marketplace_agent_id: str
    persona_name: Optional[str] = Field(None, min_length=2, max_length=100)
    persona_email: Optional[EmailStr] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class CustomerVEResponse(BaseModel):
    id: str
    customer_id: str
    marketplace_agent_id: str
    persona_name: str
    persona_email: Optional[str] = None
    hired_at: datetime
    status: str
    agent_namespace: Optional[str] = None
    agent_name: Optional[str] = None
    agent_type: Optional[str] = None
    agent_gateway_route: Optional[str] = None
    agent_gateway_route_id: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    ve_details: Optional[VirtualEmployeeResponse] = None

# Org Chart Schemas
class UpdatePositionsRequest(BaseModel):
    positions: List[Dict[str, Any]]  # [{ve_id, position_x, position_y}]

class CreateConnectionRequest(BaseModel):
    from_ve_id: str
    to_ve_id: str
    connection_type: ConnectionType

class VEConnectionResponse(BaseModel):
    id: str
    customer_id: str
    from_ve_id: str
    to_ve_id: str
    connection_type: ConnectionType
    created_at: datetime

class OrgChartResponse(BaseModel):
    ves: List[CustomerVEResponse]
    connections: List[VEConnectionResponse]

# Task Schemas
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to_ve: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to_ve: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None

class TaskResponse(TaskBase):
    id: str
    customer_id: str
    created_by_user: bool
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    assigned_ve_details: Optional[CustomerVEResponse] = None

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

# Message Schemas
# Message Schemas
class MessageCreate(BaseModel):
    task_id: Optional[str] = None
    to_ve_id: Optional[str] = None
    subject: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.EMAIL
    thread_id: Optional[str] = None
    replied_to_id: Optional[str] = None

class MessageResponse(BaseModel):
    id: str
    task_id: Optional[str] = None
    customer_id: str
    from_type: str
    from_user_id: Optional[str] = None
    from_ve_id: Optional[str] = None
    to_type: str
    to_user_id: Optional[str] = None
    to_ve_id: Optional[str] = None
    subject: str
    content: str
    message_type: MessageType
    read: bool
    created_at: datetime
    thread_id: Optional[str] = None
    replied_to_id: Optional[str] = None

# Orchestrator Schemas
class OrchestratorRequest(BaseModel):
    task_description: str
    context: Optional[Dict[str, Any]] = None

class OrchestratorResponse(BaseModel):
    task_id: str
    routed_to_ve: str
    status: str
    message: str

# Billing Schemas
class TokenUsageResponse(BaseModel):
    id: str
    customer_id: str
    ve_id: Optional[str] = None
    operation: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    model: str
    timestamp: datetime

class BillingUsageResponse(BaseModel):
    total_tokens: int
    total_cost: float
    period_start: datetime
    period_end: datetime
    usage_by_ve: List[Dict[str, Any]]
    usage_by_operation: List[Dict[str, Any]]

class SubscriptionResponse(BaseModel):
    customer_id: str
    subscription_tier: str
    subscription_status: str
    monthly_ve_cost: float
    estimated_token_cost: float
    total_estimated_cost: float
    hired_ves_count: int

# Webhook Schemas
class WebhookEventType(str, Enum):
    TASK_UPDATE = "task_update"
    MESSAGE_SEND = "message_send"
    AGENT_STATUS = "agent_status"
    DELEGATION = "delegation"
    ERROR = "error"
    TOKEN_USAGE = "token_usage"

class WebhookEvent(BaseModel):
    event_type: WebhookEventType
    customer_id: str
    timestamp: Optional[datetime] = None
    data: Dict[str, Any]

class AgentStatusUpdate(BaseModel):
    customer_ve_id: str
    status: str
    message: Optional[str] = None

class DelegationEvent(BaseModel):
    from_agent_id: str
    to_agent_id: str
    task_id: str
    reason: str

class TokenUsageEvent(BaseModel):
    customer_id: str
    ve_id: Optional[str] = None
    operation: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost: float
    model: str

# Knowledge Base Schemas
class KnowledgeBaseItemCreate(BaseModel):
    content: str
    content_type: str = "text"
    metadata: Optional[Dict[str, Any]] = None

class KnowledgeBaseItemResponse(BaseModel):
    id: str
    customer_id: str
    content: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

class KnowledgeSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 5
    similarity_threshold: Optional[float] = 0.7

class KnowledgeSearchResponse(BaseModel):
    id: str
    customer_id: str
    content: str
    content_type: str
    metadata: Optional[Dict[str, Any]] = None
    similarity: float
    created_at: datetime
    updated_at: datetime

# LLM Output Schemas (for Instructor)
class DelegationDecision(BaseModel):
    """Structured output from LLM for delegation decisions"""
    action: str = Field(..., description="Action to take: 'handle', 'delegate', or 'parallel'")
    reasoning: str = Field(..., description="Explanation of why this decision was made")
    target_agent: Optional[str] = Field(None, description="Single agent to delegate to (for 'delegate' action)")
    target_agents: Optional[List[str]] = Field(None, description="Multiple agents for parallel execution")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    estimated_complexity: str = Field(..., description="Task complexity: 'low', 'medium', 'high'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action": "delegate",
                "reasoning": "This task requires marketing expertise which the Marketing Manager specializes in",
                "target_agent": "marketing-manager",
                "target_agents": None,
                "confidence": 0.9,
                "estimated_complexity": "medium"
            }
        }

class AgentAnalysis(BaseModel):
    """Analysis of an agent's capabilities and suitability"""
    agent_type: str
    expertise_match: float = Field(..., ge=0.0, le=1.0)
    workload_capacity: float = Field(..., ge=0.0, le=1.0)
    reasoning: str

class TaskDecomposition(BaseModel):
    """Breakdown of a task into subtasks"""
    subtasks: List[Dict[str, Any]]
    parallel_execution: bool
    estimated_duration: str
