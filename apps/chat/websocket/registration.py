from apps.chat.constants.consumer import USER_PRIVATE_GROUP
from apps.chat.constants.redis_keys import USER_NOTIFICATION_GROUP


async def register_user_to_group(consumer, group_name: str):
    if group_name not in consumer.groups:
        await consumer.channel_layer.group_add(group_name, consumer.channel_name)
        consumer.groups.add(group_name)


async def register_user_to_group_notification(consumer, user_id: str):
    user_notification_group = USER_NOTIFICATION_GROUP.format(user_id=user_id)
    await register_user_to_group(consumer, user_notification_group)


async def get_private_group_name(user1_id, user2_id):
    user1 = user1_id.replace(" ", "-")
    user2 = user2_id.replace(" ", "-")
    return USER_PRIVATE_GROUP.format(user1, user2).lower()
