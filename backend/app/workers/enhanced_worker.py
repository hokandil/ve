"""
Enhanced Background Worker
Processes tasks using Redis queues, Agent Gateway, and Kubernetes services
"""
import asyncio
import os
import logging
from datetime import datetime
from supabase import create_client

from app.services.redis_queue_service import get_redis_queue_service
from app.services.agent_gateway_service import get_agent_gateway_service
from app.services.kubernetes_service import get_kubernetes_service
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")


class EnhancedTaskWorker:
    """Enhanced worker for processing VE tasks"""
    
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        self.redis_queue = None
        self.agent_gateway = get_agent_gateway_service()
        self.k8s_service = get_kubernetes_service()
        self.running = False
    
    async def start(self):
        """Start the worker"""
        logger.info("🚀 Starting Enhanced Task Worker...")
        
        # Connect to Redis
        self.redis_queue = await get_redis_queue_service()
        
        self.running = True
        
        # Start multiple worker tasks
        await asyncio.gather(
            self.process_high_priority_tasks(),
            self.process_medium_priority_tasks(),
            self.process_low_priority_tasks(),
            self.monitor_agent_health(),
            self.process_webhooks()
        )
    
    async def stop(self):
        """Stop the worker"""
        logger.info("Stopping worker...")
        self.running = False
        if self.redis_queue:
            await self.redis_queue.disconnect()
    
    async def process_high_priority_tasks(self):
        """Process high and urgent priority tasks"""
        logger.info("📌 High priority task processor started")
        
        while self.running:
            try:
                # Check urgent queue first
                task = await self.redis_queue.dequeue_task(priority="urgent", timeout=1)
                if not task:
                    # Then check high priority
                    task = await self.redis_queue.dequeue_task(priority="high", timeout=1)
                
                if task:
                    await self.process_task(task)
                else:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in high priority processor: {e}")
                await asyncio.sleep(5)
    
    async def process_medium_priority_tasks(self):
        """Process medium priority tasks"""
        logger.info("📋 Medium priority task processor started")
        
        while self.running:
            try:
                task = await self.redis_queue.dequeue_task(priority="medium", timeout=5)
                
                if task:
                    await self.process_task(task)
                else:
                    await asyncio.sleep(2)
                    
            except Exception as e:
                logger.error(f"Error in medium priority processor: {e}")
                await asyncio.sleep(5)
    
    async def process_low_priority_tasks(self):
        """Process low priority tasks"""
        logger.info("📝 Low priority task processor started")
        
        while self.running:
            try:
                task = await self.redis_queue.dequeue_task(priority="low", timeout=10)
                
                if task:
                    await self.process_task(task)
                else:
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Error in low priority processor: {e}")
                await asyncio.sleep(5)
    
    async def process_task(self, task_item: dict):
        """Process a single task"""
        try:
            task_id = task_item["task_id"]
            customer_id = task_item["customer_id"]
            task_data = task_item["task_data"]
            
            logger.info(f"🔄 Processing task {task_id}")
            
            # Get task details from database
            task_response = self.supabase.table("tasks").select(
                "*, customer_ves(*, virtual_employees(*))"
            ).eq("id", task_id).single().execute()
            
            if not task_response.data:
                logger.error(f"Task {task_id} not found")
                return
            
            task = task_response.data
            assigned_ve = task.get("customer_ves")
            
            if not assigned_ve:
                logger.error(f"No VE assigned to task {task_id}")
                return
            
            # Update task status
            self.supabase.table("tasks").update({
                "status": "in_progress",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", task_id).execute()
            
            # Invoke agent via Agent Gateway
            namespace = f"{settings.K8S_NAMESPACE_PREFIX}{customer_id}"
            
            try:
                response = await self.agent_gateway.invoke_agent(
                    namespace=namespace,
                    agent_name=assigned_ve["agent_name"],
                    request_data={
                        "task_id": task_id,
                        "task": task["title"],
                        "description": task["description"],
                        "priority": task.get("priority", "medium"),
                        "context": task_data.get("context", {})
                    },
                    customer_id=customer_id
                )
                
                # Process agent response
                if response.get("status") == "success":
                    # Task completed successfully
                    self.supabase.table("tasks").update({
                        "status": "completed",
                        "completed_at": datetime.utcnow().isoformat()
                    }).eq("id", task_id).execute()
                    
                    # Create completion message
                    self.supabase.table("messages").insert({
                        "task_id": task_id,
                        "customer_id": customer_id,
                        "from_type": "ve",
                        "from_ve_id": assigned_ve["id"],
                        "to_type": "customer",
                        "to_user_id": customer_id,
                        "subject": f"Task Completed: {task['title']}",
                        "content": response.get("response", {}).get("message", "Task completed successfully"),
                        "message_type": "email",
                        "read": False
                    }).execute()
                    
                    logger.info(f"✅ Task {task_id} completed successfully")
                else:
                    # Task failed
                    self.supabase.table("tasks").update({
                        "status": "cancelled"
                    }).eq("id", task_id).execute()
                    
                    logger.error(f"❌ Task {task_id} failed")
                    
            except Exception as e:
                logger.error(f"Agent invocation failed for task {task_id}: {e}")
                
                # Update task status to error
                self.supabase.table("tasks").update({
                    "status": "cancelled"
                }).eq("id", task_id).execute()
                
        except Exception as e:
            logger.error(f"Error processing task: {e}")
    
    async def monitor_agent_health(self):
        """Monitor health of deployed agents"""
        logger.info("🏥 Agent health monitor started")
        
        while self.running:
            try:
                # Get all active customer VEs
                ves_response = self.supabase.table("customer_ves").select("*").eq("status", "active").execute()
                
                for ve in ves_response.data:
                    try:
                        # Check agent status in Kubernetes
                        namespace = ve["namespace"]
                        agent_name = ve["agent_name"]
                        
                        status = await self.k8s_service.get_agent_status(namespace, agent_name)
                        
                        if status and not status.get("ready", True):
                            logger.warning(f"Agent {agent_name} is not ready")
                            
                            # Update VE status
                            self.supabase.table("customer_ves").update({
                                "status": "unhealthy"
                            }).eq("id", ve["id"]).execute()
                        
                    except Exception as e:
                        logger.error(f"Error checking agent {ve['agent_name']}: {e}")
                
                # Check every 30 seconds
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(60)
    
    async def process_webhooks(self):
        """Process webhook events from queue"""
        logger.info("🔔 Webhook processor started")
        
        while self.running:
            try:
                # This would process webhook events from Redis queue
                # For now, just sleep
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in webhook processor: {e}")
                await asyncio.sleep(10)


async def main():
    """Main entry point"""
    worker = EnhancedTaskWorker()
    
    try:
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        await worker.stop()
    except Exception as e:
        logger.error(f"Worker error: {e}")
        await worker.stop()


if __name__ == "__main__":
    asyncio.run(main())
