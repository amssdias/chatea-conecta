import asyncio

import aioredis
from django.conf import settings

aio_redis_connection = None


async def get_redis_aio_connection():
    global aio_redis_connection
    aio_redis_connection = await aioredis.from_url(settings.REDIS_CHANNEL_LAYER_URL, decode_responses=True)

asyncio.run(get_redis_aio_connection())
