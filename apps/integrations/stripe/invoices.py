from __future__ import annotations

from stripe import Invoice


def get_invoice_subscription_id(invoice: Invoice) -> str | None:
    parent = invoice.parent

    if not parent or not parent.subscription_details:
        return None

    subscription = parent.subscription_details.subscription

    if not subscription:
        return None

    if isinstance(subscription, str):
        return subscription

    return subscription.id


def get_invoice_url(invoice: Invoice) -> str | None:
    return invoice.hosted_invoice_url or invoice.invoice_pdf
