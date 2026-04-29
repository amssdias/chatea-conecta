from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from apps.chat.websocket.broadcast import broadcast_private_chat_participant_online


class BroadcastPrivateChatParticipantOnlineTests(IsolatedAsyncioTestCase):
    async def test_broadcasts_private_chat_participant_online_event(self):
        consumer = Mock()
        consumer.id = 1
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        private_group_id = "private_chat_123"

        await broadcast_private_chat_participant_online(
            consumer=consumer,
            private_group_id=private_group_id,
        )

        consumer.channel_layer.group_send.assert_awaited_once_with(
            private_group_id,
            {
                "type": "private.chat.participant.online",
                "user_id": consumer.id,
                "private_group_id": private_group_id,
            },
        )
