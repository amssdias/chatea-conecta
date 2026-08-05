"""
Guest session identity.

Guests have no Django session, so their identity travels in a cookie. That
cookie is a *signed* token: the browser can read nothing useful out of it and
cannot forge one, because it is signed with ``SECRET_KEY``.

A valid signature only proves the server once issued the ``(username, user_id)``
pair. Before the identity is trusted it is also checked against the Redis
ownership mapping, so a nickname can never be claimed by a different id.

Both checks run on every entry point: the HTTP chat view and the websocket
handshake.
"""

from __future__ import annotations

from django.conf import settings
from django.core import signing

from apps.chat.constants.redis_keys import ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.constants.username import USERNAME_REGEX
from apps.chat.infrastructure.redis.async_redis_service import AsyncRedisService
from apps.chat.infrastructure.redis.sync_redis_service import RedisService

GUEST_SESSION_COOKIE = "guest_session"
GUEST_SESSION_SALT = "apps.chat.guest_session"

USERNAME_CLAIM = "u"
USER_ID_CLAIM = "i"


def issue_guest_token(username: str, user_id: str) -> str:
    """
    Mint a signed token carrying a guest identity.

    Args:
        username: Nickname chosen by the guest.
        user_id: Server generated id the nickname was registered with.

    Returns:
        Signed token, safe to hand to the browser as a cookie value.
    """
    return signing.dumps(
        {USERNAME_CLAIM: username, USER_ID_CLAIM: str(user_id)},
        salt=GUEST_SESSION_SALT,
    )


def read_guest_token(token: str) -> tuple[str, str] | None:
    """
    Verify a guest token's signature and return the identity it carries.

    This only proves the token was issued by this server and has not expired.
    Ownership of the nickname still has to be confirmed against Redis with
    ``claim_guest_identity`` before the identity is used.

    Args:
        token: Raw cookie value.

    Returns:
        (username, user_id), or None if the token is missing, tampered with,
        expired or malformed.
    """
    if not token:
        return None

    try:
        payload = signing.loads(
            token,
            salt=GUEST_SESSION_SALT,
            max_age=settings.GUEST_SESSION_MAX_AGE,
        )
    except signing.BadSignature:
        return None

    if not isinstance(payload, dict):
        return None

    username = payload.get(USERNAME_CLAIM)
    user_id = payload.get(USER_ID_CLAIM)

    if not isinstance(username, str) or not isinstance(user_id, str):
        return None

    if not user_id or not USERNAME_REGEX.fullmatch(username):
        return None

    return username, user_id


def claim_guest_identity(username: str, user_id: str) -> bool:
    """
    Confirm that ``user_id`` owns ``username`` in Redis, and refresh the mapping.

    The nickname is claimed with SET NX, so the check stays race free: either
    this call wins the nickname or it reads back whoever holds it. Winning is
    only possible when the mapping has expired, and a signed token is proof the
    server issued that pair in the first place, so the session is re-adopted
    instead of being thrown away.

    Args:
        username: Nickname from the signed token.
        user_id: User id from the signed token.

    Returns:
        True if the identity is legitimate, False if the nickname belongs to
        another user id.
    """
    username_key = USERNAME_TO_UUID_KEY.format(username=username.lower())

    claimed = RedisService.set_unique(
        username_key,
        user_id,
        ttl=settings.GUEST_SESSION_MAX_AGE,
    )

    if not claimed and RedisService.get_key(username_key) != user_id:
        return False

    RedisService.set_value(
        ID_TO_USERNAME_KEY.format(user_id=user_id),
        username,
        timeout=settings.GUEST_SESSION_MAX_AGE,
    )

    if not claimed:
        RedisService.set_expiration(username_key, settings.GUEST_SESSION_MAX_AGE)

    return True


async def aclaim_guest_identity(username: str, user_id: str) -> bool:
    """
    Async counterpart of :func:`claim_guest_identity`, for the websocket handshake.
    """
    username_key = USERNAME_TO_UUID_KEY.format(username=username.lower())

    claimed = await AsyncRedisService.set_value(
        username_key,
        user_id,
        ex=settings.GUEST_SESSION_MAX_AGE,
        nx=True,
    )

    if not claimed and await AsyncRedisService.get_value(username_key) != user_id:
        return False

    await AsyncRedisService.set_value(
        ID_TO_USERNAME_KEY.format(user_id=user_id),
        username,
        ex=settings.GUEST_SESSION_MAX_AGE,
    )

    if not claimed:
        await AsyncRedisService.set_expiration(
            username_key,
            settings.GUEST_SESSION_MAX_AGE,
        )

    return True


async def aresolve_guest_identity(token: str) -> tuple[str, str] | None:
    """
    Turn a raw cookie value into a trusted guest identity.

    Args:
        token: Raw ``guest_session`` cookie value from the websocket scope.

    Returns:
        (username, user_id) when both the signature and the Redis ownership
        check pass, None otherwise.
    """
    identity = read_guest_token(token)

    if identity is None:
        return None

    username, user_id = identity

    if not await aclaim_guest_identity(username, user_id):
        return None

    return username, user_id


async def arefresh_guest_identity(username: str, user_id: str) -> None:
    """
    Extend the TTL of the identity mapping of a connected guest.

    Called from the websocket heartbeat so an open session never has its
    ownership mapping expire underneath it.
    """
    await AsyncRedisService.set_expiration(
        USERNAME_TO_UUID_KEY.format(username=username.lower()),
        settings.GUEST_SESSION_MAX_AGE,
    )
    await AsyncRedisService.set_expiration(
        ID_TO_USERNAME_KEY.format(user_id=user_id),
        settings.GUEST_SESSION_MAX_AGE,
    )


def revoke_guest_identity(username: str, user_id: str) -> None:
    """
    Drop the ownership mapping of a guest, so an old token stops being usable.

    Used on logout: without this the token stays valid until it expires and
    could collide with whoever takes the nickname next.
    """
    RedisService.delete_key(USERNAME_TO_UUID_KEY.format(username=username.lower()))

    if user_id:
        RedisService.delete_key(ID_TO_USERNAME_KEY.format(user_id=user_id))
