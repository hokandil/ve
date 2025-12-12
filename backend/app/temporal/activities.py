"""
Temporal Activities
"""
from temporalio import activity
from typing import Dict, Any, List, Optional
from app.services.agent_gateway_service import get_agent_gateway_service
from app.core.centrifugo import get_centrifugo_client
from app.core.database import get_supabase_admin
from datetime import datetime

@activity.defn
async def invoke_agent_activity(
    customer_id: str,
    agent_type: str,
    message: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Activity to invoke an agent via the Agent Gateway.
    """
    service = get_agent_gateway_service()
    
    # Invoke agent
    result = await service.invoke_agent(
        customer_id=customer_id,
        agent_type=agent_type,
        message=message,
        session_id=session_id
    )
    
    return result

@activity.defn
async def publish_update_activity(
    channel: str,
    data: Dict[str, Any]
) -> None:
    """
    Activity to publish real-time updates to Centrifugo.
    """
    client = get_centrifugo_client()
    await client.publish(channel, data)

@activity.defn
async def update_task_status_activity(
    task_id: str,
    status: str,
    assigned_to_agent_type: Optional[str] = None,
    progress_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    Activity to update task status in database and send real-time update to UI.
    This connects the workflow execution to the Kanban board.
    
    Args:
        task_id: The task ID
        status: New status (pending, in_progress, completed, failed)
        assigned_to_agent_type: Agent type (e.g., "devops-manager") - will be converted to customer_ves ID
        progress_message: Optional progress message to display
    """
    supabase = get_supabase_admin()
    centrifugo = get_centrifugo_client()
    
    try:
        task_response = supabase.table("tasks").select("customer_id, metadata").eq("id", task_id).execute()
        if not task_response.data:
            raise Exception(f"Task {task_id} not found")
        
        customer_id = task_response.data[0]["customer_id"]
        current_metadata = task_response.data[0].get("metadata") or {}
        
        # Update task in database
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Add progress message to metadata if provided
        if progress_message:
            current_metadata["last_progress_message"] = progress_message
            current_metadata["last_progress_timestamp"] = datetime.utcnow().isoformat()
            update_data["metadata"] = current_metadata
        
        # If agent_type provided, lookup the customer_ves ID
        assigned_to_ve_id = None
        if assigned_to_agent_type:
            ve_response = supabase.table("customer_ves").select("id").eq(
                "customer_id", customer_id
            ).eq(
                "agent_type", assigned_to_agent_type
            ).limit(1).execute()
            
            if ve_response.data:
                assigned_to_ve_id = ve_response.data[0]["id"]
                update_data["assigned_to_ve"] = assigned_to_ve_id
        
        if status == "completed":
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        response = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
        
        if not response.data:
            raise Exception(f"Failed to update task {task_id}")
        
        task_data = response.data[0]
        
        # Send real-time update to frontend via Centrifugo
        if centrifugo:
            try:
                centrifugo.publish(
                    channel=f"customer:{customer_id}:tasks",
                    data={
                        "type": "task_update",
                        "task_id": task_id,
                        "status": status,
                        "assigned_to_agent_type": assigned_to_agent_type,
                        "assigned_to_ve_id": assigned_to_ve_id,
                        "progress_message": progress_message,
                        "updated_at": update_data["updated_at"]
                    }
                )
            except Exception as e:
                activity.logger.warning(f"Failed to publish to Centrifugo: {e}")
                # Don't fail the activity if Centrifugo fails
        
        activity.logger.info(f"✅ Task {task_id} updated: status={status}, assigned_to={assigned_to_agent_type}")
        
        return {
            "success": True,
            "task_id": task_id,
            "status": status,
            "assigned_to_agent_type": assigned_to_agent_type,
            "assigned_to_ve_id": assigned_to_ve_id
        }
        
    except Exception as e:
        activity.logger.error(f"Error updating task status: {e}")
        raise

@activity.defn
async def save_task_result_activity(
    task_id: str,
    result: Dict[str, Any],
    status: str = "completed"
) -> Dict[str, Any]:
    """
    Activity to save task result and add system comment.
    """
    supabase = get_supabase_admin()
    
    try:
        # Get task to find customer_id
        task_response = supabase.table("tasks").select("customer_id").eq("id", task_id).execute()
        if not task_response.data:
            raise Exception(f"Task {task_id} not found")
        
        customer_id = task_response.data[0]["customer_id"]
        
        # Update task status to completed
        await update_task_status_activity(task_id, status)
        
        # Add result as comment
        if "message" in result:
            comment_data = {
                "task_id": task_id,
                "customer_id": customer_id,  # ✅ Added customer_id
                "author_type": "system",
                "content": f"Task {status}. Result: {result['message'][:500]}",
                "created_at": datetime.utcnow().isoformat()
            }
            supabase.table("task_comments").insert(comment_data).execute()
        
        activity.logger.info(f"✅ Task {task_id} result saved")
        
        return {"success": True, "task_id": task_id}
    except Exception as e:
        activity.logger.error(f"Error saving task result: {e}")
        raise

@activity.defn
async def get_campaign_performance_activity(
    campaign_id: str
) -> Dict[str, Any]:
    """
    Mock activity to get campaign performance data.
    """
    return {
        "engagement_rate": 0.05,
        "impressions": 1200,
        "clicks": 45
    }

@activity.defn
async def analyze_routing_activity(
    customer_id: str,
    task_description: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Activity to analyze task and determine routing.
    Calls the System Orchestrator Agent via Agent Gateway.
    """
    service = get_agent_gateway_service()
    
    try:
        # Invoke System Orchestrator
        response = await service.invoke_agent(
            customer_id=customer_id,
            agent_type="system-orchestrator",
            message=f"""
Please analyze this task and determine the best routing.
Task: {task_description}
Context: {context}

Return JSON with 'routing_info' containing 'primary_agent'.
""",
            session_id=f"routing-{datetime.utcnow().timestamp()}"
        )
        
        # Parse response to find JSON block
        import re
        content = response.get("message", "")
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            # Try parsing raw if no code block
            try:
                data = json.loads(content)
            except:
                # Fallback extraction (simple brace matching)
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(content[start:end+1])
                else:
                    raise Exception("Could not parse Orchestrator response")

        routing_info = data.get("routing_info", {})
        decision = data.get("decision", {})
        
        target_agent = routing_info.get("primary_agent") or decision.get("target_agent")
        
        return {
            "routed_to_ve": None, # Will be resolved by workflow using target_agent
            "target_agent": target_agent,
            "reason": data.get("thought_process", response.get("message"))
        }

    except Exception as e:
        activity.logger.error(f"Routing failed: {e}")
        # Fallback to local heuristic if Orchestrator is offline
        fallback_agent = await analyze_task_description_activity(task_description, context)
        return {
            "target_agent": fallback_agent,
            "reason": f"Fallback routing used due to error: {e}"
        }

@activity.defn
async def get_customer_ves_activity(
    customer_id: str
) -> List[Dict[str, Any]]:
    """
    Activity to fetch customer's VEs for routing logic.
    """
    supabase = get_supabase_admin()
    response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("customer_id", customer_id).execute()
    return response.data

@activity.defn
async def analyze_task_description_activity(
    task_description: str,
    context: Dict[str, Any]
) -> str:
    """
    Fallback activity to analyze task description using local keyword matching.
    Used when System Orchestrator is unavailable.
    """
    description_lower = task_description.lower()
    
    # Simple keyword matching fallback
    if any(k in description_lower for k in ["code", "deploy", "server", "bug", "fix"]):
        return "devops-manager"
    if any(k in description_lower for k in ["post", "write", "blog", "social"]):
        return "marketing-manager"
    
    return "devops-manager" # Default

@activity.defn
async def analyze_and_decide_delegation_activity(
    agent_type: str,
    task_description: str,
    context: Dict[str, Any],
    available_agents: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Activity where an agent decides delegation strategy.
    Invokes the specific Agent via Gateway to make the decision.
    """
    service = get_agent_gateway_service()
    customer_id = context.get("customer_id")
    
    try:
        response = await service.invoke_agent(
            customer_id=customer_id,
            agent_type=agent_type,
            message=f"""
You are managing a task. Decide if you can handle it or need to delegate.
Task: {task_description}

Available Agents: {[a['name'] for a in available_agents]}

Return JSON:
{{
  "decision": {{
    "action": "handle" | "delegate",
    "delegated_to": "agent_name" (if delegating)
  }}
}}
""",
            session_id=f"delegation-{datetime.utcnow().timestamp()}"
        )
        
        # Parse JSON similar to routing
        import re
        content = response.get("message", "")
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
            decision = data.get("decision", {})
            return {
                "action": decision.get("action", "handle"),
                "delegated_to": decision.get("delegated_to"),
                "reason": data.get("thought_process", "Agent decision")
            }
            
        return {"action": "handle", "reason": "Could not parse decision, defaulting to handle"}

    except Exception as e:
        activity.logger.error(f"Delegation decision failed: {e}")
        return {"action": "handle", "reason": f"Fallback due to error: {e}"}
    
    # Check if DSPy should be used (feature flag + rollout percentage)
    use_dspy = should_use_dspy_delegation()
    
    if use_dspy:
        # Use DSPy-optimized delegation
        from app.temporal.activities_dspy import analyze_and_decide_delegation_activity_dspy
        return await analyze_and_decide_delegation_activity_dspy(
            agent_type, task_description, context, available_agents
        )
    
    # Otherwise use Instructor (default)
    import instructor
    from openai import AsyncOpenAI
    from app.schemas import DelegationDecision
    
    # Patch schema to support 'ask_clarification' at runtime if not updated
    # Ideally should be in app/schemas/__init__.py but for activity-level logical isolation:
    from pydantic import BaseModel, Field
    from typing import Literal
    
    class DelegationDecision(BaseModel):
        action: Literal["handle", "delegate", "parallel", "ask_clarification"] = Field(
            description="The action to take: handle directly, delegate to another, split in parallel, or ask user for clarification"
        )
        delegated_to: Optional[str] = Field(None, description="The agent type to delegate to (if action is delegate)")
        reason: str = Field(description="The reasoning behind the decision or the questions to ask the user")
        confidence: float = Field(description="Confidence score between 0.0 and 1.0")
        subtasks: Optional[List[Dict[str, Any]]] = Field(None, description="List of subtasks if action is parallel")

    import os
    
    # Build list of available agents for delegation
    agent_list = "\n".join([
        f"- {agent['agent_type']} ({agent['ve_details']['seniority_level']}): {agent['persona_name']}"
        for agent in available_agents
    ])
    
    # Create delegation analysis prompt
    system_prompt = f"""You are a {agent_type} with expertise in task delegation and team coordination.

Your role is to analyze tasks and make intelligent delegation decisions based on:
1. Task complexity and requirements
2. Team member expertise and availability
3. Efficiency and quality considerations

You can choose to:
- HANDLE: Execute the task yourself if it's within your expertise
- DELEGATE: Assign to ONE specialist if they're better suited
- PARALLEL: Split among MULTIPLE team members for faster completion
- ASK_CLARIFICATION: Ask the user if requirements are ambiguous or key information (budget, timeline) is missing"""

    user_prompt = f"""TASK: {task_description}

CONTEXT:
- Priority: {context.get('priority', 'medium')}
- Due Date: {context.get('due_date', 'Not specified')}
- User Feedback History: {context.get('user_feedback', 'None')}

AVAILABLE TEAM MEMBERS:
{agent_list}

Analyze this task and decide the best delegation strategy. Consider:
1. Is the task clear? If NO, ask for clarification.
2. Can YOU handle this alone effectively?
3. Would ONE specialist be better suited?
4. Should this be SPLIT among multiple people for parallel work?

Provide your decision with clear reasoning."""
    
    try:
        from app.core.config import settings
        
        # Initialize Instructor client with OpenAI
        client = instructor.from_openai(
            AsyncOpenAI(api_key=settings.OPENAI_API_KEY),
            mode=instructor.Mode.TOOLS  # Use function calling for better structured outputs
        )
        
        # Get structured decision with automatic validation and retries
        decision = await client.chat.completions.create(
            model="gpt-4",  # Use GPT-4 for better reasoning
            response_model=DelegationDecision,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_retries=3,  # Automatic retry on validation failure
            temperature=0.7  # Balanced creativity and consistency
        )
        
        # Log the decision for monitoring and training
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Instructor delegation decision by {agent_type}: {decision.action} "
            f"(confidence: {decision.confidence:.2f}) - {decision.reason}"
        )
        
        # Log for training if enabled
        from app.core.feature_flags import is_feature_enabled
        if is_feature_enabled('log_delegation_decisions'):
            logger.info(f"TRAINING_DATA: {decision.model_dump()}")
        
        # Return as dict (already validated by Pydantic!)
        result = decision.model_dump()
        result['method'] = 'instructor'
        return result
        
    except Exception as e:
        # Fallback on error: agent handles it themselves
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in delegation analysis: {e}")
        
        return {
            "action": "handle",
            "delegated_to": None,
            "subtasks": None,
            "reason": f"Error in delegation analysis, defaulting to self-execution: {str(e)}",
            "confidence": 0.3,
            "method": "fallback"
        }


@activity.defn
async def create_task_plan_activity(
    task_id: str,
    task_description: str,
    agent_type: str,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Activity to generate a structured execution plan using the assigned Agent via Gateway.
    """
    supabase = get_supabase_admin()
    service = get_agent_gateway_service()
    customer_id = context.get("customer_id")
    
    try:
        response = await service.invoke_agent(
            customer_id=customer_id,
            agent_type=agent_type,
            message=f"""
Please create a detailed execution plan for this task.
Task: {task_description}
Context: {context}

Return JSON with a 'plan' object containing:
- steps: list of {{"output_type", "description"}}
- timeline: string
- resources_needed: list of strings
- initial_thought: string
""",
            session_id=f"plan-{task_id}"
        )
        
        # Parse JSON
        import re
        content = response.get("message", "")
        # Extract JSON from markdown code blocks
        json_match = re.search(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(1))
        else:
            # Try raw parse or fuzzy extraction
            try:
                data = json.loads(content)
            except:
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1:
                    data = json.loads(content[start:end+1])
                else:
                    # Fallback default plan if parsing fails
                    data = {
                        "plan": {
                            "initial_thought": content[:200],
                            "steps": [{"output_type": "text", "description": "Execute task based on user request"}],
                            "timeline": "unknown",
                            "resources_needed": []
                        }
                    }

        plan = data.get("plan", data) # Handle if plan is root or nested
        
        # Persist to Supabase
        plan_data = {
            "task_id": task_id,
            "steps": plan.get("steps", []),
            "timeline": plan.get("timeline", "1 hour"),
            "resources": plan.get("resources_needed", []),
            "status": "draft",
            "created_at": datetime.utcnow().isoformat()
        }
        
        plan_res = supabase.table("task_plans").insert(plan_data).execute()
        
        # Update Task Phase
        supabase.table("tasks").update({
            "current_phase": "planning",
            "metadata": {
                **context, 
                "latest_plan_id": plan_res.data[0]['id'] if plan_res.data else None,
                "last_progress_message": f"Drafted execution plan: {plan.get('initial_thought', 'Plan created')}"
            }
        }).eq("id", task_id).execute()
        
        return {
            "success": True,
            "plan_id": plan_res.data[0]['id'] if plan_res.data else None,
            "summary": plan.get("initial_thought", "Plan ready for review")
        }
        
    except Exception as e:
        activity.logger.error(f"Error creating task plan: {e}")
        return {"success": False, "error": str(e)}
