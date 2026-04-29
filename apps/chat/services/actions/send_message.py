from apps.chat.websocket.broadcast import broadcast_chat_message
from apps.chat.websocket.exceptions import WebSocketValidationError
from apps.chat.websocket.validation import validate_group_payload


async def handle_send_message(consumer, data):
    try:
        group = validate_group_payload(data)
    except WebSocketValidationError:
        await consumer.close(code=401, reason="No group")
        return None

    message = data.get("message")
    await broadcast_chat_message(consumer, group, message)
