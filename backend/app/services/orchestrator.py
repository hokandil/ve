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
        
        # Invoke the target agent to start working on the task
        try:
            agent_type = target_ve.get("agent_type")
            if agent_type:
                # Format task as a message
                prompt = f"New Task Assigned: {task_description}"
                
                agent_response = await agent_gateway.invoke_agent(
                    customer_id=customer_id,
                    agent_type=agent_type,
                    message=prompt,
                    user_id=customer_id
                )
                
                # Add agent response as a comment
                if agent_response and "message" in agent_response:
                    from datetime import datetime
                    supabase.table("task_comments").insert({
                        "task_id": task_id,
                        "customer_id": customer_id,
                        "content": agent_response["message"],
                        "author_type": "ve",
                        "created_at": datetime.utcnow().isoformat()
                    }).execute()
        except Exception as e:
            logger.error(f"Failed to invoke target agent {target_ve['persona_name']}: {e}")
        
        return {
            "task_id": task_id,
            "routed_to_ve": target_ve_id,
            "status": "routed",
            "message": f"Task assigned to {target_ve['persona_name']}"
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
    Route a specific task to a specific VE
    """
    try:
        supabase = get_supabase_admin()
        
        # Get VE details
        ve_response = supabase.table("customer_ves").select("*").eq("id", ve_id).eq("customer_id", customer_id).execute()
        
        if not ve_response.data:
            raise Exception("VE not found")
        
        ve = ve_response.data[0]
        
        # Update task status
        supabase.table("tasks").update({"status": "in_progress"}).eq("id", task_id).execute()
        
        # TODO: Call Agent Gateway to invoke VE
        logger.info(f"Routed task {task_id} to VE {ve['persona_name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"Task routing failed: {e}")
        return False
