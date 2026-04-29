import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock

from apps.chat.constants.consumer import PRIVATE_CHATS_RESTORED
from apps.chat.websocket.broadcast import send_private_chats_restored


class SendPrivateChatsRestoredTests(IsolatedAsyncioTestCase):
    async def test_sends_restored_private_chats_to_current_connection(self):
        consumer = Mock()
        consumer.send = AsyncMock()

        private_chats = {
            "10": 100,
            "20": 200,
        }

        await send_private_chats_restored(
            consumer=consumer,
            private_chats=private_chats,
        )

        consumer.send.assert_awaited_once()

        call_kwargs = consumer.send.await_args.kwargs
        payload = json.loads(call_kwargs["text_data"])

        self.assertEqual(
            payload,
            {
                "type": PRIVATE_CHATS_RESTORED,
                "privateChats": private_chats,
            },
        )
