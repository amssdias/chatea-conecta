import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chat.constants.consumer import (
    SEND_MESSAGE,
    NOTIFY_USERS_COUNT,
    PRIVATE_INVITE,
    PRIVATE_CHAT_PARTICIPANT_OFFLINE,
)
from apps.chat.services.activity import (
    update_chat_activity_status,
    cleanup_user_presence,
    get_online_users_count,
)
from apps.chat.websocket.broadcast import (
    notify_group_online_count,
    broadcast_private_chat_user_offline,
)
from apps.chat.websocket.dispatch import dispatch_action
from apps.chat.websocket.registration import register_user_to_group

logger = logging.getLogger("chat_connect")


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        logger.info(
            f"---- {self.scope['cookies'].get('username')} CONNECTED TO WEBSOCKET ----"
        )
        self.id = self.scope["cookies"].get("user_id")
        self.username = self.scope["cookies"].get("username", "").lower()
        self.groups = set()
        self.private_chats = {}
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handles the cleanup when a user disconnects from the WebSocket.

        Steps:
        1. Remove the user from Redis to update the list of active users.
        2. Unregister the user from all groups they were a part of and notify remaining users about the updated online count.
        3. Reassess the activity status of the chat to update the `REDIS_HAS_ACTIVE_USERS_KEY` key.
        """

        logger.info(
            f"---- {self.scope['cookies'].get('username')} DISCONNECTING FROM WEBSOCKET ----"
        )
        username = self.scope["cookies"].get("username")
        await broadcast_private_chat_user_offline(self)
        await self.unregister_user_from_all_groups()
        await cleanup_user_presence(username, self.id)
        await update_chat_activity_status()

    async def unregister_user_from_all_groups(self):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)
            online_count = await get_online_users_count()
            await notify_group_online_count(
                self, group_name=group, online_count=online_count
            )

        self.groups.clear()

    async def receive(self, text_data):
        data = json.loads(text_data)
        await dispatch_action(self, data)

    async def notify_users_count(self, event):
        group_size = event["group_size"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {"type": NOTIFY_USERS_COUNT, "users_online": group_size}
            )
        )

    async def chat_message(self, event):
        """Receive message from room group"""
        message = event["message"]
        user_id = event["user_id"]
        username = event["username"]
        group = event["group"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {
                    "type": SEND_MESSAGE,
                    "message": message,
                    "username": username,
                    "userId": user_id,
                    "groupChatName": group,
                }
            )
        )

    async def chat_invite(self, event):
        private_group = event["private_group"]
        user_id = event["from_user_id"]

        await register_user_to_group(self, private_group)
        self.private_chats[user_id] = private_group

        await self.send(
            text_data=json.dumps(
                {
                    "type": PRIVATE_INVITE,
                    "fromUserId": user_id,
                    "privateGroup": private_group,
                }
            )
        )

    async def user_offline(self, event):
        user_id = event["user_id"]
        await self.send(
            text_data=json.dumps(
                {
                    "type": PRIVATE_CHAT_PARTICIPANT_OFFLINE,
                    "userId": user_id,
                }
            )
        )

        del self.private_chats[user_id]
