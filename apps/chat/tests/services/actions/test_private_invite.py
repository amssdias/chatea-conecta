from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.constants.private_chat import (
    FREE_PRIVATE_CHAT_LIMIT,
    PRIVATE_CHAT_ACCESS_FREE,
)
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
        consumer.closed_private_chats = set()

        data = {
            "target_user_id": target_user_id,
        }

        await handle_private_invite(consumer, data)

        mock_is_user_online.assert_not_awaited()
        mock_get_private_group_name.assert_not_called()

    @patch(
        "apps.chat.services.actions.private_invite.broadcast_private_chat_participant_online",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.save_user_private_chat_group",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.register_user_to_group",
        new_callable=AsyncMock,
    )
    @patch("apps.chat.services.actions.private_invite.is_bot_user", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    @patch(
        "apps.chat.services.actions.private_invite.resolve_private_chat_access",
        new_callable=AsyncMock,
    )
    async def test_reopening_a_closed_chat_reuses_its_original_group(
        self,
        mock_resolve_private_chat_access,
        mock_is_user_online,
        mock_get_private_group_name,
        mock_is_bot_user,
        mock_register_user_to_group,
        mock_save_user_private_chat_group,
        mock_broadcast_participant_online,
    ):
        """
        The stored name may have been built from the other id, so recomputing
        it here would open a second group nobody else is in.
        """
        target_user_id = "20"
        original_group_id = "private-chat-20-10"

        consumer = Mock()
        consumer.id = "10"
        consumer.user = Mock()
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()
        consumer.private_chats = {target_user_id: original_group_id}
        consumer.closed_private_chats = {target_user_id}

        mock_resolve_private_chat_access.return_value = PRIVATE_CHAT_ACCESS_FREE
        mock_is_user_online.return_value = True
        mock_is_bot_user.return_value = False

        await handle_private_invite(consumer, {"target_user_id": target_user_id})

        mock_get_private_group_name.assert_not_called()

        mock_register_user_to_group.assert_awaited_once_with(
            consumer,
            original_group_id,
        )

        self.assertEqual(consumer.closed_private_chats, set())
        self.assertEqual(consumer.private_chats, {target_user_id: original_group_id})

    @patch("apps.chat.services.actions.private_invite.notify_user_offline", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.is_bot_user", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    @patch(
        "apps.chat.services.actions.private_invite.resolve_private_chat_access",
        new_callable=AsyncMock,
    )
    async def test_notifies_current_user_when_target_user_is_offline(
            self,
            mock_resolve_private_chat_access,
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
        consumer.closed_private_chats = set()

        data = {
            "target_user_id": target_user_id,
        }

        mock_resolve_private_chat_access.return_value = PRIVATE_CHAT_ACCESS_FREE
        mock_is_user_online.return_value = False
        mock_is_bot_user.return_value = False
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_resolve_private_chat_access.assert_awaited_once_with(authenticated_user)
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
        "apps.chat.services.actions.private_invite.broadcast_private_chat_participant_online",
        new_callable=AsyncMock,
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
        "apps.chat.services.actions.private_invite.resolve_private_chat_access",
        new_callable=AsyncMock,
    )
    async def test_registers_saves_and_sends_invite_when_target_user_is_online(
        self,
        mock_resolve_private_chat_access,
        mock_is_user_online,
        mock_get_private_group_name,
        mock_is_bot_user,
        mock_register_user_to_group,
        mock_save_user_private_chat_group,
        mock_broadcast_participant_online,
    ):
        target_user_id = "20"
        private_group_id = "private-chat-10-20"
        authenticated_user = Mock()

        consumer = Mock()
        consumer.id = "10"
        consumer.user = authenticated_user
        consumer.private_chats = {}
        consumer.closed_private_chats = set()
        consumer.channel_layer = Mock()
        consumer.channel_layer.group_send = AsyncMock()

        data = {
            "target_user_id": target_user_id,
        }

        mock_resolve_private_chat_access.return_value = PRIVATE_CHAT_ACCESS_FREE
        mock_is_user_online.return_value = True
        mock_is_bot_user.return_value = False
        mock_get_private_group_name.return_value = private_group_id

        await handle_private_invite(consumer, data)

        mock_resolve_private_chat_access.assert_awaited_once_with(
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

        # Without this the other side stays greyed out from an earlier
        # disconnect: it can read the conversation but never reply.
        mock_broadcast_participant_online.assert_awaited_once_with(
            consumer=consumer,
            private_group_id=private_group_id,
        )

    @patch(
        "apps.chat.services.actions.private_invite.send_private_chat_access_denied",
        new_callable=AsyncMock,
    )
    @patch(
        "apps.chat.services.actions.private_invite.resolve_private_chat_access",
        new_callable=AsyncMock,
    )
    async def test_pro_access_uses_authenticated_user_not_cookie_user_id(
        self,
        mock_resolve_private_chat_access,
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
        consumer.closed_private_chats = set()

        mock_resolve_private_chat_access.return_value = PRIVATE_CHAT_ACCESS_FREE

        await handle_private_invite(
            consumer,
            {"target_user_id": "20"},
        )

        mock_resolve_private_chat_access.assert_awaited_once_with(
            authenticated_user,
        )
        mock_send_access_denied.assert_awaited_once()

    @patch(
        "apps.chat.services.actions.private_invite.send_private_chat_access_denied",
        new_callable=AsyncMock,
    )
    @patch("apps.chat.services.actions.private_invite.notify_user_offline", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.is_bot_user", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.private_invite.get_private_group_name")
    @patch("apps.chat.services.actions.private_invite.is_user_online", new_callable=AsyncMock)
    @patch(
        "apps.chat.services.actions.private_invite.resolve_private_chat_access",
        new_callable=AsyncMock,
    )
    async def test_closed_chats_do_not_count_towards_the_ceiling(
        self,
        mock_resolve_private_chat_access,
        mock_is_user_online,
        mock_get_private_group_name,
        mock_is_bot_user,
        mock_notify_user_offline,
        mock_send_access_denied,
    ):
        """
        The original bug: closing a chat only cleared it from the rail, so the
        ledger still held it and the next invite was refused.
        """
        consumer = Mock()
        consumer.id = "10"
        consumer.user = Mock()
        consumer.private_chats = {
            str(index): f"private-chat-{index}"
            for index in range(FREE_PRIVATE_CHAT_LIMIT)
        }
        consumer.closed_private_chats = {"0"}

        mock_resolve_private_chat_access.return_value = PRIVATE_CHAT_ACCESS_FREE
        mock_is_user_online.return_value = False
        mock_is_bot_user.return_value = False

        await handle_private_invite(consumer, {"target_user_id": "20"})

        mock_send_access_denied.assert_not_awaited()
