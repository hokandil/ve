"""
Orchestrator Service
Routes customer requests to appropriate VEs via Agent Gateway
"""
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.database import get_supabase_admin
from app.services.agent_gateway_service import get_agent_gateway_service
import uuid

logger = logging.getLogger(__name__)

MAX_ESCALATION_ATTEMPTS = 3
SENIORITY_LEVELS = ["manager", "senior", "junior"]

def build_escalation_chain(ves_list: list, failed_ve_id: str = None) -> list:
    """
    Build escalation chain based on seniority levels
    Returns list of VEs ordered by seniority (manager -> senior -> junior)
    Excludes the failed VE from the chain
    """
    # Group VEs by seniority
    ves_by_seniority = {level: [] for level in SENIORITY_LEVELS}
    
    for ve in ves_list:
        seniority = ve.get("ve_details", {}).get("seniority_level")
        if seniority in SENIORITY_LEVELS and ve["id"] != failed_ve_id:
            ves_by_seniority[seniority].append(ve)
    
    # Build chain: managers first, then seniors, then juniors
    escalation_chain = []
    for level in SENIORITY_LEVELS:
        escalation_chain.extend(ves_by_seniority[level])
    
    return escalation_chain

async def route_request_to_orchestrator(
    customer_id: str,
    task_description: str,
    context: Dict[str, Any],
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route a customer request through the shared orchestrator
    
    The orchestrator analyzes the request and routes it to the appropriate VE
    via Agent Gateway using A2A protocol
    """
    try:
        # Get customer's org structure
        supabase = get_supabase_admin()
        ves_response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("customer_id", customer_id).execute()
        
        if not ves_response.data:
            raise Exception("No VEs hired yet")
        
        # Create task in database if not provided
        if not task_id:
            task_id = str(uuid.uuid4())
            task_data = {
                "id": task_id,
                "customer_id": customer_id,
                "title": task_description[:255],
                "description": task_description,
                "created_by_user": True,
                "status": "pending"
            }
            supabase.table("tasks").insert(task_data).execute()
        else:
            # Verify task exists
            # We assume it exists if passed, but could verify
            pass
        
        # Get Agent Gateway service
        agent_gateway = get_agent_gateway_service()
        
        # ROUTING LOGIC: Orchestrator is ALWAYS the first hop.
        # The Orchestrator Agent will decide based on:
        # 1. Task Domain (Marketing, IT, etc.)
        # 2. Available Managers (Prefer Managers for their domain)
        # 3. Cross-functional needs
        
        try:
            orchestrator_response = await agent_gateway.invoke_orchestrator(
                customer_id=customer_id,
                task_description=task_description,
                context={
                    **context,
                    "task_id": task_id,
                    "routing_rules": [
                        "1. ALWAYS analyze the task domain (e.g., Marketing, IT, Sales).",
                        "2. IF a Manager exists for that domain, route to them.",
                        "3. IF the task requires multiple departments, identify the primary department's manager.",
                        "4. IF no manager exists for the domain, route to the most senior specialist.",
                        "5. IF multiple managers are needed, route to the one most relevant to the core objective."
                    ],
                    "available_ves": [
                        {
                            "id": ve["id"],
                            "name": ve["persona_name"],
                            "role": ve["ve_details"]["role"],
                            "department": ve["ve_details"]["department"],
                            "seniority": ve["ve_details"]["seniority_level"]
                        }
                        for ve in ves_response.data
                    ]
                }
            )
            
            # Extract routing decision from orchestrator
            target_ve_id = orchestrator_response.get("routed_to_ve")
            
            if not target_ve_id:
                # Fallback: route to first manager VE or any VE
                logger.warning("Orchestrator returned no VE ID. Using fallback.")
                manager_ves = [ve for ve in ves_response.data if ve["ve_details"]["seniority_level"] == "manager"]
                target_ve = manager_ves[0] if manager_ves else ves_response.data[0]
                target_ve_id = target_ve["id"]
            else:
                # Find the VE by ID
                target_ve = next((ve for ve in ves_response.data if ve["id"] == target_ve_id), None)
                if not target_ve:
                     logger.warning(f"Orchestrator routed to unknown VE ID {target_ve_id}. Using fallback.")
                     target_ve = ves_response.data[0]
                     target_ve_id = target_ve["id"]
                else:
                     logger.info(f"Orchestrator routed to: {target_ve['persona_name']} ({target_ve['ve_details']['role']})")
            
        except Exception as e:
            logger.warning(f"Orchestrator call failed, using fallback routing: {e}")
            # Fallback routing logic
            manager_ves = [ve for ve in ves_response.data if ve["ve_details"]["seniority_level"] == "manager"]
            target_ve = manager_ves[0] if manager_ves else ves_response.data[0]
            target_ve_id = target_ve["id"]
        
        # Update task assignment
        supabase.table("tasks").update({
            "assigned_to_ve": target_ve_id,
            "status": "in_progress"
        }).eq("id", task_id).execute()
        
        logger.info(f"Task {task_id} assigned to VE {target_ve['persona_name']} ({target_ve['ve_details']['role']})")
        
        # ESCALATION LOGIC: Try to invoke agent with automatic escalation on failure
        escalation_attempts = 0
        escalation_chain = [target_ve]
        current_ve = target_ve
        final_status = "routed"
        escalation_log = []
        
        from datetime import datetime
        
        for attempt in range(MAX_ESCALATION_ATTEMPTS):
            try:
                agent_type = current_ve.get("agent_type")
                if not agent_type:
                    raise Exception(f"VE {current_ve['persona_name']} has no agent_type configured")
                
                # Format task as a message
                prompt = f"New Task Assigned: {task_description}"
                if attempt > 0:
                    prompt = f"ESCALATED Task (Attempt {attempt + 1}): {task_description}\n\nPrevious agent failed to respond."
                
                logger.info(f"Attempt {attempt + 1}/{MAX_ESCALATION_ATTEMPTS}: Invoking {current_ve['persona_name']} ({current_ve['ve_details']['role']})")
                
                agent_response = await agent_gateway.invoke_agent(
                    customer_id=customer_id,
                    agent_type=agent_type,
                    message=prompt,
                    user_id=customer_id
                )
                
                # Check if we got a valid response
                if not agent_response or "message" not in agent_response or not agent_response["message"]:
                    raise Exception("Agent returned empty or invalid response")
                
                # Success! Add agent response as a comment
                supabase.table("task_comments").insert({
                    "task_id": task_id,
                    "customer_id": customer_id,
                    "content": agent_response["message"],
                    "author_type": "ve",
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                
                # Log successful assignment
                escalation_log.append({
                    "attempt": attempt + 1,
                    "ve_id": current_ve["id"],
                    "ve_name": current_ve["persona_name"],
                    "status": "success",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.info(f"Task {task_id} successfully handled by {current_ve['persona_name']} on attempt {attempt + 1}")
                break  # Success, exit loop
                
            except Exception as e:
                escalation_attempts += 1
                error_msg = str(e)
                
                # Log failed attempt
                escalation_log.append({
                    "attempt": attempt + 1,
                    "ve_id": current_ve["id"],
                    "ve_name": current_ve["persona_name"],
                    "status": "failed",
                    "reason": error_msg,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                logger.warning(f"Attempt {attempt + 1} failed for {current_ve['persona_name']}: {error_msg}")
                
                # Check if we have more attempts
                if attempt < MAX_ESCALATION_ATTEMPTS - 1:
                    # Build escalation chain excluding failed VEs
                    failed_ve_ids = [log["ve_id"] for log in escalation_log if log["status"] == "failed"]
                    available_ves = [ve for ve in ves_response.data if ve["id"] not in failed_ve_ids]
                    
                    if not available_ves:
                        logger.error("No more VEs available for escalation")
                        final_status = "failed_after_escalations"
                        break
                    
                    # Get next VE in escalation chain (by seniority)
                    next_escalation_chain = build_escalation_chain(available_ves)
                    
                    if not next_escalation_chain:
                        logger.error("No suitable VEs in escalation chain")
                        final_status = "failed_after_escalations"
                        break
                    
                    next_ve = next_escalation_chain[0]
                    escalation_chain.append(next_ve)
                    
                    # Update task assignment to escalated VE
                    supabase.table("tasks").update({
                        "assigned_to_ve": next_ve["id"],
                        "status": "escalated"
                    }).eq("id", task_id).execute()
                    
                    logger.info(f"Escalating to {next_ve['persona_name']} ({next_ve['ve_details']['seniority_level']} - {next_ve['ve_details']['role']})")
                    current_ve = next_ve
                else:
                    # All attempts exhausted
                    logger.error(f"All {MAX_ESCALATION_ATTEMPTS} escalation attempts exhausted for task {task_id}")
                    final_status = "failed_after_escalations"
                    
                    # Mark task as failed
                    supabase.table("tasks").update({
                        "status": "failed",
                        "metadata": {
                            "failure_reason": "All escalation attempts exhausted",
                            "escalation_log": escalation_log
                        }
                    }).eq("id", task_id).execute()
        
        return {
            "task_id": task_id,
            "routed_to_ve": current_ve["id"],
            "final_assigned_ve_id": current_ve["id"],
            "escalation_attempts": escalation_attempts,
            "escalation_chain": [ve["id"] for ve in escalation_chain],
            "escalation_log": escalation_log,
            "status": final_status,
            "message": f"Task assigned to {current_ve['persona_name']}" if final_status == "routed" else f"Task failed after {escalation_attempts} escalation attempts"
        }
        
    except Exception as e:
        logger.error(f"Orchestrator routing failed: {e}")
        raise

async def route_task_to_ve(
    customer_id: str,
    task_id: str,
    ve_id: str,
    task_description: str
) -> bool:
    """
    Route a specific task directly to a specific VE (manual routing)
    This is used when a task is manually assigned to a VE, bypassing the orchestrator
    """
    try:
        supabase = get_supabase_admin()
        
        # Get VE details with marketplace info
        ve_response = supabase.table("customer_ves").select("*, ve_details:virtual_employees(*)").eq("id", ve_id).eq("customer_id", customer_id).execute()
        
        if not ve_response.data:
            logger.error(f"VE {ve_id} not found for customer {customer_id}")
            return False
        
        ve = ve_response.data[0]
        
        # Get Agent Gateway service
        agent_gateway = get_agent_gateway_service()
        
        # Invoke the VE agent
        try:
            agent_type = ve.get("agent_type")
            if not agent_type:
                logger.error(f"VE {ve['persona_name']} has no agent_type configured")
                return False
            
            logger.info(f"Invoking agent {ve['persona_name']} ({agent_type}) for task {task_id}")
            
            agent_response = await agent_gateway.invoke_agent(
                customer_id=customer_id,
                agent_type=agent_type,
                message=f"New Task Assigned: {task_description}",
                user_id=customer_id
            )
            
            # Update task status and assignment
            supabase.table("tasks").update({
                "assigned_to_ve": ve_id,
                "status": "in_progress"
            }).eq("id", task_id).execute()
            
            # Add agent response as a comment if available
            if agent_response and "message" in agent_response:
                from datetime import datetime
                supabase.table("task_comments").insert({
                    "task_id": task_id,
                    "customer_id": customer_id,
                    "content": agent_response["message"],
                    "author_type": "ve",
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Successfully routed task {task_id} to VE {ve['persona_name']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to invoke agent for VE {ve['persona_name']}: {e}")
            # Update task status to indicate failure
            supabase.table("tasks").update({
                "status": "failed",
                "metadata": {
                    "failure_reason": f"Agent invocation failed: {str(e)}"
                }
            }).eq("id", task_id).execute()
            return False
            
    except Exception as e:
        logger.error(f"route_task_to_ve failed: {e}")
        return False
