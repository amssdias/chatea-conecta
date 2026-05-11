import logging
import random

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from apps.chat.services.activity import has_online_users
from apps.chat.services.bots.bot_message_service import BotMessageService

logger = logging.getLogger("chat_connect")

BOT_MESSAGE_SEND_PROBABILITY = 0.9


@shared_task(name="apps.chat.tasks.send_random_messages_tick")
def send_random_messages_tick(group: str) -> None:
    """
    Send one random bot message to the chat group if there are online users.

    This task is triggered periodically by Celery Beat. It intentionally sends
    messages frequently to make the chat feel active, while occasionally
    skipping ticks to avoid a perfectly mechanical rhythm.
    """
    if not has_online_users():
        return

    if random.random() > BOT_MESSAGE_SEND_PROBABILITY:
        return

    service = BotMessageService()
    user_message = service.get_message_to_send()

    if not user_message:
        return

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "chat.message",
            "message": user_message.get("message"),
            "user_id": user_message.get("user_id"),
            "username": user_message.get("username"),
            "group": group,
        },
    )
