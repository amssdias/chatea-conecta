from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call, patch

from apps.chat.websocket.broadcast import broadcast_private_chat_user_offline


class BroadcastPrivateChatUserOfflineTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.websocket.broadcast.notify_user_offline", new_callable=AsyncMock)
    async def test_broadcasts_offline_event_to_all_private_chat_users(
            self,
            mock_notify_user_offline,
    ):
        consumer = Mock()
        consumer.id = 1
        consumer.channel_layer = Mock()
        consumer.private_chats = {
            10: 100,
            20: 200,
            30: 300,
        }

        await broadcast_private_chat_user_offline(consumer)

        self.assertEqual(mock_notify_user_offline.await_count, 3)

        mock_notify_user_offline.assert_has_awaits(
            [
                call(
                    channel_layer=consumer.channel_layer,
                    receiver_user_id=10,
                    offline_user_id=consumer.id,
                    chat_id=100,
                ),
                call(
                    channel_layer=consumer.channel_layer,
                    receiver_user_id=20,
                    offline_user_id=consumer.id,
                    chat_id=200,
                ),
                call(
                    channel_layer=consumer.channel_layer,
                    receiver_user_id=30,
                    offline_user_id=consumer.id,
                    chat_id=300,
                ),
            ],
            any_order=False,
        )

    @patch("apps.chat.websocket.broadcast.notify_user_offline", new_callable=AsyncMock)
    async def test_does_not_notify_anyone_when_user_has_no_private_chats(
            self,
            mock_notify_user_offline,
    ):
        consumer = Mock()
        consumer.id = 1
        consumer.channel_layer = Mock()
        consumer.private_chats = {}

        await broadcast_private_chat_user_offline(consumer)

        mock_notify_user_offline.assert_not_awaited()
