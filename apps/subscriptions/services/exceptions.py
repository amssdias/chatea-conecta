class SubscriptionServiceError(Exception):
    """Base error for subscription service failures."""


class UserSubscriptionNotFoundError(SubscriptionServiceError):
    """Raised when a local user subscription cannot be found."""


class InvalidStripeSubscriptionStatusError(SubscriptionServiceError):
    """Raised when a Stripe subscription has an unexpected status for the current operation."""


class SubscriptionMissingStripeIdError(SubscriptionServiceError):
    """Raised when the local subscription has no Stripe subscription ID."""


class SubscriptionAlreadyCancellingError(SubscriptionServiceError):
    """Raised when the subscription is already scheduled for cancellation."""


class SubscriptionCannotBeCancelledError(SubscriptionServiceError):
    """Raised when the subscription status does not allow cancellation."""


class SubscriptionCancellationProviderError(SubscriptionServiceError):
    """Raised when Stripe cannot cancel the subscription."""
