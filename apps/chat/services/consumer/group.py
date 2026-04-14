from apps.chat.constants.consumer import USER_PRIVATE_GROUP
from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY, USER_NOTIFICATION_GROUP
from apps.chat.services import AsyncRedisService


async def register_user_to_group(consumer, group_name: str):
    if group_name not in consumer.groups:
        await consumer.channel_layer.group_add(group_name, consumer.channel_name)
        consumer.groups.add(group_name)


async def register_user_to_group_notification(consumer, user_id: str):
    user_notification_group = USER_NOTIFICATION_GROUP.format(username=user_id)
    await consumer.channel_layer.group_add(user_notification_group, consumer.channel_name)
    consumer.groups.add(user_notification_group)


async def get_group_size():
    group_size = await AsyncRedisService.get_group_size(REDIS_ALL_USERNAMES_KEY)
    return group_size


async def notify_group_online_count(consumer, group_name: str):
    """Sends the updated count of online users to all members of a group."""

    group_size = await get_group_size()

    await consumer.channel_layer.group_send(
        group_name,
        {
            "type": "notify.users.count",
            "group_size": group_size + 60,
        },
    )


async def get_private_group_name(user1_id, user2_id):
    user1 = user1_id.replace(" ", "-")
    user2 = user2_id.replace(" ", "-")
    return USER_PRIVATE_GROUP.format(user1, user2).lower()
