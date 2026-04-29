from apps.chat.services.activity import get_online_users_count

from apps.chat.websocket.broadcast import notify_group_online_count
from apps.chat.websocket.exceptions import WebSocketValidationError
from apps.chat.websocket.registration import (
    register_user_to_group,
    register_user_to_group_notification,
)
from apps.chat.websocket.validation import validate_group_payload


async def handle_register_group(consumer, data):
    try:
        group = validate_group_payload(data)
    except WebSocketValidationError:
        await consumer.close(code=4001, reason="Invalid group")
        return

    await register_user_to_group(consumer, group)
    await register_user_to_group_notification(consumer, consumer.id)

    online_count = (await get_online_users_count()) + 60
    await notify_group_online_count(consumer, group_name=group, online_count=online_count)
    return None
