from typing import List, Optional, Dict, Any, AsyncGenerator
from datetime import datetime
import logging
import json
from .base import BaseService

logger = logging.getLogger(__name__)

class MessageService(BaseService):
    """Service for message operations"""
    
    async def send_message_stream(
        self,
        customer_id: str,
        to_ve_id: str,
        subject: str,
        content: str,
        thread_id: Optional[str] = None,
        replied_to_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Send a message and stream the response (SSE format)
        """
        try:
            # 1. Save User Message
            message_data = {
                "customer_id": customer_id,
                "customer_ve_id": to_ve_id,
                "from_type": "customer",
                "to_ve_id": to_ve_id,
                "subject": subject,
                "content": content,
                "thread_id": thread_id,
                "replied_to_id": replied_to_id,
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("messages").insert(message_data).execute()
            user_message = result.data[0] if result.data else None
            
            if not user_message:
                yield f"data: {json.dumps({'type': 'error', 'content': 'Failed to save message'})}\n\n"
                return

            # 2. Get Agent Details
            ve_record = self.supabase.table("customer_ves").select("agent_type").eq("id", to_ve_id).single().execute()
            if not ve_record.data:
                yield f"data: {json.dumps({'type': 'error', 'content': 'VE not found'})}\n\n"
                return
            
            agent_type = ve_record.data.get("agent_type") or "marketing-manager"
            
            from app.services.agent_gateway_service import agent_gateway_service
            
            # 3. Stream from Agent Gateway
            accumulated_response = ""
            
            async for event in agent_gateway_service.invoke_agent_stream(
                customer_id=customer_id,
                agent_type=agent_type,
                message=content,
                session_id=thread_id or user_message["id"],
                user_id=customer_id
            ):
                # Accumulate text content for final save
                if event["type"] == "message":
                    accumulated_response += event["content"]
                
                # Yield SSE event
                yield f"data: {json.dumps(event)}\n\n"
            
            # 4. Save Final Agent Response
            if accumulated_response:
                response_data = {
                    "customer_id": customer_id,
                    "customer_ve_id": to_ve_id,
                    "from_type": "ve",
                    "from_ve_id": to_ve_id,
                    "subject": f"Re: {subject}",
                    "content": accumulated_response,
                    "thread_id": thread_id or user_message["id"],
                    "replied_to_id": user_message["id"],
                    "read": False,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.supabase.table("messages").insert(response_data).execute()
                
            # Send done signal
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    async def send_message(
        self,
        customer_id: str,
        to_ve_id: str,
        subject: str,
        content: str,
        thread_id: Optional[str] = None,
        replied_to_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to a VE and get response"""
        try:
            # 1. Save User Message
            message_data = {
                "customer_id": customer_id,
                "customer_ve_id": to_ve_id, # Link message to the VE
                "from_type": "customer",
                "to_ve_id": to_ve_id,
                "subject": subject,
                "content": content,
                "thread_id": thread_id,
                "replied_to_id": replied_to_id,
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("messages").insert(message_data).execute()
            user_message = result.data[0] if result.data else None
            
            if not user_message:
                raise Exception("Failed to save user message")

            # 2. Forward to Agent Gateway (Shared Agent Runtime)
            if to_ve_id:
                try:
                    # Get VE details to find agent_type
                    ve_record = self.supabase.table("customer_ves").select("agent_type").eq("id", to_ve_id).single().execute()
                    if not ve_record.data:
                        raise Exception("VE not found")
                    
                    agent_type = ve_record.data.get("agent_type")
                    if not agent_type:
                        # Fallback for legacy records
                        agent_type = "marketing-manager" 
                    
                    from app.services.agent_gateway_service import agent_gateway_service
                    
                    logger.info(f"Invoking agent type: {agent_type} for customer: {customer_id}")
                    
                    # Invoke shared agent
                    agent_result = await agent_gateway_service.invoke_agent(
                        customer_id=customer_id,
                        agent_type=agent_type,
                        message=content,
                        session_id=thread_id or user_message["id"],
                        user_id=customer_id
                    )
                    
                    response_content = agent_result.get("message", "No response")
                    
                    # Check if blocked by security
                    if agent_result.get("blocked"):
                        logger.warning(f"Message blocked by security for customer {customer_id}")
                    
                    # 3. Save Agent Response
                    response_data = {
                        "customer_id": customer_id,
                        "customer_ve_id": to_ve_id, # Link message to the VE
                        "from_type": "ve",
                        "from_ve_id": to_ve_id,
                        "subject": f"Re: {subject}",
                        "content": response_content,
                        "thread_id": thread_id or user_message["id"], # Use user message ID as thread ID if new
                        "replied_to_id": user_message["id"],
                        "read": False,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    self.supabase.table("messages").insert(response_data).execute()
                    logger.info(f"Agent response saved for customer {customer_id}")
                    
                except Exception as agent_error:
                    # Log the error but don't fail the entire message send
                    logger.error(f"Failed to get agent response: {agent_error}", exc_info=True)
                    # Optionally, save an error message from the system
                    error_response_data = {
                        "customer_id": customer_id,
                        "customer_ve_id": to_ve_id,
                        "from_type": "ve",
                        "from_ve_id": to_ve_id,
                        "subject": f"Re: {subject}",
                        "content": f"I apologize, but I'm currently experiencing technical difficulties. Please try again later. (Error: {str(agent_error)[:100]})",
                        "thread_id": thread_id or user_message["id"],
                        "replied_to_id": user_message["id"],
                        "read": False,
                        "created_at": datetime.utcnow().isoformat()
                    }
                    try:
                        self.supabase.table("messages").insert(error_response_data).execute()
                    except Exception as e:
                        logger.error(f"Failed to save error message: {e}")
            
            return user_message
        except Exception as e:
            self._handle_error(e, "MessageService.send_message")
    
    async def send_message_stream(
        self,
        customer_id: str,
        to_ve_id: str,
        subject: str,
        content: str,
        thread_id: Optional[str] = None,
        replied_to_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a message to a VE and stream the response
        
        Yields:
            Dict events from agent stream
        """
        try:
            # 1. Save User Message
            message_data = {
                "customer_id": customer_id,
                "customer_ve_id": to_ve_id,
                "from_type": "customer",
                "to_ve_id": to_ve_id,
                "subject": subject,
                "content": content,
                "thread_id": thread_id,
                "replied_to_id": replied_to_id,
                "read": False,
                "created_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("messages").insert(message_data).execute()
            user_message = result.data[0] if result.data else None
            
            if not user_message:
                raise Exception("Failed to save user message")
            
            # Yield user message first
            yield {"type": "user_message", "data": user_message}
            
            # 2. Stream agent response
            if to_ve_id:
                try:
                    # Get VE details
                    ve_record = self.supabase.table("customer_ves").select("agent_type").eq("id", to_ve_id).single().execute()
                    if not ve_record.data:
                        raise Exception("VE not found")
                    
                    agent_type = ve_record.data.get("agent_type")
                    if not agent_type:
                        agent_type = "marketing-manager"
                    
                    from app.services.agent_gateway_service import agent_gateway_service
                    
                    logger.info(f"Streaming agent type: {agent_type} for customer: {customer_id}")
                    
                    # Accumulate full response for saving
                    full_response = ""
                    
                    # Stream from agent
                    async for event in agent_gateway_service.invoke_agent_stream(
                        customer_id=customer_id,
                        agent_type=agent_type,
                        message=content,
                        session_id=thread_id or user_message["id"],
                        user_id=customer_id
                    ):
                        # Forward event to client
                        yield event
                        
                        # Accumulate message content
                        if event.get("type") in ["message", "artifact"]:
                            full_response += event.get("content", "")
                    
                    # 3. Save final agent response
                    if full_response:
                        response_data = {
                            "customer_id": customer_id,
                            "customer_ve_id": to_ve_id,
                            "from_type": "ve",
                            "from_ve_id": to_ve_id,
                            "subject": f"Re: {subject}",
                            "content": full_response,
                            "thread_id": thread_id or user_message["id"],
                            "replied_to_id": user_message["id"],
                            "read": False,
                            "created_at": datetime.utcnow().isoformat()
                        }
                        result = self.supabase.table("messages").insert(response_data).execute()
                        agent_message = result.data[0] if result.data else None
                        
                        # Yield final saved message
                        yield {"type": "agent_message_saved", "data": agent_message}
                        
                except Exception as agent_error:
                    logger.error(f"Failed to stream agent response: {agent_error}", exc_info=True)
                    yield {"type": "error", "content": str(agent_error)}
                    
        except Exception as e:
            logger.error(f"Error in send_message_stream: {e}", exc_info=True)
            yield {"type": "error", "content": str(e)}
    
    async def get_inbox(
        self,
        customer_id: str,
        folder: str = "inbox"
    ) -> List[Dict[str, Any]]:
        """Get messages grouped by thread"""
        try:
            query = self.supabase.table("messages").select("*").eq("customer_id", customer_id)
            
            if folder == "inbox":
                # Inbox = messages FROM VEs (from_type = 've' or from_ve_id is not null)
                query = query.eq("from_type", "ve")
            elif folder == "sent":
                # Sent = messages FROM customer
                query = query.eq("from_type", "customer")
            
            result = query.order("created_at", desc=True).execute()
            return result.data
        except Exception as e:
            self._handle_error(e, "MessageService.get_inbox")
    
    async def get_thread(
        self,
        thread_id: str,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Get all messages in a thread"""
        try:
            result = (
                self.supabase.table("messages")
                .select("*")
                .eq("thread_id", thread_id)
                .eq("customer_id", customer_id)
                .order("created_at", asc=True)
                .execute()
            )
            return result.data
        except Exception as e:
            self._handle_error(e, "MessageService.get_thread")
    
    async def mark_as_read(
        self,
        message_id: str,
        customer_id: str
    ) -> Dict[str, Any]:
        """Mark a message as read"""
        try:
            result = (
                self.supabase.table("messages")
                .update({"read": True})
                .eq("id", message_id)
                .eq("customer_id", customer_id)
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            self._handle_error(e, "MessageService.mark_as_read")
