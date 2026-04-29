from apps.chat.websocket.validation import validate_group_payload


async def handle_send_message(consumer, data):
    group = validate_group_payload(data)
    if not group:
        await consumer.close(code=401, reason="No group")
        return None

    message = data.get("message")
    await broadcast_chat_message(consumer, group, message)
