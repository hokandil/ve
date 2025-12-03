"""
Redis Queue Service
Handles background task queuing and processing using Redis
"""
import logging
import json
import redis.asyncio as redis
from typing import Dict, Any, Optional, Callable
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisQueueService:
    """Service for managing Redis-based task queues"""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client: Optional[redis.Redis] = None
        self.task_queue_name = "ve:tasks"
        self.message_queue_name = "ve:messages"
        self.webhook_queue_name = "ve:webhooks"
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.warning(f"Could not connect to Redis: {e}. Queue operations will be disabled.")
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Disconnected from Redis")
    
    async def enqueue_task(
        self,
        task_id: str,
        customer_id: str,
        task_data: Dict[str, Any],
        priority: str = "medium"
    ) -> bool:
        """
        Enqueue a task for background processing
        
        Args:
            task_id: Task UUID
            customer_id: Customer UUID
            task_data: Task information
            priority: Task priority (low, medium, high, urgent)
            
        Returns:
            bool: True if enqueued successfully
        """
        if not self.redis_client:
            logger.warning("Redis not connected, skipping task enqueue")
            return False
        
        try:
            queue_item = {
                "task_id": task_id,
                "customer_id": customer_id,
                "task_data": task_data,
                "priority": priority,
                "enqueued_at": asyncio.get_event_loop().time()
            }
            
            # Use different queues based on priority
            queue_name = f"{self.task_queue_name}:{priority}"
            
            await self.redis_client.lpush(queue_name, json.dumps(queue_item))
            logger.info(f"Enqueued task {task_id} with priority {priority}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task: {e}")
            return False
    
    async def dequeue_task(self, priority: str = "medium", timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Dequeue a task from the queue
        
        Args:
            priority: Priority queue to check
            timeout: Blocking timeout in seconds
            
        Returns:
            Task data or None if queue is empty
        """
        if not self.redis_client:
            return None
        
        try:
            queue_name = f"{self.task_queue_name}:{priority}"
            result = await self.redis_client.brpop(queue_name, timeout=timeout)
            
            if result:
                _, task_json = result
                return json.loads(task_json)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {e}")
            return None
    
    async def enqueue_message(
        self,
        message_id: str,
        customer_id: str,
        message_data: Dict[str, Any]
    ) -> bool:
        """Enqueue a message for processing"""
        if not self.redis_client:
            return False
        
        try:
            queue_item = {
                "message_id": message_id,
                "customer_id": customer_id,
                "message_data": message_data
            }
            
            await self.redis_client.lpush(
                self.message_queue_name,
                json.dumps(queue_item)
            )
            
            logger.info(f"Enqueued message {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            return False
    
    async def enqueue_webhook(
        self,
        event_type: str,
        customer_id: str,
        webhook_data: Dict[str, Any]
    ) -> bool:
        """Enqueue a webhook event for processing"""
        if not self.redis_client:
            return False
        
        try:
            queue_item = {
                "event_type": event_type,
                "customer_id": customer_id,
                "webhook_data": webhook_data
            }
            
            await self.redis_client.lpush(
                self.webhook_queue_name,
                json.dumps(queue_item)
            )
            
            logger.info(f"Enqueued webhook event {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue webhook: {e}")
            return False
    
    async def set_cache(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis cache
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            expire_seconds: Optional expiration time
            
        Returns:
            bool: True if cached successfully
        """
        if not self.redis_client:
            return False
        
        try:
            serialized_value = json.dumps(value)
            
            if expire_seconds:
                await self.redis_client.setex(key, expire_seconds, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache: {e}")
            return False
    
    async def get_cache(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            value = await self.redis_client.get(key)
            
            if value:
                return json.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get cache: {e}")
            return None
    
    async def delete_cache(self, key: str) -> bool:
        """Delete a key from cache"""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete cache: {e}")
            return False
    
    async def publish_event(self, channel: str, event_data: Dict[str, Any]) -> bool:
        """
        Publish an event to a Redis pub/sub channel
        
        Args:
            channel: Channel name
            event_data: Event data to publish
            
        Returns:
            bool: True if published successfully
        """
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.publish(
                channel,
                json.dumps(event_data)
            )
            
            logger.info(f"Published event to channel {channel}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False
    
    async def subscribe_to_events(
        self,
        channel: str,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to events on a Redis pub/sub channel
        
        Args:
            channel: Channel name
            callback: Function to call when event is received
        """
        if not self.redis_client:
            logger.warning("Redis not connected, cannot subscribe")
            return
        
        try:
            pubsub = self.redis_client.pubsub()
            await pubsub.subscribe(channel)
            
            logger.info(f"Subscribed to channel {channel}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        event_data = json.loads(message["data"])
                        await callback(event_data)
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        
        except Exception as e:
            logger.error(f"Subscription error: {e}")


# Singleton instance
_redis_queue_service = None


async def get_redis_queue_service() -> RedisQueueService:
    """Get or create Redis queue service singleton"""
    global _redis_queue_service
    if _redis_queue_service is None:
        _redis_queue_service = RedisQueueService()
        await _redis_queue_service.connect()
    return _redis_queue_service
