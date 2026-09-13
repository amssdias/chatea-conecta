from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.services.actions.close_private_chat import handle_close_private_chat


class HandleClosePrivateChatTests(IsolatedAsyncioTestCase):
    @patch(
        "apps.chat.services.actions.close_private_chat.remove_user_private_chat_group",
        new_callable=AsyncMock,
    )
    async def test_marks_the_chat_closed_and_forgets_it_in_redis(
        self,
        mock_remove_user_private_chat_group,
    ):
        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {"20": "private-chat-10-20"}
        consumer.closed_private_chats = set()

        await handle_close_private_chat(consumer, {"target_user_id": "20"})

        self.assertEqual(consumer.closed_private_chats, {"20"})

        mock_remove_user_private_chat_group.assert_awaited_once_with(
            consumer.id,
            "20",
        )

    @patch(
        "apps.chat.services.actions.close_private_chat.remove_user_private_chat_group",
        new_callable=AsyncMock,
    )
    async def test_keeps_the_user_reachable_in_the_private_group(
        self,
        mock_remove_user_private_chat_group,
    ):
        """
        Closing must not unsubscribe: the other participant is not told, so
        their next message would be delivered to nobody and still look sent on
        their side. The entry also stays in private_chats, otherwise they would
        never be told when this user actually goes offline.
        """
        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {"20": "private-chat-10-20"}
        consumer.closed_private_chats = set()

        await handle_close_private_chat(consumer, {"target_user_id": "20"})

        consumer.channel_layer.group_discard.assert_not_called()
        self.assertEqual(consumer.private_chats, {"20": "private-chat-10-20"})

    @patch(
        "apps.chat.services.actions.close_private_chat.remove_user_private_chat_group",
        new_callable=AsyncMock,
    )
    async def test_ignores_a_chat_the_user_does_not_have(
        self,
        mock_remove_user_private_chat_group,
    ):
        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {}
        consumer.closed_private_chats = set()

        await handle_close_private_chat(consumer, {"target_user_id": "20"})

        self.assertEqual(consumer.closed_private_chats, set())
        mock_remove_user_private_chat_group.assert_not_awaited()

    @patch(
        "apps.chat.services.actions.close_private_chat.remove_user_private_chat_group",
        new_callable=AsyncMock,
    )
    async def test_ignores_a_payload_without_a_target(
        self,
        mock_remove_user_private_chat_group,
    ):
        consumer = Mock()
        consumer.id = "10"
        consumer.private_chats = {"20": "private-chat-10-20"}
        consumer.closed_private_chats = set()

        await handle_close_private_chat(consumer, {})

        self.assertEqual(consumer.closed_private_chats, set())
        mock_remove_user_private_chat_group.assert_not_awaited()
