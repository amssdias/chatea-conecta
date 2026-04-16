from apps.chat.infrastructure.redis.async_client import get_aio_redis_client


class AsyncRedisService:

    @classmethod
    def get_client(cls):
        return get_aio_redis_client()

    @classmethod
    async def get_value(cls, redis_key):
        return await cls.get_client().get(redis_key)

    @classmethod
    async def remove_username_from_set(cls, redis_key, username):
        """
        Remove the username from the Redis set.

        :param redis_key: The Redis key for the set.
        :param username: The username to remove.
        :return: Number of removed members (0 if the user wasn't in the set).
        """
        removed_count = await cls.get_client().srem(redis_key, username)
        return removed_count

    @classmethod
    async def set_if_not_exists(cls, lock_key, value="locked"):
        """
        Set a Redis key only if it does not already exist (NX: Set if Not Exists).

        :param lock_key: The Redis key to set.
        :param value: The value to set. Default is "locked".
        :return: True if the key was set, False otherwise.
        """
        was_set = await cls.get_client().setnx(lock_key, value)
        return was_set

    @classmethod
    async def get_group_size(cls, redis_key):
        """
        Asynchronously get the size of a Redis set.

        :param redis_key: The Redis key representing the set.
        :return: The size of the set.
        """
        group_size = await cls.get_client().scard(redis_key)
        return group_size

    @classmethod
    async def delete_key(cls, redis_key):
        """
        Asynchronously delete a key from Redis.

        :param redis_key: The Redis key to delete.
        :return: Number of keys deleted (1 if successful, 0 if the key didn't exist).
        """
        result = await cls.get_client().delete(redis_key)
        return result
