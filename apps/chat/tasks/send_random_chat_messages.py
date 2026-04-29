import logging

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer

from apps.chat.services.activity import has_online_users
from apps.chat.services.message_service import MessageService

logger = logging.getLogger("chat_connect")


@shared_task(name="apps.chat.tasks.send_random_messages_tick")
def send_random_messages_tick(group: str):
    logger.info("Running 'send_random_messages_tick' for group: %s", group)

    if not has_online_users():
        logger.info("No online users found. Skipping bot message tick.")
        return

    service = MessageService()
    user_message = service.get_message_to_send()

    if not user_message:
        logger.warning(
            "No message available to send for group '%s'. Skipping tick.",
            group,
        )
        return

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        group,
        {
            "type": "chat.message",
            "message": user_message.get("message"),
            "username": user_message.get("username"),
            "group": group,
        },
    )

    logger.info("Bot message sent to group '%s'.", group)
