# --- WebSocket group names ---

# Group name used for private chats between two users.
# Example: private-userA-userB
USER_PRIVATE_GROUP = "private-{}-{}"

# --- Client -> Server actions ---
# Actions received from the frontend and handled by ACTION_MAP.

HEARTBEAT = "heartbeat"
REGISTER_GROUP = "register_group"
SEND_MESSAGE = "send_message"
PRIVATE_INVITE = "private_invite"

# --- Server -> Client events ---
# Events sent from the backend to the frontend so the UI can react.

NOTIFY_USERS_COUNT = "notify_users_count"

PRIVATE_CHAT_PARTICIPANT_ONLINE = "private_chat_participant_online"
PRIVATE_CHAT_PARTICIPANT_OFFLINE = "private_chat_participant_offline"

PRIVATE_CHATS_RESTORED = "private_chats_restored"

# --- Error events ---

ERROR_ACTION = "error_action"
