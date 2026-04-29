from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.websocket.broadcast import notify_user_offline


class NotifyUserOfflineTests(IsolatedAsyncioTestCase):
    async def test_notifies_receiver_that_user_is_offline(self):
        channel_layer = Mock()
        channel_layer.group_send = AsyncMock()

        receiver_user_id = 10
        offline_user_id = 25
        chat_id = 99

        await notify_user_offline(
            channel_layer=channel_layer,
            receiver_user_id=receiver_user_id,
            offline_user_id=offline_user_id,
            chat_id=chat_id,
        )

        channel_layer.group_send.assert_awaited_once_with(
            USER_NOTIFICATION_GROUP.format(user_id=receiver_user_id),
            {
                "type": "user.offline",
                "user_id": offline_user_id,
                "chat_id": chat_id,
            },
        )
