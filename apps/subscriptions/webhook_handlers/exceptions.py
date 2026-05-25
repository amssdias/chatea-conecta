class StripeWebhookProcessingError(Exception):
    """Base error for subscription webhook processing failures."""


class InvalidStripeInvoiceError(StripeWebhookProcessingError):
    """Raised when a Stripe invoice is missing required data."""


class SubscriptionPaymentProcessingError(StripeWebhookProcessingError):
    """Raised when a subscription payment event cannot be processed."""


class MissingStripeInvoiceCustomerError(InvalidStripeInvoiceError):
    """Raised when a Stripe invoice has no customer."""


class MissingStripeInvoiceSubscriptionError(InvalidStripeInvoiceError):
    """Raised when a Stripe invoice has no subscription."""


class InvalidStripeSubscriptionError(StripeWebhookProcessingError):
    """Raised when a Stripe subscription payload is missing required data."""


class MissingStripeSubscriptionCustomerError(InvalidStripeSubscriptionError):
    """Raised when a Stripe subscription has no customer."""
