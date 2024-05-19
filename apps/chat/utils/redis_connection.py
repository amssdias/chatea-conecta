import redis
from django.conf import settings

redis_pool = redis.ConnectionPool.from_url(settings.REDIS_CHANNEL_LAYER_URL, decode_responses=True)

redis_connection = redis.Redis(connection_pool=redis_pool)
