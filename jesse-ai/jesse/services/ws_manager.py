import asyncio
import json
import time
from typing import Set, Optional
from starlette.websockets import WebSocket
from queue import Queue, Empty
import threading

from jesse.services.multiprocessing import process_manager
import jesse.helpers as jh


class ConnectionManager:
    """
    WebSocket Connection Manager that works with or without Redis.
    When Redis is not available, it uses an internal message queue.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.is_subscribed = False
        self.redis_subscriber = None
        self.reader_task = None
        self.heartbeat_task = None
        self.heartbeat_interval = 30
        self._message_queue: Queue = Queue()
        self._queue_processor_task = None
        self._redis_available = False
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        await self.start_heartbeat()
        # Start internal queue processor if not running
        await self._start_queue_processor()
        
    def disconnect(self, websocket: WebSocket):
        # Use discard to avoid KeyError if already removed
        self.active_connections.discard(websocket)
        
    async def broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        if not self.active_connections:
            return
            
        for connection in list(self.active_connections):
            message_copy = dict(message)
            # Handle process ID mapping if needed
            if 'id' in message_copy:
                message_copy['id'] = process_manager.get_client_id(message_copy['id'])
            try:
                await connection.send_json(message_copy)
            except Exception as e:
                # Drop the failing connection and continue broadcasting
                jh.terminal_debug(f"WebSocket send error: {str(e)}")
                self.disconnect(connection)
    
    def queue_message(self, message: dict):
        """
        Queue a message for broadcasting (thread-safe).
        Can be called from sync code like backtest workers.
        """
        self._message_queue.put(message)
    
    async def _start_queue_processor(self):
        """Start the internal message queue processor."""
        if self._queue_processor_task is None or self._queue_processor_task.done():
            self._queue_processor_task = asyncio.create_task(self._process_queue())
    
    async def _process_queue(self):
        """Process messages from internal queue and broadcast them."""
        while len(self.active_connections) > 0:
            try:
                # Non-blocking check for messages
                while True:
                    try:
                        message = self._message_queue.get_nowait()
                        await self.broadcast(message)
                    except Empty:
                        break
                await asyncio.sleep(0.1)  # Small delay to prevent CPU spin
            except asyncio.CancelledError:
                break
            except Exception as e:
                jh.terminal_debug(f"Queue processor error: {str(e)}")
                await asyncio.sleep(0.5)
            
    async def start_redis_listener(self, channel_pattern):
        """Start Redis listener if Redis is available, otherwise just run queue processor."""
        # Check if Redis is available
        try:
            from jesse.services.redis import async_redis
            if async_redis is None:
                jh.terminal_debug("Redis not available, using internal message queue only")
                self._redis_available = False
                return
        except Exception:
            self._redis_available = False
            return
            
        # Start or restart the listener task if missing or completed
        if self.reader_task is None or self.reader_task.done():
            self.is_subscribed = True
            self._redis_available = True
            self.reader_task = asyncio.create_task(self._redis_listener(channel_pattern))
            
    async def _redis_listener(self, channel_pattern):
        """Keep the Redis subscription alive and resubscribe on failures with backoff."""
        from jesse.services.redis import async_redis
        
        backoff_seconds = 0.1
        while self.is_subscribed:
            try:
                if async_redis is None:
                    self._redis_available = False
                    await asyncio.sleep(5)
                    continue

                self.redis_subscriber, = await async_redis.psubscribe(channel_pattern)
                backoff_seconds = 0.1  # Reset backoff after successful subscribe
                
                async for ch, message in self.redis_subscriber.iter():
                    message_dict = json.loads(message)
                    await self.broadcast(message_dict)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                jh.terminal_debug(f"Redis listener error: {str(e)}")
                self._redis_available = False
                await asyncio.sleep(backoff_seconds)
                backoff_seconds = min(backoff_seconds * 2, 5.0)
            
    async def start_heartbeat(self):
        if self.heartbeat_task is None or self.heartbeat_task.done():
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
    async def _heartbeat_loop(self):
        """Send periodic heartbeat/ping messages to keep connections alive."""
        while len(self.active_connections) > 0:
            try:
                ping_message = {
                    'event': 'ping',
                    'timestamp': time.time(),
                    'id': 0,
                    'data': None
                }
                await self.broadcast(ping_message)
                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                jh.terminal_debug(f"Heartbeat error: {str(e)}")
                await asyncio.sleep(self.heartbeat_interval)
    
    async def stop_redis_listener(self):
        """Stop the Redis listener and cleanup tasks when no clients remain."""
        if len(self.active_connections) > 0:
            return  # Don't stop if clients are still connected
            
        self.is_subscribed = False
        
        # Cancel Redis reader task
        if self.reader_task and not self.reader_task.done():
            self.reader_task.cancel()
            try:
                await self.reader_task
            except asyncio.CancelledError:
                pass
        
        # Cancel heartbeat task
        if self.heartbeat_task and not self.heartbeat_task.done():
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
        
        # Cancel queue processor task
        if self._queue_processor_task and not self._queue_processor_task.done():
            self._queue_processor_task.cancel()
            try:
                await self._queue_processor_task
            except asyncio.CancelledError:
                pass
                
        # Unsubscribe from Redis if it was connected
        if self._redis_available:
            from jesse.services.env import ENV_VALUES
            try:
                from jesse.services.redis import async_redis
                if async_redis:
                    await async_redis.punsubscribe(f"{ENV_VALUES['APP_PORT']}:channel:*")
            except Exception as e:
                jh.terminal_debug(f"Redis punsubscribe error: {str(e)}")
                
        jh.terminal_debug("WebSocket manager stopped - no more active connections")


# Create a global instance
ws_manager = ConnectionManager()

