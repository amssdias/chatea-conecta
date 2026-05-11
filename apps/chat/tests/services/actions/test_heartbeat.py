from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.services.actions.heartbeat import handle_heartbeat


class HandleHeartbeatTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.actions.heartbeat.mark_user_online", new_callable=AsyncMock)
    async def test_marks_current_user_online(self, mock_mark_user_online):
        consumer = Mock()
        consumer.id = "10"

        data = {
            "type": "heartbeat",
        }

        await handle_heartbeat(
            consumer=consumer,
            data=data,
        )

        mock_mark_user_online.assert_awaited_once_with(consumer.id)
