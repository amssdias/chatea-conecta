from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.websocket.registration import (
    register_user_to_group,
    register_user_to_group_notification,
)


class RegisterUserToGroupTests(IsolatedAsyncioTestCase):
    async def test_register_user_to_group_adds_user_when_group_is_not_registered(self):
        consumer = Mock()
        consumer.channel_name = "specific-channel-name"
        consumer.groups = set()
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_add = AsyncMock()

        group_name = "chat-room-1"

        await register_user_to_group(
            consumer=consumer,
            group_name=group_name,
        )

        consumer.channel_layer.group_add.assert_awaited_once_with(
            group_name,
            consumer.channel_name,
        )
        self.assertIn(group_name, consumer.groups)

    async def test_register_user_to_group_does_not_add_user_when_group_is_already_registered(self):
        group_name = "chat-room-1"

        consumer = Mock()
        consumer.channel_name = "specific-channel-name"
        consumer.groups = {group_name}
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_add = AsyncMock()

        await register_user_to_group(
            consumer=consumer,
            group_name=group_name,
        )

        consumer.channel_layer.group_add.assert_not_awaited()
        self.assertEqual(consumer.groups, {group_name})

    @patch(
        "apps.chat.websocket.registration.register_user_to_group",
        new_callable=AsyncMock,
    )
    async def test_register_user_to_group_notification_registers_user_notification_group(
            self,
            mock_register_user_to_group,
    ):
        consumer = Mock()
        user_id = "10"

        await register_user_to_group_notification(
            consumer=consumer,
            user_id=user_id,
        )

        mock_register_user_to_group.assert_awaited_once_with(
            consumer,
            USER_NOTIFICATION_GROUP.format(user_id=user_id),
        )
