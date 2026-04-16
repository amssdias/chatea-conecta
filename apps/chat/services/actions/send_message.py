from apps.chat.websocket.validation import validate_group_payload


async def handle_send_message(consumer, data):
    group = validate_group_payload(data)
    if not group:
        await consumer.close(code=401, reason="No group")
        return None

    # Send regular messages to the corresponding group
    message = data.get("message")
    print("---------------------------------------")
    print("-------- Sending message...")
    print("---------------------------------------")

    # Send message to room group
    await consumer.channel_layer.group_send(
        group,
        {
            "type": "chat.message",
            "message": message,
            "username": consumer.username,
            "user_id": consumer.id,
            "group": group,
        },
    )
