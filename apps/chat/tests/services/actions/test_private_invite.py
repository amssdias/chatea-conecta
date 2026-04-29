from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP
from apps.chat.services.actions.private_invite import handle_private_invite


class HandlePrivateInviteTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    async def test_does_nothing_when_private_chat_already_exists(
            self,
            mock_get_private_group_name,
            mock_is_user_online,
    ):
        target_user_id = "20"

        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {
            target_user_id: "private-chat-10-20",
        }

        data = {
            "target_user_id": target_user_id,
        }

        await handle_private_invite(consumer, data)

        mock_is_user_online.assert_not_awaited()
        mock_get_private_group_name.assert_not_called()

    @patch("apps.chat.services.actions.private_invite.notify_user_offline", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    async def test_notifies_current_user_when_target_user_is_offline(
            self,
            mock_is_user_online,
            mock_get_private_group_name,
            mock_notify_user_offline,
    ):
        target_user_id = "20"
        private_group_id = "private-chat-10-20"

        consumer = Mock()
        consumer.id = "10"
        consumer.channel_layer = Mock()
        consumer.private_chats = {}

        data = {
            "target_user_id": target_user_id,
        }

        mock_is_user_online.return_value = False
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_is_user_online.assert_awaited_once_with(target_user_id)
        mock_get_private_group_name.assert_called_once_with(
            consumer.id,
            target_user_id,
        )
        mock_notify_user_offline.assert_awaited_once_with(
            channel_layer=consumer.channel_layer,
            receiver_user_id=consumer.id,
            offline_user_id=target_user_id,
            chat_id=private_group_id,
        )

    @patch("apps.chat.services.actions.private_invite.save_user_private_chat_group", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.register_user_to_group", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    async def test_registers_saves_and_sends_invite_when_target_user_is_online(
            self,
            mock_is_user_online,
            mock_get_private_group_name,
            mock_register_user_to_group,
            mock_save_user_private_chat_group,
    ):
        target_user_id = "20"
        private_group_id = "private-chat-10-20"

        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {}
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        data = {
            "target_user_id": target_user_id,
        }

        mock_is_user_online.return_value = True
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_is_user_online.assert_awaited_once_with(target_user_id)
        mock_get_private_group_name.assert_called_once_with(
            consumer.id,
            target_user_id,
        )

        mock_register_user_to_group.assert_awaited_once_with(
            consumer,
            private_group_id,
        )

        mock_save_user_private_chat_group.assert_awaited_once_with(
            consumer.id,
            target_user_id,
            private_group_id,
        )

        self.assertEqual(
            consumer.private_chats,
            {
                target_user_id: private_group_id,
            },
        )

        consumer.channel_layer.group_send.assert_awaited_once_with(
            USER_NOTIFICATION_GROUP.format(user_id=target_user_id),
            {
                "type": "chat.invite",
                "from_user_id": consumer.id,
                "private_group": private_group_id,
            },
        )
