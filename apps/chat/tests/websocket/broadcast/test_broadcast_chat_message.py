from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from apps.chat.websocket.broadcast import broadcast_chat_message


class BroadcastChatMessageTests(IsolatedAsyncioTestCase):
    async def test_broadcasts_chat_message_to_group(self):
        consumer = Mock()
        consumer.id = "10"
        consumer.username = "Andre"
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        group = "main-room"
        message = "Hello world"

        await broadcast_chat_message(
            consumer=consumer,
            group=group,
            message=message,
        )

        consumer.channel_layer.group_send.assert_awaited_once_with(
            group,
            {
                "type": "chat.message",
                "message": message,
                "username": consumer.username,
                "user_id": consumer.id,
                "group": group,
            },
        )
