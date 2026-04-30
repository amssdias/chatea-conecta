from __future__ import annotations

from django.conf import settings
from django.utils.http import int_to_base36

from apps.chat.infrastructure.redis.sync_client import redis_client


class RedisService:
    redis_client = redis_client

    @classmethod
    def get_key(cls, key):
        return cls.redis_client.get(key)

    @classmethod
    def get_random_set_member(cls, key: str) -> str | None:
        """
        Return one random member from a Redis set.

        Args:
            key: Redis set key.

        Returns:
            Random set member, or None if the set is empty/missing.
        """
        value = cls.redis_client.srandmember(key)

        if value is None:
            return None

        if isinstance(value, bytes):
            return value.decode("utf-8")

        return value

    @classmethod
    def get_hash(cls, key: str) -> dict[str, str]:
        """
        Return all field/value pairs from a Redis hash.

        Args:
            key: Redis hash key.

        Returns:
            Dictionary with decoded string fields and values.
        """
        data = cls.redis_client.hgetall(key)

        if not data:
            return {}

        return {
            key.decode("utf-8") if isinstance(key, bytes) else str(key):
                value.decode("utf-8") if isinstance(value, bytes) else str(value)
            for key, value in data.items()
        }

    @classmethod
    def get_from_hash(cls, key: str, field: str | int) -> str | None:
        """
        Get one value from a Redis hash.

        Args:
            key: Redis hash key.
            field: Hash field.

        Returns:
            Hash value, or None if the field does not exist.
        """
        value = cls.redis_client.hget(key, str(field))

        if value is None:
            return None

        if isinstance(value, bytes):
            return value.decode("utf-8")

        return value

    @classmethod
    def key_exists(cls, redis_key):
        """
        Check if a Redis key exists.

        :param redis_key: The Redis key to check.
        :return: True if the key exists, False otherwise.
        """
        return bool(cls.redis_client.exists(redis_key))

    @classmethod
    def set_value(cls, redis_key: str, value: str, timeout=None) -> bool:
        """
        Store a string value in Redis.

        Args:
            redis_key: Redis key where the value will be stored.
            value: Value to store.
            timeout: Optional expiration time in seconds.

        Returns:
            True if the value was stored successfully.
        """
        return bool(
            cls.redis_client.set(
                name=redis_key,
                value=value,
                ex=timeout,
            )
        )

    @classmethod
    def set_expiration(cls, key: str, ttl: int) -> bool:
        """
        Set an expiration time on a Redis key.

        Args:
            key: Redis key.
            ttl: Expiration time in seconds.

        Returns:
            True if the timeout was set.
        """
        return bool(cls.redis_client.expire(key, ttl))

    @classmethod
    def store_hash(cls, key: str, data: dict[str, str]) -> int:
        """
        Store multiple field/value pairs in a Redis hash.

        Args:
            key: Redis hash key.
            data: Mapping of hash fields to values.

        Returns:
            Number of fields added.
        """
        if not data:
            return 0

        return cls.redis_client.hset(key, mapping=data)

    @classmethod
    def is_member(cls, redis_key, username):
        """
        Check if a username exists in the Redis set.

        :param redis_key: The Redis key representing the set.
        :param username: The username to check (case-insensitive).
        :return: True if the username exists, False otherwise.
        """
        lower_username = username.lower()
        return cls.redis_client.sismember(redis_key, lower_username)

    @classmethod
    def add_to_set(cls, key: str, *values: str | int) -> int:
        """
        Add one or more values to a Redis set.

        Args:
            key: Redis set key.
            values: Values to add to the set.

        Returns:
            Number of new values added to the set.
        """
        if not values:
            return 0

        normalized_values = [str(value) for value in values]

        return cls.redis_client.sadd(key, *normalized_values)

    @classmethod
    def set_unique(cls, key, value, ttl=settings.CACHE_TIMEOUT_ONE_DAY):
        """
        Store a key/value pair only if the key doesn't exist yet.

        Args:
            key: Redis key.
            value: Value to store.
            ttl: Optional expiration time in seconds.

        Returns:
            True if created, False if key already existed.
        """
        return cls.redis_client.set(key, value, ex=ttl, nx=True)

    @classmethod
    def create_user_id(cls):
        n = cls.redis_client.incr("user:next_id")
        short_id = int_to_base36(n)
        return f"u_{short_id.zfill(5)}"

    @classmethod
    def delete_key(cls, redis_key):
        """
        Delete a key from Redis.

        :param redis_key: The Redis key to delete.
        :return: Number of keys deleted (1 if successful, 0 if the key didn't exist).
        """
        return cls.redis_client.delete(redis_key)

    @classmethod
    def remove_from_set(cls, redis_key, username):
        """
        Remove a username from the Redis set.

        :param redis_key: The Redis key representing the set.
        :param username: The username to remove (case-insensitive).
        :return: Number of members removed from the set.
        """
        lower_username = username.lower()
        return cls.redis_client.srem(redis_key, lower_username)

    # TODO: Delete, used on old message service
    @classmethod
    def store_in_hash(cls, hash_key: str, data: dict):
        """
        Stores data in a Redis hash.

        Args:
            hash_key (str): The key for the Redis hash.
            data (dict): A dictionary with field-value pairs to store in the hash.
        """
        cls.redis_client.hset(hash_key, mapping=data)
        cls.set_hash_expiration(hash_key, settings.CACHE_TIMEOUT_ONE_DAY)

    # @classmethod
    # def get_from_hash(cls, hash_key: str, field: str) -> str:
    #     """
    #     Retrieves a specific field value from a Redis hash.
    #
    #     Args:
    #         hash_key (str): The key for the Redis hash.
    #         field (str): The field to retrieve.
    #
    #     Returns:
    #         str: The value associated with the field, or None if not found.
    #     """
    #     value = cls.redis_client.hget(hash_key, field)
    #     return value

    @classmethod
    def set_hash_expiration(cls, hash_key: str, ttl_seconds: int):
        """
        Sets a time-to-live (TTL) for a Redis hash.

        Args:
            hash_key (str): The key for the Redis hash.
            ttl_seconds (int): Time-to-live in seconds.
        """
        cls.redis_client.expire(hash_key, ttl_seconds)

    @classmethod
    def get_group_size(cls, redis_key: str) -> int:
        """Returns the size of a Redis set synchronously"""
        return cls.redis_client.scard(redis_key)

    @classmethod
    def has_keys_matching_pattern(cls, pattern: str) -> bool:
        for _ in cls.redis_client.scan_iter(match=pattern, count=1):
            return True

        return False
