import asyncio
import aioredis
from django.conf import settings

redis_connection = None


async def main():
    global redis_connection
    redis_connection = aioredis.from_url(settings.REDIS_CHANNEL_LAYER_URL, decode_responses=True)

asyncio.run(main())
