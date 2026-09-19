from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from django.core.cache import cache

from apps.chat.services.actions.send_message import handle_send_message
from apps.chat.websocket.exceptions import WebSocketValidationError


class HandleSendMessageTests(IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await cache.aclear()

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    @patch("apps.chat.services.actions.send_message.validate_group_payload")
    async def test_broadcasts_chat_message_when_group_is_valid(
            self,
            mock_validate_group_payload,
            mock_broadcast_chat_message,
    ):
        consumer = Mock()
        consumer.id = "user-1"

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

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    async def test_rejects_non_string_messages(self, mock_broadcast_chat_message):
        for invalid_message in (None, 123, ["hello"], {"text": "hello"}):
            with self.subTest(message=invalid_message):
                consumer = Mock()
                consumer.id = "user-1"
                consumer.groups = {"chatea"}
                consumer.send = AsyncMock()

                await handle_send_message(
                    consumer=consumer,
                    data={
                        "group": "chatea",
                        "message": invalid_message,
                    },
                )

                consumer.send.assert_awaited_once()

        mock_broadcast_chat_message.assert_not_awaited()

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    async def test_rejects_blank_messages(self, mock_broadcast_chat_message):
        consumer = Mock()
        consumer.id = "user-1"
        consumer.groups = {"chatea"}
        consumer.send = AsyncMock()

        await handle_send_message(
            consumer=consumer,
            data={
                "group": "chatea",
                "message": "   ",
            },
        )

        consumer.send.assert_awaited_once()
        mock_broadcast_chat_message.assert_not_awaited()

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    async def test_rejects_messages_longer_than_1000_characters(
            self,
            mock_broadcast_chat_message,
    ):
        consumer = Mock()
        consumer.id = "user-1"
        consumer.groups = {"chatea"}
        consumer.send = AsyncMock()

        await handle_send_message(
            consumer=consumer,
            data={
                "group": "chatea",
                "message": "x" * 1001,
            },
        )

        consumer.send.assert_awaited_once()
        mock_broadcast_chat_message.assert_not_awaited()

    @patch("apps.chat.services.actions.send_message.broadcast_chat_message", new_callable=AsyncMock)
    async def test_rate_limit_is_shared_by_connections_with_the_same_identity(
            self,
            mock_broadcast_chat_message,
    ):
        first_consumer = Mock()
        first_consumer.id = "same-user"
        first_consumer.groups = {"chatea"}
        first_consumer.close = AsyncMock()

        second_consumer = Mock()
        second_consumer.id = "same-user"
        second_consumer.groups = {"chatea"}
        second_consumer.close = AsyncMock()

        for index in range(4):
            await handle_send_message(
                consumer=first_consumer,
                data={
                    "group": "chatea",
                    "message": f"message {index}",
                },
            )

        for index in range(5):
            await handle_send_message(
                consumer=second_consumer,
                data={
                    "group": "chatea",
                    "message": f"message {index + 4}",
                },
            )

        self.assertEqual(mock_broadcast_chat_message.await_count, 8)
        first_consumer.close.assert_not_awaited()
        second_consumer.close.assert_awaited_once_with(
            code=4008,
            reason="Message rate limit exceeded",
        )
