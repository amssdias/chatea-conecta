from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from apps.chat.constants.redis_keys import (
    REDIS_ALL_USERNAMES_KEY,
)
from apps.chat.services.activity import (
    get_online_users_count,
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
