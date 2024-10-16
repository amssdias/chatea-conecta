import logging

from chat_connect.utils.aio_redis_connection import aio_redis_connection

logger = logging.getLogger("chat_connect")


class AsyncRedisService:
    async_redis_connection = aio_redis_connection # Singleton

    @classmethod
    async def is_user_in_set(cls, redis_key, username):
        """
        Check if the username exists in the Redis set.

        :param redis_key: The Redis key for the set.
        :param username: The username to check.
        :return: True if the user is in the set, False otherwise.
        """
        is_connected = await cls.async_redis_connection.sismember(redis_key, username)
        return is_connected

    @classmethod
    async def remove_username_from_set(cls, redis_key, username):
        """
        Remove the username from the Redis set.

        :param redis_key: The Redis key for the set.
        :param username: The username to remove.
        :return: Number of removed members (0 if the user wasn't in the set).
        """
        removed_count = await cls.async_redis_connection.srem(redis_key, username)
        return removed_count

    @classmethod
    async def set_task_lock(cls, lock_key, value="locked"):
        """
        Set a Redis key only if it does not already exist (NX: Set if Not Exists).

        :param lock_key: The Redis key to set.
        :param value: The value to set. Default is "locked".
        :return: True if the key was set, False otherwise.
        """
        was_set = await cls.async_redis_connection.setnx(lock_key, value)
        return was_set

    @classmethod
    async def get_group_size(cls, redis_key):
        """
        Asynchronously get the size of a Redis set.

        :param redis_key: The Redis key representing the set.
        :return: The size of the set.
        """
        group_size = await cls.async_redis_connection.scard(redis_key)
        return group_size