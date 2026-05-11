import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from apps.chat.constants.consumer import ERROR_ACTION
from apps.chat.websocket.dispatch import dispatch_action


class DispatchActionTests(IsolatedAsyncioTestCase):
    @patch("apps.chat.websocket.dispatch.ACTION_MAP")
    async def test_dispatch_action_calls_matching_handler(self, mock_action_map):
        consumer = Mock()
        handler = AsyncMock()

        action = "test.action"
        content = {
            "type": action,
            "message": "Hello",
        }

        mock_action_map.get.return_value = handler

        await dispatch_action(
            consumer=consumer,
            content=content,
        )

        mock_action_map.get.assert_called_once_with(action)
        handler.assert_awaited_once_with(consumer, content)

    @patch("apps.chat.websocket.dispatch.logger")
    @patch("apps.chat.websocket.dispatch.ACTION_MAP")
    async def test_dispatch_action_sends_error_when_action_is_unknown(
            self,
            mock_action_map,
            mock_logger,
    ):
        consumer = Mock()
        consumer.send = AsyncMock()

        content = {
            "type": "unknown.action",
            "message": "Hello",
        }

        mock_action_map.get.return_value = None

        await dispatch_action(
            consumer=consumer,
            content=content,
        )

        mock_action_map.get.assert_called_once_with("unknown.action")

        mock_logger.warning.assert_called_once_with(
            "Unknown websocket action received",
            extra={
                "action": "unknown.action",
                "content": content,
            },
        )

        consumer.send.assert_awaited_once()

        payload = json.loads(consumer.send.await_args.kwargs["text_data"])

        self.assertEqual(
            payload,
            {
                "type": ERROR_ACTION,
                "error": "Invalid action",
            },
        )

    @patch("apps.chat.websocket.dispatch.logger")
    @patch("apps.chat.websocket.dispatch.ACTION_MAP")
    async def test_dispatch_action_sends_error_when_type_is_missing(
            self,
            mock_action_map,
            mock_logger,
    ):
        consumer = Mock()
        consumer.send = AsyncMock()

        content = {
            "message": "Hello",
        }

        mock_action_map.get.return_value = None

        await dispatch_action(
            consumer=consumer,
            content=content,
        )

        mock_action_map.get.assert_called_once_with(None)

        mock_logger.warning.assert_called_once_with(
            "Unknown websocket action received",
            extra={
                "action": None,
                "content": content,
            },
        )

        consumer.send.assert_awaited_once()

        payload = json.loads(consumer.send.await_args.kwargs["text_data"])

        self.assertEqual(
            payload,
            {
                "type": ERROR_ACTION,
                "error": "Invalid action",
            },
        )
