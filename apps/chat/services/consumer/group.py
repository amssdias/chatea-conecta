from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.services import AsyncRedisService


async def register_user_to_group(consumer, group_name: str):
    if group_name not in consumer.groups:
        await consumer.channel_layer.group_add(group_name, consumer.channel_name)
        consumer.groups.add(group_name)


async def get_group_size():
    group_size = await AsyncRedisService.get_group_size(REDIS_USERNAME_KEY)
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
