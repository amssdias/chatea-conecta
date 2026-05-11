from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, call, patch

from apps.chat.constants.cache_expiration import PRIVATE_CHATS_TTL
from apps.chat.constants.redis_keys import USER_PRIVATE_CHATS_KEY
from apps.chat.services.private_chats import (
    restore_user_private_chat_groups,
    save_user_private_chat_group,
)


class PrivateChatsServiceTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.private_chats.AsyncRedisService.set_hash_value", new_callable=AsyncMock)
    async def test_save_user_private_chat_group_stores_private_group_with_ttl(self, mock_set_hash_value):
        user_id = "10"
        target_user_id = 20
        private_group = "private-chat-10-20"

        await save_user_private_chat_group(
            user_id=user_id,
            target_user_id=target_user_id,
            private_group=private_group,
        )

        mock_set_hash_value.assert_awaited_once_with(
            redis_key=USER_PRIVATE_CHATS_KEY.format(user_id=user_id),
            field=str(target_user_id),
            value=private_group,
            ex=PRIVATE_CHATS_TTL,
        )

    @patch("apps.chat.services.private_chats.AsyncRedisService.set_expiration", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.broadcast_private_chat_participant_online", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.register_user_to_group", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.send_private_chats_restored", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.AsyncRedisService.get_hash", new_callable=AsyncMock)
    async def test_restore_user_private_chat_groups_restores_chats_and_registers_groups(
            self,
            mock_get_hash,
            mock_send_private_chats_restored,
            mock_register_user_to_group,
            mock_broadcast_private_chat_participant_online,
            mock_set_expiration,
    ):
        consumer = Mock()
        consumer.id = "10"

        private_chats = {
            "20": "private-chat-10-20",
            "30": "private-chat-10-30",
        }

        redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=consumer.id)
        mock_get_hash.return_value = private_chats

        await restore_user_private_chat_groups(consumer)

        mock_get_hash.assert_awaited_once_with(redis_key)

        self.assertEqual(consumer.private_chats, private_chats)

        mock_send_private_chats_restored.assert_awaited_once_with(
            consumer=consumer,
            private_chats=private_chats,
        )

        mock_register_user_to_group.assert_has_awaits(
            [
                call(consumer, "private-chat-10-20"),
                call(consumer, "private-chat-10-30"),
            ]
        )

        mock_broadcast_private_chat_participant_online.assert_has_awaits(
            [
                call(
                    consumer=consumer,
                    private_group_id="private-chat-10-20",
                ),
                call(
                    consumer=consumer,
                    private_group_id="private-chat-10-30",
                ),
            ]
        )

        mock_set_expiration.assert_awaited_once_with(
            redis_key,
            PRIVATE_CHATS_TTL,
        )

    @patch("apps.chat.services.private_chats.AsyncRedisService.set_expiration", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.broadcast_private_chat_participant_online", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.register_user_to_group", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.send_private_chats_restored", new_callable=AsyncMock)
    @patch("apps.chat.services.private_chats.AsyncRedisService.get_hash", new_callable=AsyncMock)
    async def test_restore_user_private_chat_groups_does_nothing_when_no_private_chats_exist(
            self,
            mock_get_hash,
            mock_send_private_chats_restored,
            mock_register_user_to_group,
            mock_broadcast_private_chat_participant_online,
            mock_set_expiration,
    ):
        consumer = Mock()
        consumer.id = "10"

        redis_key = USER_PRIVATE_CHATS_KEY.format(user_id=consumer.id)
        mock_get_hash.return_value = {}

        await restore_user_private_chat_groups(consumer)

        mock_get_hash.assert_awaited_once_with(redis_key)
        mock_send_private_chats_restored.assert_not_awaited()
        mock_register_user_to_group.assert_not_awaited()
        mock_broadcast_private_chat_participant_online.assert_not_awaited()
        mock_set_expiration.assert_not_awaited()
