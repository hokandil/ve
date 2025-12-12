"""
Pydantic models for structured LLM outputs using Instructor
Ensures type-safe, validated responses from LLM agents
"""
from pydantic import BaseModel, Field, field_validator
from typing import Literal, List, Optional


class DelegationDecision(BaseModel):
    """
    Structured delegation decision from an agent.
    Used with Instructor to ensure LLM returns valid, typed data.
    """
    action: Literal["handle", "delegate", "parallel"] = Field(
        description="The delegation action: handle (do it myself), delegate (assign to one person), or parallel (split among team)"
    )
    
    delegated_to: Optional[str | List[str]] = Field(
        default=None,
        description="Agent type(s) to delegate to. Single string for 'delegate', list for 'parallel', None for 'handle'"
    )
    
    subtasks: Optional[List[dict]] = Field(
        default=None,
        description="Subtask definitions for parallel execution. Each dict should have 'agent' and 'task' keys"
    )
    
    reason: str = Field(
        description="Brief explanation of why this delegation decision was made",
        min_length=10,
        max_length=500
    )
    
    confidence: float = Field(
        description="Confidence score for this decision, between 0.0 (no confidence) and 1.0 (very confident)",
        ge=0.0,
        le=1.0
    )
    
    @field_validator('delegated_to')
    @classmethod
    def validate_delegated_to(cls, v, info):
        """Ensure delegated_to matches the action"""
        action = info.data.get('action')
        
        if action == 'handle' and v is not None:
            raise ValueError("delegated_to must be None when action is 'handle'")
        
        if action == 'delegate':
            if v is None:
                raise ValueError("delegated_to must be specified when action is 'delegate'")
            if isinstance(v, list):
                raise ValueError("delegated_to must be a string (not list) when action is 'delegate'")
        
        if action == 'parallel':
            if v is None:
                raise ValueError("delegated_to must be specified when action is 'parallel'")
            if not isinstance(v, list):
                raise ValueError("delegated_to must be a list when action is 'parallel'")
            if len(v) < 2:
                raise ValueError("delegated_to must have at least 2 agents for parallel execution")
        
        return v
    
    @field_validator('subtasks')
    @classmethod
    def validate_subtasks(cls, v, info):
        """Ensure subtasks are provided for parallel execution"""
        action = info.data.get('action')
        
        if action == 'parallel' and not v:
            raise ValueError("subtasks must be provided for parallel execution")
        
        if v:
            for subtask in v:
                if 'agent' not in subtask or 'task' not in subtask:
                    raise ValueError("Each subtask must have 'agent' and 'task' keys")
        
        return v


class AgentAnalysis(BaseModel):
    """
    Structured analysis result for task routing.
    Used for NLP-based agent selection.
    """
    recommended_agent_type: str = Field(
        description="The recommended agent type for this task (e.g., 'marketing-manager', 'copywriter')"
    )
    
    reasoning: str = Field(
        description="Explanation of why this agent type was selected",
        min_length=20,
        max_length=500
    )
    
    confidence: float = Field(
        description="Confidence in this recommendation (0.0 to 1.0)",
        ge=0.0,
        le=1.0
    )
    
    alternative_agents: Optional[List[str]] = Field(
        default=None,
        description="Alternative agent types that could also handle this task"
    )
    
    task_complexity: Literal["simple", "moderate", "complex"] = Field(
        description="Assessed complexity of the task"
    )


class TaskDecomposition(BaseModel):
    """
    Structured task decomposition for parallel execution.
    Used when a senior/manager breaks down a complex task.
    """
    subtasks: List[dict] = Field(
        description="List of subtasks, each with 'id', 'agent_type', 'description', and 'priority'",
        min_length=2,
        max_length=5
    )
    
    coordination_strategy: str = Field(
        description="How the subtask results should be combined",
        min_length=20,
        max_length=300
    )
    
    estimated_parallel_time: Optional[int] = Field(
        default=None,
        description="Estimated time in minutes for parallel execution",
        ge=1,
        le=480  # Max 8 hours
    )
    
    @field_validator('subtasks')
    @classmethod
    def validate_subtasks_structure(cls, v):
        """Ensure each subtask has required fields"""
        required_keys = {'id', 'agent_type', 'description', 'priority'}
        
        for i, subtask in enumerate(v):
            missing_keys = required_keys - set(subtask.keys())
            if missing_keys:
                raise ValueError(f"Subtask {i} missing required keys: {missing_keys}")
        
        return v
