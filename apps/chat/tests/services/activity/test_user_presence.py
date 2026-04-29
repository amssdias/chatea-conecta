from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from apps.chat.constants.cache_expiration import ONLINE_USER_TTL
from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
    USER_ONLINE_KEY,
)
from apps.chat.services.activity import (
    cleanup_user_presence,
    is_user_online,
    mark_user_offline,
    mark_user_online,
    register_username_as_active,
)


class UserPresenceTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.activity.mark_user_offline", new_callable=AsyncMock)
    @patch("apps.chat.services.activity.AsyncRedisService.remove_username_from_set", new_callable=AsyncMock)
    async def test_cleanup_user_presence_removes_username_and_marks_user_offline(
            self,
            mock_remove_username_from_set,
            mock_mark_user_offline,
    ):
        username = "Andre"
        user_id = "10"

        await cleanup_user_presence(
            username=username,
            user_id=user_id,
        )

        mock_remove_username_from_set.assert_awaited_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "andre",
        )
        mock_mark_user_offline.assert_awaited_once_with("10")

    @patch("apps.chat.services.activity.AsyncRedisService.set_value", new_callable=AsyncMock)
    async def test_mark_user_online_sets_user_online_key_with_ttl(self, mock_set_value):
        user_id = "10"

        await mark_user_online(user_id)

        mock_set_value.assert_awaited_once_with(
            USER_ONLINE_KEY.format(user_id=user_id),
            "1",
            ex=ONLINE_USER_TTL,
        )

    @patch("apps.chat.services.activity.AsyncRedisService.delete_key", new_callable=AsyncMock)
    async def test_mark_user_offline_deletes_user_online_key(self, mock_delete_key):
        user_id = "10"

        await mark_user_offline(user_id)

        mock_delete_key.assert_awaited_once_with(
            USER_ONLINE_KEY.format(user_id=user_id),
        )

    @patch("apps.chat.services.activity.AsyncRedisService.get_value", new_callable=AsyncMock, )
    async def test_is_user_online_returns_true_when_online_key_exists(self, mock_get_value):
        user_id = "10"
        mock_get_value.return_value = "1"

        result = await is_user_online(user_id)

        self.assertTrue(result)
        mock_get_value.assert_awaited_once_with(
            USER_ONLINE_KEY.format(user_id=user_id),
        )

    @patch("apps.chat.services.activity.AsyncRedisService.get_value", new_callable=AsyncMock)
    async def test_is_user_online_returns_false_when_online_key_does_not_exist(self, mock_get_value):
        user_id = "10"
        mock_get_value.return_value = None

        result = await is_user_online(user_id)

        self.assertFalse(result)
        mock_get_value.assert_awaited_once_with(
            USER_ONLINE_KEY.format(user_id=user_id),
        )

    @patch("apps.chat.services.activity.AsyncRedisService.add_to_set", new_callable=AsyncMock, )
    async def test_register_username_as_active_adds_lowercase_username_to_active_usernames_set(self, mock_add_to_set):
        username = "Andre"

        await register_username_as_active(username)

        mock_add_to_set.assert_awaited_once_with(
            REDIS_ALL_USERNAMES_KEY,
            "andre",
        )
