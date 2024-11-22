from django.conf import settings

from apps.chat.utils.redis_connection import redis_connection


class RedisService:
    redis_connection = redis_connection  # Singleton sync Redis connection

    @classmethod
    def key_exists(cls, redis_key):
        """
        Check if a Redis key exists.

        :param redis_key: The Redis key to check.
        :return: True if the key exists, False otherwise.
        """
        return cls.redis_connection.exists(redis_key) == 1

    @classmethod
    def is_member(cls, redis_key, username):
        """
        Check if a username exists in the Redis set.

        :param redis_key: The Redis key representing the set.
        :param username: The username to check (case-insensitive).
        :return: True if the username exists, False otherwise.
        """
        lower_username = username.lower()
        return cls.redis_connection.sismember(redis_key, lower_username)

    @classmethod
    def add_to_set(cls, redis_key, username):
        """
        Add a username to the Redis set.

        :param redis_key: The Redis key representing the set.
        :param username: The username to add (case-insensitive).
        :return: Number of elements added to the set.
        """
        lower_username = username.lower()
        return cls.redis_connection.sadd(redis_key, lower_username)

    @classmethod
    def delete_key(cls, redis_key):
        """
        Delete a key from Redis.

        :param redis_key: The Redis key to delete.
        :return: Number of keys deleted (1 if successful, 0 if the key didn't exist).
        """
        return cls.redis_connection.delete(redis_key)

    @classmethod
    def remove_from_set(cls, redis_key, username):
        """
        Remove a username from the Redis set.

        :param redis_key: The Redis key representing the set.
        :param username: The username to remove (case-insensitive).
        :return: Number of members removed from the set.
        """
        lower_username = username.lower()
        return cls.redis_connection.srem(redis_key, lower_username)

    @classmethod
    def store_in_hash(cls, hash_key: str, data: dict):
        """
        Stores data in a Redis hash.

        Args:
            hash_key (str): The key for the Redis hash.
            data (dict): A dictionary with field-value pairs to store in the hash.
        """
        cls.redis_connection.hset(hash_key, mapping=data)
        cls.set_hash_expiration(hash_key, settings.CACHE_TIMEOUT_ONE_DAY)

    @classmethod
    def get_from_hash(cls, hash_key: str, field: str) -> str:
        """
        Retrieves a specific field value from a Redis hash.

        Args:
            hash_key (str): The key for the Redis hash.
            field (str): The field to retrieve.

        Returns:
            str: The value associated with the field, or None if not found.
        """
        import logging
        logger = logging.getLogger("chat_connect")
        value = cls.redis_connection.hget(hash_key, field)
        logger.info(f"--------- {value} ----------")
        return value

    @classmethod
    def set_hash_expiration(cls, hash_key: str, ttl_seconds: int):
        """
        Sets a time-to-live (TTL) for a Redis hash.

        Args:
            hash_key (str): The key for the Redis hash.
            ttl_seconds (int): Time-to-live in seconds.
        """
        cls.redis_connection.expire(hash_key, ttl_seconds)
