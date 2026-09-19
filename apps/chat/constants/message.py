MAX_CHAT_MESSAGE_LENGTH = 1000

# Shared by every WebSocket carrying the same trusted user/guest identity.
CHAT_MESSAGE_RATE_LIMIT = 8
CHAT_MESSAGE_RATE_WINDOW_SECONDS = 5
CHAT_MESSAGE_RATE_LIMIT_CLOSE_CODE = 4008
CHAT_MESSAGE_RATE_CACHE_KEY = "chat-message-rate:{user_id}"
