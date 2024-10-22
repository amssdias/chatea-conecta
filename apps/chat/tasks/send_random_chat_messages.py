import logging
import random
import time

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.chat.constants.redis_keys import HAS_USERS, TASK_LOCK_KEY
from apps.chat.services import MessageService, RedisService
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
            time.sleep(random.randint(1, 3))
            async_to_sync(channel_layer.group_send)(
                group,
                {
                    "type": "chat.message",
                    "message": user_message.get("message"),
                    "username": user_message.get("username"),
                    "group": group,
                },
            )
            logger.info(
                f"Sent message from user '{user_message.get('username')}' to group '{group}'."
            )

    RedisService.delete_key(TASK_LOCK_KEY)
    logger.info(f"'send_random_messages' task for group '{group}' completed.")
    return
