from apps.chat.constants.consumer import USER_PRIVATE_GROUP


def get_private_group_name(user1_id, user2_id):
    user1 = str(user1_id).replace(" ", "-")
    user2 = str(user2_id).replace(" ", "-")
    return USER_PRIVATE_GROUP.format(user1, user2).lower()
