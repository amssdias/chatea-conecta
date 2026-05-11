from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.services.actions.send_message import handle_send_message
from apps.chat.websocket.exceptions import WebSocketValidationError


class HandleSendMessageTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.send_message.validate_group_payload")
    async def test_broadcasts_chat_message_when_group_is_valid(
            self,
            mock_validate_group_payload,
            mock_broadcast_chat_message,
    ):
        consumer = Mock()

        data = {
            "group": "main-room",
            "message": "Hello world",
        }

        group = "main-room"
        mock_validate_group_payload.return_value = group

        await handle_send_message(
            consumer=consumer,
            data=data,
        )

        mock_validate_group_payload.assert_called_once_with(data)

        mock_broadcast_chat_message.assert_awaited_once_with(
            consumer,
            group,
            "Hello world",
        )

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.send_message.validate_group_payload")
    async def test_closes_connection_when_group_payload_is_invalid(
            self,
            mock_validate_group_payload,
            mock_broadcast_chat_message,
    ):
        consumer = Mock()
        consumer.close = AsyncMock()

        data = {
            "group": "",
            "message": "Hello world",
        }

        mock_validate_group_payload.side_effect = WebSocketValidationError(
            "Missing group"
        )

        result = await handle_send_message(
            consumer=consumer,
            data=data,
        )

        self.assertIsNone(result)

        mock_validate_group_payload.assert_called_once_with(data)

        consumer.close.assert_awaited_once_with(
            code=401,
            reason="No group",
        )

        mock_broadcast_chat_message.assert_not_awaited()
