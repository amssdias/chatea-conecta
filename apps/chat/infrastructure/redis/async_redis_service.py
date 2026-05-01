from django.conf import settings

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

    @classmethod
    async def add_to_set(cls, redis_key, value):
        """
        Add a username to the Redis set.

        Args:
            redis_key: Redis key representing the set.
            value: value to add.

        Returns:
            Number of elements added to the set.
        """
        lower_username = value.lower()
        return await cls.get_client().sadd(redis_key, lower_username)

    @classmethod
    async def set_expiration(cls, redis_key, seconds):
        """
        Set expiration time for a Redis key.
        """
        return await cls.get_client().expire(redis_key, seconds)

    @classmethod
    async def set_value(cls, key, value, ex=settings.CACHE_TIMEOUT_ONE_DAY, nx=False):
        """
        Set a Redis key/value pair.

        Args:
            key: Redis key.
            value: Value to store.
            ex: Optional expiration time in seconds.
            nx: If True, only set the key if it does not already exist.

        Returns:
            True if the value was set.
            False if nx=True and the key already existed.
        """
        return bool(
            await cls.get_client().set(
                key,
                value,
                ex=ex,
                nx=nx,
            )
        )

    @classmethod
    async def set_hash_value(cls, redis_key, field, value, ex=None):
        """
        Set a field/value pair inside a Redis hash.

        Args:
            redis_key: Redis hash key.
            field: Hash field to store, e.g. target user ID.
            value: Hash value to store, e.g. private group name.
            ex: Optional expiration time in seconds for the whole hash key.

        Returns:
            Number of fields that were added.
            Redis returns 1 if a new field was created, 0 if an existing field was updated.
        """
        result = await cls.get_client().hset(redis_key, field, value)

        if ex:
            await cls.get_client().expire(redis_key, ex)

        return result

    @classmethod
    async def get_hash(cls, redis_key):
        """
        Return all fields and values from a Redis hash.
        """
        return await cls.get_client().hgetall(redis_key)

    @classmethod
    async def is_member(cls, key: str, value: str) -> bool:
        return bool(await cls.get_client().sismember(key, value))
