import logging
import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY, TASK_LOCK_KEY, HAS_USERS
from apps.chat.services import AsyncRedisService
from apps.chat.tasks.send_random_chat_messages import send_random_messages

logger = logging.getLogger("chat_connect")


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        logger.info(f"---- {self.scope['cookies'].get('username')} CONNECTED TO WEBSOCKET ----")
        self.groups = set()
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
        await self.remove_user_from_active_list()
        await self.unregister_user_from_all_groups()
        await self.update_chat_activity_status()

    async def remove_user_from_active_list(self):
        """
        Removes the user from the list of active users stored in Redis.

        This operation ensures that the user's session is no longer considered active
        once they disconnect from the WebSocket.
        """

        username = self.scope.get("cookies", {}).get("username", "").lower()
        await AsyncRedisService.remove_username_from_set(REDIS_USERNAME_KEY, username)

    async def unregister_user_from_all_groups(self):
        for group in self.groups:
            await self.channel_layer.group_discard(group, self.channel_name)
            await self.notify_users_about_online_count(group_name=group)

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
        is_connected = await AsyncRedisService.is_user_in_set(
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
            await self.update_chat_activity_status()

            await self.notify_users_about_online_count(group_name=group)
            await self.send_user_bots_messages(group)
            # TODO: Should I leave this task only when a user enters? What if I run out of users and then they get deleted
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

    async def update_chat_activity_status(self):
        """
        Ensures the chat remains active by checking the group size and updating the HAS_USERS key.
        """
        group_size = await self.get_group_size()

        if group_size:
            await AsyncRedisService.set_if_not_exists(HAS_USERS, "true")
        else:
            await AsyncRedisService.delete_key(HAS_USERS)

    async def notify_users_about_online_count(self, group_name: str):
        """Sends the updated count of online users to all members of a group."""

        group_size = await self.get_group_size()

        # Send the user count to the group
        await self.channel_layer.group_send(
            group_name,
            {
                "type": "notify.users.count",
                "group_size": group_size + 60,
            },
        )

    async def notify_users_count(self, event):
        group_size = event["group_size"]

        # Send message to WebSocket (frontend)
        await self.send(
            text_data=json.dumps(
                {
                    "users_online": group_size
                }
            )
        )

    async def send_user_bots_messages(self, group: str):
        task_lock = await AsyncRedisService.set_if_not_exists(TASK_LOCK_KEY, "locked")
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
        group_size = await AsyncRedisService.get_group_size(REDIS_USERNAME_KEY)
        return group_size
