import redis.asyncio as redis
from django.conf import settings

aio_redis_pool = redis.ConnectionPool.from_url(
    settings.REDIS_CHANNEL_LAYER_URL,
    decode_responses=True,
)

aio_redis_client = redis.Redis(connection_pool=aio_redis_pool)
