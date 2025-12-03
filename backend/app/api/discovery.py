"""
Discovery API routes for KAgent agents, MCPs, and tools
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from app.services.kagent_service import kagent_service
from app.core.database import get_supabase_admin
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/agents")
async def list_agents(
    namespace: Optional[str] = None,
    search: Optional[str] = None,
    department: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List all available agents from KAgent.
    
    Query Parameters:
    - namespace: Filter by K8s namespace
    - search: Search in name and description
    - department: Filter by department label
    - page: Page number
    - page_size: Items per page
    """
    try:
        agents = await kagent_service.list_agents(namespace=namespace)
        
        # Apply filters
        if search:
            search_lower = search.lower()
            agents = [
                a for a in agents
                if search_lower in a.get("name", "").lower()
                or search_lower in a.get("description", "").lower()
            ]
        
        if department:
            agents = [
                a for a in agents
                if a.get("labels", {}).get("department") == department
            ]
        
        # Pagination
        total = len(agents)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_agents = agents[start:end]
        
        return {
            "items": paginated_agents,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/{agent_id}")
async def get_agent(
    agent_id: str,
    namespace: str = Query("default")
):
    """
    Get details of a specific agent from KAgent.
    """
    try:
        agent = await kagent_service.get_agent(agent_id, namespace=namespace)
        
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcps")
async def list_mcps(
    namespace: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List all available MCP servers from KAgent.
    
    Query Parameters:
    - namespace: Filter by K8s namespace
    - search: Search in name and description
    - page: Page number
    - page_size: Items per page
    """
    try:
        mcps = await kagent_service.list_mcps(namespace=namespace)
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            mcps = [
                m for m in mcps
                if search_lower in m.get("name", "").lower()
                or search_lower in m.get("description", "").lower()
            ]
        
        # Pagination
        total = len(mcps)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_mcps = mcps[start:end]
        
        return {
            "items": paginated_mcps,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing MCP servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools")
async def list_tools(
    search: Optional[str] = None,
    mcp_server: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    List all available tools from all MCP servers.
    
    Query Parameters:
    - search: Search in tool name
    - mcp_server: Filter by MCP server name
    - page: Page number
    - page_size: Items per page
    """
    try:
        tools = await kagent_service.list_tools()
        
        # Apply filters
        if search:
            search_lower = search.lower()
            tools = [
                t for t in tools
                if search_lower in t.get("name", "").lower()
            ]
        
        if mcp_server:
            tools = [
                t for t in tools
                if t.get("mcp_server") == mcp_server
            ]
        
        # Pagination
        total = len(tools)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_tools = tools[start:end]
        
        return {
            "items": paginated_tools,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except Exception as e:
        logger.error(f"Error listing tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/agent/{agent_id}")
async def import_agent(
    agent_id: str,
    namespace: str = Query("kagent"),
    pricing_monthly: float = Query(99.0),
    token_billing: str = Query("customer_pays"),
    estimated_usage: str = Query("medium")
):
    """
    Import an agent from KAgent and add it to the marketplace.
    
    This creates a virtual_employees record with source='kagent'.
    """
    try:
        # Get agent from KAgent
        agent = await kagent_service.get_agent(agent_id, namespace=namespace)
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {agent_id} not found in KAgent"
            )
        
        # Create VE record in database
        supabase = get_supabase_admin()
        
        ve_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # Extract department and seniority from labels
        labels = agent.get("labels", {})
        department = labels.get("department", "general")
        seniority = labels.get("seniority", "senior")  # Default to 'senior' (valid: junior, senior, manager)
        
        data = {
            "id": ve_id,
            "name": agent["name"],
            "role": agent["name"],  # Use name as role
            "department": department,
            "seniority_level": seniority,
            "description": agent["description"],
            "pricing_monthly": pricing_monthly,
            "framework": "kagent",
            "status": "stable",
            # Source tracking
            "source": "kagent",
            "source_id": agent["id"],
            "kagent_namespace": agent["namespace"],
            "kagent_version": agent["version"],
            # Business metadata
            "token_billing": token_billing,
            "estimated_usage": estimated_usage,
            "tags": [],
            "category": department,
            "featured": False,
            # Timestamps
            "created_at": now,
            "updated_at": now,
            "last_synced_at": now,
            "sync_status": "synced"
        }
        
        response = supabase.table("virtual_employees").insert(data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to import agent")
        
        # Create HTTPRoute in Agent Gateway for this agent
        from app.services.gateway_config_service import get_gateway_config_service
        
        gateway_config = get_gateway_config_service()
        try:
            route_info = gateway_config.create_agent_route(
                agent_type=agent["name"],
                agent_namespace=namespace
            )
            logger.info(f"Created Agent Gateway route for {agent['name']}: {route_info}")
        except Exception as e:
            logger.error(f"Failed to create Agent Gateway route: {e}")
            # Don't fail the import if route creation fails
            # Admin can manually create route later if needed
        
        return {
            "success": True,
            "ve_id": ve_id,
            "agent_id": agent_id,
            "message": f"Agent {agent_id} imported successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/agents/{ve_id}")
async def delete_agent(ve_id: str):
    """
    Delete an imported agent from the marketplace.
    
    This will:
    1. Delete the virtual_employees record
    2. Delete the HTTPRoute and TrafficPolicy from Agent Gateway
    3. Ensure no customers are still using this agent
    """
    try:
        supabase = get_supabase_admin()
        
        # Get the VE record to find agent_type
        ve_response = supabase.table("virtual_employees").select("*").eq("id", ve_id).execute()
        
        if not ve_response.data:
            raise HTTPException(status_code=404, detail=f"Agent {ve_id} not found")
        
        ve = ve_response.data[0]
        agent_type = ve.get("source_id") or ve.get("name")
        
        # Check if any customers are using this agent
        customer_ves = supabase.table("customer_ves").select("id").eq("marketplace_agent_id", ve_id).execute()
        
        if customer_ves.data and len(customer_ves.data) > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete agent. {len(customer_ves.data)} customer(s) are currently using it. Please ensure all customers unhire this agent first."
            )
        
        # Delete from database
        supabase.table("virtual_employees").delete().eq("id", ve_id).execute()
        logger.info(f"Deleted VE record {ve_id}")
        
        # Delete HTTPRoute and TrafficPolicy from Agent Gateway
        from app.services.gateway_config_service import get_gateway_config_service
        
        gateway_config = get_gateway_config_service()
        try:
            success = gateway_config.delete_agent_route(agent_type)
            if success:
                logger.info(f"Deleted Agent Gateway route and policy for {agent_type}")
            else:
                logger.warning(f"Failed to delete Agent Gateway route for {agent_type}")
        except Exception as e:
            logger.error(f"Error deleting Agent Gateway route: {e}")
            # Don't fail the delete if gateway cleanup fails
        
        return {
            "success": True,
            "ve_id": ve_id,
            "message": f"Agent {ve_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting agent {ve_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
