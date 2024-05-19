import json

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY, REDIS_GROUPS_KEY
from chat_connect.utils.aio_redis_connection import aio_redis_connection
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("---- CONNECTED ----")
        self.groups = set()
        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    async def receive(self, text_data):
        # Send message that user should be registered in a group
        data = json.loads(text_data)

        # Join room group
        group = data.get("registerGroup", "").lower()
        if group and group not in self.groups:
            await self.channel_layer.group_add(
                group, self.channel_name
            )
            self.groups.add(group)
            users_online = await self.get_group_size(group)
            await self.send(text_data=json.dumps({"users_online": users_online}))
            return

        # Send regular messages to the corresponding group
        group = data.get("group").lower()
        message = data.get("message")

        username = self.scope["cookies"].get("username").lower()
        if not username:
            await self.close(code=401, reason="No username")
            return

        # Send message to room group
        await self.channel_layer.group_send(
            group,
            {
                "type": "chat.message",
                "message": message,
                "username": username,
                "group": group,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]
        group = event["group"]

        # Send message to WebSocket (frontend)
        await self.send(text_data=json.dumps(
                {
                    "message": message, 
                    "username": username,
                    "groupChatName": group,
                }
            )
        )

    async def get_group_size(self, group_name):
        group_key = f"{REDIS_GROUPS_KEY}:{group_name}"
        group_size = await aio_redis_connection.zcard(group_key)
        return group_size
