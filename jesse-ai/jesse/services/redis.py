import simplejson as json
import asyncio
import jesse.helpers as jh
from jesse.libs.custom_json import NpEncoder
import os
import base64
from jesse.services.env import ENV_VALUES

# Initialize Redis connections as None - they will stay None if Redis is unavailable
async_redis = None
sync_redis = None

# Try to import Redis libraries but don't fail if not available
try:
    import aioredis
    import redis as sync_redis_lib
    _redis_libs_available = True
except ImportError:
    _redis_libs_available = False
    aioredis = None
    sync_redis_lib = None

# Initialize sync_redis if libraries are available
if _redis_libs_available:
    try:
        sync_redis = sync_redis_lib.Redis(
            host=ENV_VALUES.get('REDIS_HOST', 'localhost'),
            port=int(ENV_VALUES.get('REDIS_PORT', 6379)),
            password=ENV_VALUES.get('REDIS_PASSWORD') or None,
            db=int(ENV_VALUES.get('REDIS_DB') or 0),
            decode_responses=False # Keep it False for consistency with Jesse's binary/json handling
        )
        # Test connection
        sync_redis.ping()
    except Exception as e:
        jh.terminal_debug(f"Sync Redis connection failed: {e}")
        sync_redis = None


async def init_redis():
    """Initialize async Redis connection if libraries are available."""
    global async_redis
    if not _redis_libs_available:
        return None
    try:
        async_redis = await aioredis.create_redis_pool(
            address=(ENV_VALUES.get('REDIS_HOST', 'localhost'), ENV_VALUES.get('REDIS_PORT', 6379)),
            password=ENV_VALUES.get('REDIS_PASSWORD') or None,
            db=int(ENV_VALUES.get('REDIS_DB') or 0),
        )
        return async_redis
    except Exception as e:
        jh.terminal_debug(f"Async Redis connection failed: {e}")
        async_redis = None
        return None


def sync_publish(event: str, msg, compression: bool = False):
    """
    Publish a message via Redis or fallback to WebSocket manager's internal queue.
    """
    if jh.is_unit_testing():
        raise EnvironmentError('sync_publish() should NOT be called during testing.')

    if compression:
        msg = jh.gzip_compress(msg)
        msg = base64.b64encode(msg).decode('utf-8')

    message_data = {
        'id': os.getpid(),
        'event': f'{jh.app_mode()}.{event}',
        'is_compressed': compression,
        'data': msg
    }

    # Try Redis first
    if sync_redis is not None:
        try:
            sync_redis.publish(
                f"{ENV_VALUES['APP_PORT']}:channel:1",
                json.dumps(message_data, ignore_nan=True, cls=NpEncoder)
            )
            return
        except Exception as e:
            jh.terminal_debug(f"Redis publish error: {e}")

    # Fallback to WebSocket manager's internal queue
    try:
        # Debug print for when Redis is unavailable
        print(f"Fallback Pub: {message_data['event']}")
        from jesse.services.ws_manager import ws_manager
        ws_manager.queue_message(message_data)
    except Exception as e:
        jh.terminal_debug(f"WebSocket queue error: {e}")


async def async_publish(event: str, msg, compression: bool = False):
    """
    Async publish a message via Redis or fallback to WebSocket manager's internal queue.
    """
    if jh.is_unit_testing():
        raise EnvironmentError('async_publish() should NOT be called during testing.')

    if compression:
        msg = jh.gzip_compress(msg)
        msg = base64.b64encode(msg).decode('utf-8')

    message_data = {
        'id': os.getpid(),
        'event': f'{jh.app_mode()}.{event}',
        'is_compressed': compression,
        'data': msg
    }

    # Try Redis first
    if async_redis is not None:
        try:
            await async_redis.publish(
                f"{ENV_VALUES['APP_PORT']}:channel:1",
                json.dumps(message_data, ignore_nan=True, cls=NpEncoder)
            )
            return
        except Exception as e:
            jh.terminal_debug(f"Redis async publish error: {e}")
    
    # Fallback to WebSocket manager's internal queue
    try:
        from jesse.services.ws_manager import ws_manager
        ws_manager.queue_message(message_data)
    except Exception as e:
        jh.terminal_debug(f"WebSocket queue error: {e}")


def is_process_active(client_id: str) -> bool:
    """Check if a process is active via Redis or return False if Redis unavailable."""
    if jh.is_unit_testing():
        return False

    if sync_redis is None:
        return False
        
    try:
        return sync_redis.sismember(f"{ENV_VALUES['APP_PORT']}|active-processes", client_id)
    except Exception:
        return False

