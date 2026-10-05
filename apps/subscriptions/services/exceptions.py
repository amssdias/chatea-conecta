class SubscriptionServiceError(Exception):
    """Base error for subscription service failures."""


class UserSubscriptionNotFoundError(SubscriptionServiceError):
    """Raised when a local user subscription cannot be found."""


class SubscriptionMissingStripeIdError(SubscriptionServiceError):
    """Raised when the local subscription has no Stripe subscription ID."""


class SubscriptionAlreadyCancellingError(SubscriptionServiceError):
    """Raised when the subscription is already scheduled for cancellation."""


class SubscriptionCannotBeCancelledError(SubscriptionServiceError):
    """Raised when the subscription status does not allow cancellation."""


class SubscriptionCancellationProviderError(SubscriptionServiceError):
    """Raised when Stripe cannot cancel the subscription."""


class SubscriptionAlreadyActiveError(SubscriptionServiceError):
    """Raised when checkout is requested for an already active subscription."""


class CheckoutConfigurationError(SubscriptionServiceError):
    """Raised when the Stripe pricing configuration needed for checkout is missing."""


class CheckoutProviderError(SubscriptionServiceError):
    """Raised when Stripe cannot create the customer or the Checkout Session."""
