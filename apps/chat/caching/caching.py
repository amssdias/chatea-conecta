from django.core.cache import cache
from django.conf import settings


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
