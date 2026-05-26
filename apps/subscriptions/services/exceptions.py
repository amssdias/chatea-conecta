class SubscriptionServiceError(Exception):
    """Base error for subscription service failures."""


class UserSubscriptionNotFoundError(SubscriptionServiceError):
    """Raised when a local user subscription cannot be found."""


class InvalidStripeSubscriptionStatusError(SubscriptionServiceError):
    """Raised when a Stripe subscription has an unexpected status for the current operation."""
