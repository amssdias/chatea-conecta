from apps.integrations.stripe.client import get_stripe_client


def create_billing_portal_session(*, stripe_customer_id: str, return_url: str):
    """Create a Stripe-hosted portal session for a known customer."""
    client = get_stripe_client()
    return client.v1.billing_portal.sessions.create(
        {
            "customer": stripe_customer_id,
            "return_url": return_url,
        }
    )
