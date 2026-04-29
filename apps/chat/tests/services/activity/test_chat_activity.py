from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
    REDIS_HAS_ACTIVE_USERS_KEY,
)
from apps.chat.services.activity import (
    get_online_users_count,
    update_chat_activity_status,
)


class ChatActivityTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.activity.AsyncRedisService.get_group_size", new_callable=AsyncMock)
    async def test_get_online_users_count_returns_active_usernames_group_size(
            self,
            mock_get_group_size,
    ):
        mock_get_group_size.return_value = 5

        result = await get_online_users_count()

        self.assertEqual(result, 5)
        mock_get_group_size.assert_awaited_once_with(REDIS_ALL_USERNAMES_KEY)

    @patch("apps.chat.services.activity.AsyncRedisService.delete_key", new_callable=AsyncMock)
    @patch("apps.chat.services.activity.AsyncRedisService.set_if_not_exists", new_callable=AsyncMock)
    @patch("apps.chat.services.activity.get_online_users_count", new_callable=AsyncMock)
    async def test_update_chat_activity_status_sets_active_users_key_when_users_are_online(
            self,
            mock_get_online_users_count,
            mock_set_if_not_exists,
            mock_delete_key,
    ):
        mock_get_online_users_count.return_value = 3

        await update_chat_activity_status()

        mock_get_online_users_count.assert_awaited_once_with()
        mock_set_if_not_exists.assert_awaited_once_with(
            REDIS_HAS_ACTIVE_USERS_KEY,
            "true",
        )
        mock_delete_key.assert_not_awaited()

    @patch("apps.chat.services.activity.AsyncRedisService.delete_key", new_callable=AsyncMock)
    @patch("apps.chat.services.activity.AsyncRedisService.set_if_not_exists", new_callable=AsyncMock)
    @patch("apps.chat.services.activity.get_online_users_count", new_callable=AsyncMock)
    async def test_update_chat_activity_status_deletes_active_users_key_when_no_users_are_online(
            self,
            mock_get_online_users_count,
            mock_set_if_not_exists,
            mock_delete_key,
    ):
        mock_get_online_users_count.return_value = 0

        await update_chat_activity_status()

        mock_get_online_users_count.assert_awaited_once_with()
        mock_delete_key.assert_awaited_once_with(REDIS_HAS_ACTIVE_USERS_KEY)
        mock_set_if_not_exists.assert_not_awaited()
