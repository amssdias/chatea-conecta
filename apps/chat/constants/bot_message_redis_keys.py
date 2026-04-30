from apps.chat.constants.redis_keys import REDIS_NAMESPACE

FEATURE = "bots"

# =============================================================================
# Bot message service - cached DB data
# =============================================================================

# Set of bot user IDs available to send automatic public chat messages.
BOT_USER_IDS = f"{REDIS_NAMESPACE}:{FEATURE}:user_ids"

# Hash of bot usernames.
# Field: user ID
# Value: username
BOT_USERNAMES = f"{REDIS_NAMESPACE}:{FEATURE}:usernames"

# Set of topic IDs available for normal bot messages.
BOT_TOPIC_IDS = f"{REDIS_NAMESPACE}:{FEATURE}:topic_ids"

# Hash of messages for a specific normal topic.
# Field: ConversationFlow ID
# Value: message text
BOT_TOPIC_MESSAGES = f"{REDIS_NAMESPACE}:{FEATURE}:topics:{{topic_id}}:messages"

# =============================================================================
# Bot message service - cache state
# =============================================================================

# String flag used to know whether bot users, topics and messages were already
# loaded from the database into Redis.
BOT_MESSAGE_CACHE_LOADED = f"{REDIS_NAMESPACE}:{FEATURE}:cache_loaded"

# =============================================================================
# Bot message service - runtime state
# =============================================================================

# String key marking that a message was recently sent by any bot.
# Should have a short TTL, for example 30 minutes or 1 hour.
BOT_MESSAGE_SENT = f"{REDIS_NAMESPACE}:{FEATURE}:messages:sent:{{message_id}}"

# =============================================================================
# Bot message service - promotional messages
# =============================================================================

# Hash of promotional links for bot users.
# Field: user ID
# Value: promotional/profile link
BOT_USER_PROMOTIONAL_LINKS = f"{REDIS_NAMESPACE}:{FEATURE}:promotional_links"

# Set of bot user IDs that have promotional links.
BOT_PROMOTIONAL_USER_IDS = f"{REDIS_NAMESPACE}:{FEATURE}:promotional_user_ids"

# Set of topic IDs available for promotional bot messages.
BOT_PROMOTIONAL_TOPIC_IDS = f"{REDIS_NAMESPACE}:{FEATURE}:promotional_topic_ids"

# Hash of messages for a specific promotional topic.
# Field: ConversationFlow ID
# Value: message text
BOT_PROMOTIONAL_TOPIC_MESSAGES = (
    f"{REDIS_NAMESPACE}:{FEATURE}:promotional_topics:{{topic_id}}:messages"
)
