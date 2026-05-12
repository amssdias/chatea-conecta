

def handle_checkout_session_completed(event_object):
    mark_subscription_active_from_checkout_session(session=event_object)


def handle_invoice_paid(event_object):
    mark_subscription_active_from_invoice(invoice=event_object)


def handle_invoice_payment_failed(event_object):
    mark_subscription_payment_failed_from_invoice(invoice=event_object)


def handle_customer_subscription_deleted(event_object):
    mark_subscription_canceled_from_stripe_subscription(
        stripe_subscription=event_object,
    )