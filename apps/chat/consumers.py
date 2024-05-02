import json

from chat_connect.utils.redis_connection import redis_connection
from channels.generic.websocket import AsyncWebsocketConsumer


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("---- CONNECTED ----")
        print(f"scope: {self.scope}")
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name.lower()}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name, self.channel_name
        )

        # Increment Redis counter for the group
        group_key_counter = f"{self.room_group_name}_counter"
        await redis_connection.incrby(group_key_counter, amount=1)
        users_online = await redis_connection.get(group_key_counter)
        await self.accept()

        # Send the amount of users online on this chat
        await self.send(text_data=json.dumps({"users_online": users_online}))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

        redis_connection.decrby(f"{self.room_group_name}_counter", 1)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        username = self.scope["cookies"].get("username")
        if not username:
            await self.close(code=401, reason="No username")
            return

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat.message",
                "message": message,
                "username": username,
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        username = event["username"]

        # Send message to WebSocket (frontend)
        await self.send(text_data=json.dumps({"message": message, "username": username}))
