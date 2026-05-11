from django.conf import settings
from stripe import StripeClient


def get_stripe_client() -> StripeClient:
    return StripeClient(settings.STRIPE_SECRET_KEY)