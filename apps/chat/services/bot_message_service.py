from asgiref.sync import sync_to_async

from apps.chat.constants.redis_keys import TASK_LOCK_KEY
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService
from apps.chat.tasks.send_random_chat_messages import send_random_messages


async def start_bot_messages_task(group: str):
    """
    Starts the bot messaging Celery task if it is not already running.

    A Redis lock is used to ensure that only one task is triggered at a time
    while real users are connected to the chat.
    """
    task_lock = await AsyncRedisService.set_if_not_exists(TASK_LOCK_KEY, "locked")
    if task_lock:
        await sync_to_async(send_random_messages.delay)(group)
