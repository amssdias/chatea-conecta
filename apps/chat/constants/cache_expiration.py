ONLINE_USER_TTL = 90
PRIVATE_CHATS_TTL = 60 * 30

# Long TTL for bot users, topics and messages cached from the database.
BOT_MESSAGE_CACHE_TTL = 60 * 60 * 24 * 7  # 1 week

# Short TTL used to avoid sending the same bot message too often.
BOT_MESSAGE_SENT_TTL = 60 * 60  # 1 hour
