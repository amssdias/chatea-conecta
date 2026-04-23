TASK_LOCK_KEY = "send_random_messages_task_lock"
USER_IDS = "user_ids"
USER_PROMOTIONAL_IDS = "user_promotional_ids"
USER_PROMOTIONAL_LINKS = "user_promotional_links"
TOPIC_IDS = "topic_ids"

# Namespace
REDIS_NAMESPACE = "chatconnect"

# --- User collections ---
REDIS_ALL_USERNAMES_KEY = f"{REDIS_NAMESPACE}:users:usernames"
REDIS_HAS_ACTIVE_USERS_KEY = f"{REDIS_NAMESPACE}:users:has_online"

# Username → UUID mapping (unique claim)
USERNAME_TO_UUID_KEY = f"{REDIS_NAMESPACE}:user:username:{{username}}"

# ID → username mapping (reverse lookup)
ID_TO_USERNAME_KEY = f"{REDIS_NAMESPACE}:user:id:{{user_id}}"

# Notification group for one user
USER_NOTIFICATION_GROUP = f"{REDIS_NAMESPACE}.user.inbox.{{user_id}}"

# Private chat group (for a chat between 2 UUIDs)
PRIVATE_CHAT_KEY = f"{REDIS_NAMESPACE}:chat:{{chat_id}}"
