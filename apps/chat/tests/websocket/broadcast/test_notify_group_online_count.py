from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from apps.chat.websocket.broadcast import notify_group_online_count


class NotifyGroupOnlineCountTests(IsolatedAsyncioTestCase):
    async def test_sends_online_count_to_group(self):
        consumer = Mock()
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        group_name = "chat_room_1"
        online_count = 5

        await notify_group_online_count(
            consumer=consumer,
            group_name=group_name,
            online_count=online_count,
        )

        consumer.channel_layer.group_send.assert_awaited_once_with(
            group_name,
            {
                "type": "notify.users.count",
                "group_size": online_count,
            },
        )
