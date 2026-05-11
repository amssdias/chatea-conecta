from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.services.actions.register_group import handle_register_group
from apps.chat.websocket.exceptions import WebSocketValidationError


class HandleRegisterGroupTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.actions.register_group.notify_group_online_count", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.get_online_users_count", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.register_user_to_group_notification", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.register_user_to_group", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.validate_group_payload")
    async def test_registers_group_and_starts_bot_messages(
            self,
            mock_validate_group_payload,
            mock_register_user_to_group,
            mock_register_user_to_group_notification,
            mock_get_online_users_count,
            mock_notify_group_online_count,
    ):
        consumer = Mock()
        consumer.id = "10"

        data = {
            "group": "main-room",
        }

        group = "main-room"
        mock_validate_group_payload.return_value = group
        mock_get_online_users_count.return_value = 5

        result = await handle_register_group(
            consumer=consumer,
            data=data,
        )

        self.assertIsNone(result)

        mock_validate_group_payload.assert_called_once_with(data)

        mock_register_user_to_group.assert_awaited_once_with(
            consumer,
            group,
        )

        mock_register_user_to_group_notification.assert_awaited_once_with(
            consumer,
            consumer.id,
        )

        mock_get_online_users_count.assert_awaited_once_with()

        mock_notify_group_online_count.assert_awaited_once_with(
            consumer,
            group_name=group,
            online_count=65,
        )


    @patch("apps.chat.services.actions.register_group.notify_group_online_count", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.get_online_users_count", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.register_user_to_group_notification", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.register_user_to_group", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.register_group.validate_group_payload")
    async def test_closes_connection_when_group_payload_is_invalid(
            self,
            mock_validate_group_payload,
            mock_register_user_to_group,
            mock_register_user_to_group_notification,
            mock_get_online_users_count,
            mock_notify_group_online_count,
    ):
        consumer = Mock()
        consumer.id = "10"
        consumer.close = AsyncMock()

        data = {
            "group": "",
        }

        mock_validate_group_payload.side_effect = WebSocketValidationError(
            "Invalid group"
        )

        result = await handle_register_group(
            consumer=consumer,
            data=data,
        )

        self.assertIsNone(result)

        mock_validate_group_payload.assert_called_once_with(data)

        consumer.close.assert_awaited_once_with(
            code=4001,
            reason="Invalid group",
        )

        mock_register_user_to_group.assert_not_awaited()
        mock_register_user_to_group_notification.assert_not_awaited()
        mock_get_online_users_count.assert_not_awaited()
        mock_notify_group_online_count.assert_not_awaited()
