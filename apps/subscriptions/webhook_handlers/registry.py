from apps.integrations.stripe.constants import StripeEventType
from apps.subscriptions.webhook_handlers.checkout import handle_checkout_session_completed
from apps.subscriptions.webhook_handlers.invoices import (
    handle_invoice_paid,
    handle_invoice_payment_failed,
)
from apps.subscriptions.webhook_handlers.subscriptions import (
    handle_customer_subscription_deleted,
)


STRIPE_EVENT_HANDLERS = {
    StripeEventType.CHECKOUT_SESSION_COMPLETED: handle_checkout_session_completed,
    StripeEventType.INVOICE_PAID: handle_invoice_paid,
    StripeEventType.INVOICE_PAYMENT_FAILED: handle_invoice_payment_failed,
    StripeEventType.CUSTOMER_SUBSCRIPTION_DELETED: handle_customer_subscription_deleted,
}
