from apps.chat.utils.redis_connection import redis_connection


class RedisService:
    redis_connection = redis_connection  # Singleton sync Redis connection

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
