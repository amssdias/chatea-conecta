import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY, TASK_LOCK_KEY, HAS_USERS
from apps.chat.tasks.send_random_chat_messages import send_random_messages
from chat_connect.utils.aio_redis_connection import aio_redis_connection


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        print("---- CONNECTED ----")
        self.groups = set()
        await self.accept()

    async def disconnect(self, close_code):
        await self.remove_user()
        await self.unregister_user_from_group()

        group_size = await self.get_group_size()
        if not group_size:
            await sync_to_async(cache.delete)(HAS_USERS)

    async def remove_user(self):
        username = self.scope.get("cookies", {}).get("username", "").lower()
        await aio_redis_connection.srem(REDIS_USERNAME_KEY, username)

    async def unregister_user_from_group(self):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)

        self.groups.clear()

    async def receive(self, text_data):
        """
        text_data: ARGS:
            group: str
            registerGroup: bool
            message: str
        """

        username = self.scope["cookies"].get("username", "")
        lower_username = username.lower()
        is_connected = await aio_redis_connection.sismember(
            REDIS_USERNAME_KEY, lower_username
        )
        if not username or not is_connected:
            await self.close(code=4001, reason="No username")
            return

        # Send message that user should be registered in a group
        data = json.loads(text_data)
        group = data.get("group", "").lower()
        if not group:
            await self.close(code=401, reason="No group")
            return None

        # Join room group
        register_group = data.get("registerGroup", False)
        if register_group and group not in self.groups:
            await self.register_user_to_room_group(group)
            await self.send_user_bots_messages(group)
            return None

        # TODO: Leave group room
        unregister_group = data.get("unregisterGroup", False)
        if unregister_group and group in self.groups:
            # Unregister group
            pass

        # Send regular messages to the corresponding group
        message = data.get("message")

        # Send message to room group
        await self.channel_layer.group_send(
            group,
            {
                "type": "chat.message",
                "message": message,
                "username": username,
                "group": group,
            },
        )

    async def register_user_to_room_group(self, group: str):
        await self.channel_layer.group_add(group, self.channel_name)
        self.groups.add(group)
        group_size = await self.get_group_size()

        # If there are users we make sure the key is true to keep sending user msgs
        if group_size:
            await sync_to_async(cache.set)(HAS_USERS, True)

        await self.send(text_data=json.dumps({"users_online": group_size}))

    async def send_user_bots_messages(self, group: str):
        task_lock = await aio_redis_connection.setnx(TASK_LOCK_KEY, "locked")
        if task_lock:
            await sync_to_async(send_random_messages.delay)(group)

    async def chat_message(self, event):
        """Receive message from room group"""
        message = event["message"]
        username = event["username"]
        group = event["group"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "username": username,
                    "groupChatName": group,
                }
            )
        )

    async def get_group_size(self):
        group_size = await aio_redis_connection.scard(REDIS_USERNAME_KEY)
        return group_size
