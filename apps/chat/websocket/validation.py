from apps.chat.websocket.exceptions import WebSocketValidationError


def validate_group_payload(data: dict) -> str:
    group = data.get("group")

    if not isinstance(group, str):
        raise WebSocketValidationError("Invalid group")

    normalized_group = group.strip().lower()
    if not normalized_group:
        raise WebSocketValidationError("Missing group")

    return normalized_group
