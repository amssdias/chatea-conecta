import json

from apps.chat.constants.consumer import ERROR_ACTION


async def send_websocket_error(consumer, message: str) -> None:
    """Send a recoverable action error without closing the connection."""
    await consumer.send(
        text_data=json.dumps(
            {
                "type": ERROR_ACTION,
                "error": message,
            }
        )
    )
