USER_IDS = "user_ids"
USER_PROMOTIONAL_IDS = "user_promotional_ids"
USER_PROMOTIONAL_LINKS = "user_promotional_links"
TOPIC_IDS = "topic_ids"

# Namespace
REDIS_NAMESPACE = "chatconnect"

# --- User collections ---
REDIS_ALL_USERNAMES_KEY = f"{REDIS_NAMESPACE}:users:usernames"

# Username → UUID mapping (unique claim)
USERNAME_TO_UUID_KEY = f"{REDIS_NAMESPACE}:user:username:{{username}}"

# ID → username mapping (reverse lookup)
ID_TO_USERNAME_KEY = f"{REDIS_NAMESPACE}:user:id:{{user_id}}"

# Notification group for one user
USER_NOTIFICATION_GROUP = f"{REDIS_NAMESPACE}.user.inbox.{{user_id}}"

# --- User online/session state ---
USER_ONLINE_KEY = f"{REDIS_NAMESPACE}:user:online:{{user_id}}"

# --- User private chats ---
USER_PRIVATE_CHATS_KEY = f"{REDIS_NAMESPACE}:user:private_chats:{{user_id}}"
