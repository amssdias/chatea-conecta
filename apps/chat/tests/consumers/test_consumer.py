import json

from channels.testing import WebsocketCommunicator
from django.test import TestCase

from apps.chat.consumers import ChatConsumer


class TestConsumerChat(TestCase):

    async def _test_connection(self):
        self.communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "ws/chat/")
        connected, _ = await self.communicator.connect()
        response = await self.communicator.receive_nothing()
        self.assertTrue(response)
        await self.communicator.disconnect()

    async def _test_receive_message_no_group(self):
        self.communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "ws/chat/")
        connected, _ = await self.communicator.connect()
        await self.communicator.send_to(json.dumps({"group": ""}))

        response = await self.communicator.receive_output()
        self.assertEqual(response.get("code"), 401)
        self.assertEqual(response.get("reason").lower(), "no group")

        await self.communicator.disconnect()

    async def _test_receive_message_join_room_group(self):
        self.communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "ws/chat/")
        connected, _ = await self.communicator.connect()
        await self.communicator.send_to(
            json.dumps(
                {
                    "group": "group1",
                    "registerGroup": "true"
                }
            )
        )

        response = await self.communicator.receive_output()
        print("RESPONSE")
        await self.communicator.disconnect()
