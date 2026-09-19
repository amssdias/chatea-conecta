from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.services.actions.heartbeat import handle_heartbeat


@patch(
    "apps.chat.services.actions.heartbeat.arefresh_guest_identity",
    new_callable=AsyncMock,
)
@patch("apps.chat.services.actions.heartbeat.mark_user_online", new_callable=AsyncMock)
class HandleHeartbeatTests(IsolatedAsyncioTestCase):
    @staticmethod
    def build_consumer(is_authenticated):
        consumer = Mock()
        consumer.id = "10"
        consumer.username = "testuser"
        consumer.user.is_authenticated = is_authenticated
        return consumer

    async def test_marks_current_user_online(self, mock_mark_user_online, mock_refresh):
        consumer = self.build_consumer(is_authenticated=True)

        data = {
            "type": "heartbeat",
        }

        await handle_heartbeat(
            consumer=consumer,
            data=data,
        )

        mock_mark_user_online.assert_awaited_once_with(consumer.id)

    async def test_extends_the_guest_identity_mapping(self, mock_mark_user_online, mock_refresh):
        consumer = self.build_consumer(is_authenticated=False)

        await handle_heartbeat(consumer=consumer, data={"type": "heartbeat"})

        mock_refresh.assert_awaited_once_with(consumer.username, consumer.id)

    async def test_does_not_touch_the_mapping_for_authenticated_users(
        self,
        mock_mark_user_online,
        mock_refresh,
    ):
        consumer = self.build_consumer(is_authenticated=True)

        await handle_heartbeat(consumer=consumer, data={"type": "heartbeat"})

        mock_refresh.assert_not_awaited()
