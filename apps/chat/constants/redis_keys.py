USER_IDS = "user_ids"
USER_PROMOTIONAL_IDS = "user_promotional_ids"
USER_PROMOTIONAL_LINKS = "user_promotional_links"
TOPIC_IDS = "topic_ids"

# =============================================================================
# Namespace
# =============================================================================

REDIS_NAMESPACE = "chatconnect"

# =============================================================================
# User collections
# =============================================================================

# Set/List of all usernames used by the chat app.
REDIS_ALL_USERNAMES_KEY = f"{REDIS_NAMESPACE}:users:usernames"

# Username → UUID mapping.
USERNAME_TO_UUID_KEY = f"{REDIS_NAMESPACE}:user:username:{{username}}"

# User ID → username mapping.
ID_TO_USERNAME_KEY = f"{REDIS_NAMESPACE}:user:id:{{user_id}}"

# =============================================================================
# User groups
# =============================================================================

# Channel layer notification group for one user.
# Note: this uses dots because it is a Channels group name, not a Redis data key.
USER_NOTIFICATION_GROUP = f"{REDIS_NAMESPACE}.user.inbox.{{user_id}}"

# =============================================================================
# User online/session state
# =============================================================================

# String key marking that a user is currently online.
USER_ONLINE_KEY = f"{REDIS_NAMESPACE}:user:online:{{user_id}}"

# =============================================================================
# User private chats
# =============================================================================

# Set of private chat group names for a user.
USER_PRIVATE_CHATS_KEY = f"{REDIS_NAMESPACE}:user:private_chats:{{user_id}}"
