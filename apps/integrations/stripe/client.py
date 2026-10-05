from functools import lru_cache

from django.conf import settings
from stripe import StripeClient


@lru_cache
def get_stripe_client() -> StripeClient:
    return StripeClient(
        settings.STRIPE_SECRET_KEY,
        stripe_version=settings.STRIPE_API_VERSION,
        max_network_retries=2,
    )
