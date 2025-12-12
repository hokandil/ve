from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional
from pydantic import BaseModel
from ..core.security import get_current_user, verify_service_token
from ..core.database import get_supabase_admin
from ..services.message_service import MessageService

router = APIRouter(prefix="/api/messages", tags=["messages"])

from app.schemas import MessageCreate, TaskCreate
from ..services.task_service import TaskService

class DelegationRequest(BaseModel):
    customer_id: str
    target_agent_id: str
    task: str

@router.post("/delegate")
async def delegate_task(
    request: DelegationRequest,
    authorized: bool = Depends(verify_service_token)
):
    """
    Delegate a task to another agent.
    Called by Delegation MCP Server.
    """
    supabase = get_supabase_admin()
    message_service = MessageService(supabase)
    
    # Send message to target agent
    # We treat delegation as a message from the system (or we could track the source agent if we had that info)
    # For now, we'll send it as a message from the customer (on behalf of the delegating agent)
    # or better, create a new message type "delegation"
    
    result = await message_service.send_message(
        customer_id=request.customer_id,
        to_ve_id=request.target_agent_id,
        subject="Delegated Task",
        content=f"Task delegated to you: {request.task}",
        # We don't have a thread_id here, so it starts a new thread
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to delegate task")
        
    return {"status": "success", "message_id": result.get("id")}

@router.post("/send")
async def send_message(
    message: MessageCreate,
    user = Depends(get_current_user)
):
    """
    Send a message to a VE.
    If to_ve_id is 'orchestrator', a new task is created and routed.
    """
    supabase = get_supabase_admin()
    message_service = MessageService(supabase)
    
    # Handle Orchestrator Routing (Create Task)
    if message.to_ve_id == "orchestrator":
        task_service = TaskService(supabase)
        
        # Create a task from the message
        task_create = TaskCreate(
            title=message.subject,
            description=message.content,
            priority="medium" # Default priority
        )
        
        # Create task (this will trigger Redis enqueue and Orchestrator routing)
        task = await task_service.create_task(task_create, user["id"])
        
        # Create a system message acknowledging receipt
        result = await message_service.send_message(
            customer_id=user["id"],
            to_ve_id=None, # System message
            subject=f"Re: {message.subject}",
            content=f"Task created successfully (ID: {task['id']}). The orchestrator is processing your request.",
            thread_id=message.thread_id,
            replied_to_id=message.replied_to_id
        )
        return result

    # Normal Message to VE
    result = await message_service.send_message(
        customer_id=user["id"],
        to_ve_id=message.to_ve_id,
        subject=message.subject,
        content=message.content,
        thread_id=message.thread_id,
        replied_to_id=message.replied_to_id
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to send message")
    
    return result

@router.post("/stream")
async def send_message_stream(
    message: MessageCreate,
    user = Depends(get_current_user)
):
    """
    Send a message and stream the response (SSE).
    """
    supabase = get_supabase_admin()
    message_service = MessageService(supabase)
    
    # For now, orchestrator routing doesn't support streaming, so we handle it normally
    if message.to_ve_id == "orchestrator":
        # ... (reuse logic or call existing service method)
        # For simplicity, we just call the non-streaming method and yield the result as a single event
        # But ideally we should refactor orchestrator to stream too.
        # For this phase, we focus on Agent streaming.
        pass

    return StreamingResponse(
        message_service.send_message_stream(
            customer_id=user["id"],
            to_ve_id=message.to_ve_id,
            subject=message.subject,
            content=message.content,
            thread_id=message.thread_id,
            replied_to_id=message.replied_to_id
        ),
        media_type="text/event-stream"
    )

@router.get("/inbox")
async def get_inbox(
    folder: str = "inbox",
    user = Depends(get_current_user)
):
    """Get messages inbox"""
    supabase = get_supabase_admin()
    service = MessageService(supabase)
    
    messages = await service.get_inbox(
        customer_id=user["id"],
        folder=folder
    )
    
    return messages

@router.get("/thread/{thread_id}")
async def get_thread(
    thread_id: str,
    user = Depends(get_current_user)
):
    """Get messages in a thread"""
    supabase = get_supabase_admin()
    service = MessageService(supabase)
    
    messages = await service.get_thread(
        thread_id=thread_id,
        customer_id=user["id"]
    )
    
    return messages

@router.patch("/{message_id}/read")
async def mark_as_read(
    message_id: str,
    user = Depends(get_current_user)
):
    """Mark message as read"""
    supabase = get_supabase_admin()
    service = MessageService(supabase)
    
    result = await service.mark_as_read(
        message_id=message_id,
        customer_id=user["id"]
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Message not found")
    
    return result
@router.post("/ves/{ve_id}/chat")
async def chat_with_ve(
    ve_id: str,
    message: MessageCreate,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user)
):
    """
    Chat with a VE - Real-time version (Centrifugo).
    Starts a background task that streams agent responses to a Centrifugo channel.
    """
    import logging
    from app.core.centrifugo import get_centrifugo_client
    
    logger = logging.getLogger(__name__)
    
    # Generate a channel name if not provided (e.g., chat:thread_id)
    # If thread_id is new, we might need to generate it here or let service handle it.
    # For simplicity, we'll use a user-specific channel or the provided thread_id.
    thread_id = message.thread_id
    if not thread_id:
        import uuid
        thread_id = str(uuid.uuid4())
        
    channel = f"chat:{thread_id}"
    
    async def stream_to_centrifugo(
        customer_id: str,
        ve_id: str,
        subject: str,
        content: str,
        thread_id: str,
        channel: str
    ):
        supabase = get_supabase_admin()
        message_service = MessageService(supabase)
        centrifugo = get_centrifugo_client()
        
        try:
            async for event in message_service.send_message_stream(
                customer_id=customer_id,
                to_ve_id=ve_id,
                subject=subject,
                content=content,
                thread_id=thread_id
            ):
                # Publish event to Centrifugo
                await centrifugo.publish(channel, event)
                
        except Exception as e:
            logger.error(f"Background streaming error: {e}", exc_info=True)
            await centrifugo.publish(channel, {"type": "error", "content": str(e)})

    # Start background task
    background_tasks.add_task(
        stream_to_centrifugo,
        customer_id=user["id"],
        ve_id=ve_id,
        subject=message.subject or "Chat",
        content=message.content,
        thread_id=thread_id,
        channel=channel
    )
    
    return {
        "status": "processing",
        "thread_id": thread_id,
        "channel": channel,
        "message": "Agent is processing your request. Subscribe to the channel for updates."
    }

@router.get("/ves/{ve_id}/history")
async def get_chat_history(
    ve_id: str,
    limit: int = 50,
    user = Depends(get_current_user)
):
    """Get chat history with a specific VE"""
    supabase = get_supabase_admin()
    
    # Fetch messages where (from_ve_id = ve_id OR to_ve_id = ve_id) AND customer_id = user.id
    # Ordered by created_at ASC
    
    response = supabase.table("messages")\
        .select("*")\
        .eq("customer_id", user["id"])\
        .or_(f"from_ve_id.eq.{ve_id},to_ve_id.eq.{ve_id}")\
        .order("created_at", desc=False)\
        .limit(limit)\
        .execute()
        
    return response.data

from fastapi import Header, HTTPException
from app.core.config import settings

async def verify_service_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    # In production, use a dedicated secret. For now, checking against configured token.
    if token != settings.AGENT_GATEWAY_AUTH_TOKEN: # Reusing gateway token for simplicity
        raise HTTPException(status_code=401, detail="Invalid service token")
    return token

@router.post("/delegate")
async def delegate_to_agent(
    request: DelegationRequest,
    token: str = Depends(verify_service_token)
):
    """
    Delegation endpoint called by MCP server.
    Invokes target agent and returns response.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    supabase = get_supabase_admin()
    
    try:
        # 1. Verify target agent exists and belongs to customer
        ve_record = supabase.table("customer_ves")\
            .select("id, persona_name, agent_type")\
            .eq("id", request.target_agent_id)\
            .eq("customer_id", request.customer_id)\
            .single()\
            .execute()
        
        if not ve_record.data:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {request.target_agent_id} not found or not accessible"
            )
        
        agent_data = ve_record.data
        agent_type = agent_data.get("agent_type")
        
        if not agent_type:
            raise HTTPException(
                status_code=400,
                detail="Agent has no agent_type configured"
            )
        
        # 2. Invoke target agent
        from app.services.agent_gateway_service import agent_gateway_service
        
        logger.info(
            f"Delegation: customer {request.customer_id} delegating to "
            f"{agent_data['persona_name']} ({agent_type})"
        )
        
        # Use non-streaming invoke for delegation (simpler)
        result = await agent_gateway_service.invoke_agent(
            customer_id=request.customer_id,
            agent_type=agent_type,
            message=request.task,
            user_id=request.customer_id
        )
        
        return {
            "target_agent_id": request.target_agent_id,
            "target_agent_name": agent_data["persona_name"],
            "response": result.get("message", "No response")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delegation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Delegation failed: {str(e)}"
        )
