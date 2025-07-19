from asgiref.sync import sync_to_async

from apps.chat.constants.redis_keys import TASK_LOCK_KEY
from apps.chat.services import AsyncRedisService
from apps.chat.tasks.send_random_chat_messages import send_random_messages


async def send_user_bots_messages(group: str):
    task_lock = await AsyncRedisService.set_if_not_exists(TASK_LOCK_KEY, "locked")
    if task_lock:
        await sync_to_async(send_random_messages.delay)(group)
