import logging
import random
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.chat.constants.redis_keys import HAS_USERS, TASK_LOCK_KEY
from apps.chat.services.message_service import MessageService
from apps.chat.services.redis_service import RedisService
from chat_connect.celery import app

logger = logging.getLogger("chat_connect")


@app.task
def send_random_messages(group):
    logger.info(f"Starting 'send_random_messages' task for group: {group}")

    service = MessageService()
    channel_layer = get_channel_layer()

    while RedisService.key_exists(HAS_USERS):

        user_message = service.get_message_to_send()

        if user_message:
            time.sleep(random.randint(1, 5))
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    "type": "chat.message",
                    "message": user_message.get("message"),
                    "username": user_message.get("username"),
                    "group": group,
                },
            )
        else:
            logger.warning(
                f"'send_random_messages' task for group '{group}' stopped because there are no more users or messages to send."
            )
            break

    logger.info(f"'send_random_messages' task for group '{group}' completed.")
    RedisService.delete_key(TASK_LOCK_KEY)
    return
