import json
import logging

from apps.chat.constants.consumer import PRIVATE_INVITE, REGISTER_GROUP, SEND_MESSAGE, ERROR_ACTION
from apps.chat.services.actions.private_invite import handle_private_invite
from apps.chat.services.actions.register_group import handle_register_group
from apps.chat.services.actions.send_message import handle_send_message

logger = logging.getLogger("chat_connect")

ACTION_MAP = {
    REGISTER_GROUP: handle_register_group,
    PRIVATE_INVITE: handle_private_invite,
    SEND_MESSAGE: handle_send_message,
}


async def dispatch_action(consumer, content):
    action = content.get("type")
    handler = ACTION_MAP.get(action)

    if not handler:
        logger.warning(
            "Unknown websocket action received",
            extra={
                "action": action,
                "content": content,
            },
        )
        await consumer.send(
            text_data=json.dumps(
                {
                    "type": ERROR_ACTION,
                    "error": "Invalid action",
                }
            )
        )
        return

    await handler(consumer, content)
