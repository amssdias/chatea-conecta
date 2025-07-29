import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chat.constants.consumer import USER_GROUP_NOTIFICATION, REGISTER_GROUP, SEND_MESSAGE, NOTIFY_USERS_COUNT, \
    PRIVATE_INVITE
from apps.chat.services.consumer.activity import update_chat_activity_status, remove_user_from_active_list
from apps.chat.services.consumer.group import register_user_to_group, notify_group_online_count, \
    register_user_to_group_notification, get_private_group_name
from apps.chat.services.consumer.messaging import send_user_bots_messages
from apps.chat.services.consumer.validation import validate_user_connection, validate_group_payload

logger = logging.getLogger("chat_connect")


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        logger.info(f"---- {self.scope['cookies'].get('username')} CONNECTED TO WEBSOCKET ----")
        self.groups = set()
        self.private_chats = {}
        await self.accept()

    async def disconnect(self, close_code):
        """
        Handles the cleanup when a user disconnects from the WebSocket.

        Steps:
        1. Remove the user from Redis to update the list of active users.
        2. Unregister the user from all groups they were a part of and notify remaining users about the updated online count.
        3. Reassess the activity status of the chat to update the `HAS_USERS` key.
        """

        logger.info(f"---- {self.scope['cookies'].get('username')} DISCONNECTING FROM WEBSOCKET ----")
        await self.unregister_user_from_all_groups()
        await remove_user_from_active_list(self.scope)
        await update_chat_activity_status()

    async def unregister_user_from_all_groups(self):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)
            await notify_group_online_count(self, group_name=group)

        self.groups.clear()

    async def receive(self, text_data):
        """
        text_data: ARGS:
            type: str
        """

        username = await validate_user_connection(self.scope)
        if not username:
            await self.close(code=4001, reason="No username")
            return

        data = json.loads(text_data)
        action = data.get("type")

        if action == PRIVATE_INVITE:
            username_target = data.get("target_user_id").replace(" ", "-")

            if self.private_chats.get(username_target):
                return

            # Add user to private group created
            private_group = await get_private_group_name(username, username_target)
            clean_private_group = private_group.lower()
            await register_user_to_group(self, clean_private_group)

            self.private_chats[username_target] = clean_private_group

            # Notify the other user, so he's added to the private group
            await self.channel_layer.group_send(
                USER_GROUP_NOTIFICATION.format(username_target),
                {
                    "type": "chat.invite",
                    "from_user": username,
                    "private_group": clean_private_group,
                }
            )

        elif action == REGISTER_GROUP:
            group = validate_group_payload(data)
            if not group:
                await self.close(code=401, reason="No group")
                return None

            await register_user_to_group(self, group)
            await register_user_to_group_notification(self, username.replace(" ", "-"))
            await update_chat_activity_status()
            await notify_group_online_count(self, group_name=group)
            await send_user_bots_messages(group)
            return None

        elif action == SEND_MESSAGE:
            group = validate_group_payload(data)
            if not group:
                await self.close(code=401, reason="No group")
                return None

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

    async def notify_users_count(self, event):
        group_size = event["group_size"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {
                    "type": NOTIFY_USERS_COUNT,
                    "users_online": group_size
                }
            )
        )

    async def chat_message(self, event):
        """Receive message from room group"""
        message = event["message"]
        username = event["username"]
        group = event["group"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {
                    "type": SEND_MESSAGE,
                    "message": message,
                    "username": username,
                    "groupChatName": group,
                }
            )
        )

    async def chat_invite(self, event):
        private_group = event["private_group"]
        username = event["from_user"]

        await register_user_to_group(self, private_group)
        self.private_chats[username] = private_group

        await self.send(
            text_data=json.dumps(
                {
                    "type": PRIVATE_INVITE,
                    "from_user": username,
                    "private_group": private_group,
                }
            )
        )
