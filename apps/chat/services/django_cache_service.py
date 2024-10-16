import logging
from django.core.cache import cache
from asgiref.sync import sync_to_async

logger = logging.getLogger("chat_connect")


class DjangoCacheService:
    CACHE_TIMEOUT = 60 * 15  # Default cache timeout (adjust as needed)

    @staticmethod
    def get_or_set_cache(cache_key, model_class, get_or_create_kwargs, timeout=60 * 60 * 24):
        """
        Retrieves an object from the cache or gets it from the database and sets the cache.

        :param cache_key: Key to identify the object in cache.
        :param model_class: Django model class to query.
        :param get_or_create_kwargs: Dict of fields to use with get_or_create.
        :param timeout: Cache timeout in seconds.
        :return: Model instance.
        """
        obj = cache.get(cache_key)

        if not obj:
            obj, _ = model_class.objects.get_or_create(**get_or_create_kwargs)
            cache.set(cache_key, obj, timeout)

        return obj

    @staticmethod
    async def async_delete_cache(cache_key):
        """
        Asynchronously delete a cache key.

        :param cache_key: The cache key to delete.
        :return: None
        """
        await sync_to_async(cache.delete)(cache_key)

    @staticmethod
    async def async_set_cache(cache_key, value, timeout=None):
        """
        Asynchronously set a cache key with a value.

        :param cache_key: The cache key to set.
        :param value: The value to store.
        :param timeout: Cache expiration timeout.
        :return: None
        """
        await sync_to_async(cache.set)(cache_key, value, timeout)


    @staticmethod
    def get_cache(cache_key):
        """
        Synchronously get a value from the cache.

        :param cache_key: The cache key to retrieve.
        :return: The cached value, or None if the key doesn't exist.
        """
        return cache.get(cache_key)
