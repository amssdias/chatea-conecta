from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.constants.private_chat import FREE_PRIVATE_CHAT_LIMIT
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
    @patch("apps.chat.services.actions.private_invite.is_bot_user", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.user_has_pro_access", new_callable=AsyncMock)
    async def test_notifies_current_user_when_target_user_is_offline(
            self,
            mock_user_has_pro_access,
            mock_is_user_online,
            mock_get_private_group_name,
            mock_is_bot_user,
            mock_notify_user_offline,
    ):
        target_user_id = "20"
        private_group_id = "private-chat-10-20"
        authenticated_user = Mock()

        consumer = Mock()
        consumer.id = "10"
        consumer.user = authenticated_user
        consumer.channel_layer = Mock()
        consumer.private_chats = {}

        data = {
            "target_user_id": target_user_id,
        }

        mock_user_has_pro_access.return_value = False
        mock_is_user_online.return_value = False
        mock_is_bot_user.return_value = False
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_user_has_pro_access.assert_awaited_once_with(authenticated_user)
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

    @patch(
        "apps.chat.services.actions.private_invite.save_user_private_chat_group",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.register_user_to_group",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.is_bot_user", new_callable=AsyncMock
    )
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch(
        "apps.chat.services.actions.private_invite.is_user_online",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.user_has_pro_access",
        new_callable=AsyncMock,
    )
    async def test_registers_saves_and_sends_invite_when_target_user_is_online(
        self,
        mock_user_has_pro_access,
        mock_is_user_online,
        mock_get_private_group_name,
        mock_is_bot_user,
        mock_register_user_to_group,
        mock_save_user_private_chat_group,
    ):
        target_user_id = "20"
        private_group_id = "private-chat-10-20"
        authenticated_user = Mock()

        consumer = Mock()
        consumer.id = "10"
        consumer.user = authenticated_user
        consumer.private_chats = {}
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        data = {
            "target_user_id": target_user_id,
        }

        mock_user_has_pro_access.return_value = False
        mock_is_user_online.return_value = True
        mock_is_bot_user.return_value = False
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_user_has_pro_access.assert_awaited_once_with(
            authenticated_user,
        )
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

    @patch(
        "apps.chat.services.actions.private_invite.send_private_chat_access_denied",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.user_has_pro_access",
        new_callable=AsyncMock,
    )
    async def test_pro_access_uses_authenticated_user_not_cookie_user_id(
        self,
        mock_user_has_pro_access,
        mock_send_access_denied,
    ):
        authenticated_user = SimpleNamespace(
            pk=10,
            is_authenticated=True,
        )

        consumer = Mock()
        consumer.user = authenticated_user

        # Simulates an attacker-controlled cookie value.
        consumer.id = "999"

        consumer.private_chats = {
            str(index): f"private-chat-{index}"
            for index in range(FREE_PRIVATE_CHAT_LIMIT)
        }

        mock_user_has_pro_access.return_value = False

        await handle_private_invite(
            consumer,
            {"target_user_id": "20"},
        )

        mock_user_has_pro_access.assert_awaited_once_with(
            authenticated_user,
        )
        mock_send_access_denied.assert_awaited_once()
