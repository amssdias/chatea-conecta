import redis.asyncio as redis
from django.conf import settings

aio_redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_CHANNEL_LAYER_URL,
    decode_responses=True,
)

aio_redis_client = None


def get_aio_redis_client():
    global aio_redis_client
    if aio_redis_client is None:
        aio_redis_client = redis.Redis(connection_pool=aio_redis_pool)
    return aio_redis_client
