from __future__ import annotations

from typing import Optional

from stripe import Invoice, Subscription

from apps.integrations.stripe.invoices import get_invoice_subscription_id, get_invoice_url
from apps.integrations.stripe.subscriptions import retrieve_subscription, get_subscription_current_period_end
from apps.integrations.stripe.utils import from_stripe_timestamp
from apps.subscriptions.webhook_handlers.dtos import PaidSubscriptionDTO, FailedSubscriptionPaymentDTO, \
    StripeSubscriptionSyncDTO, StripeSubscriptionDeletedDTO


def build_paid_subscription_dto_from_invoice(invoice: Invoice) -> Optional[PaidSubscriptionDTO]:
    stripe_customer_id = invoice.customer
    stripe_subscription_id = get_invoice_subscription_id(invoice)

    if not stripe_customer_id or not stripe_subscription_id:
        return None

    subscription = retrieve_subscription(stripe_subscription_id)

    return PaidSubscriptionDTO(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription.id,
        stripe_status=subscription.status,
        started_at=from_stripe_timestamp(subscription.start_date),
        current_period_end=get_subscription_current_period_end(subscription),
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=from_stripe_timestamp(subscription.canceled_at),
        ended_at=from_stripe_timestamp(subscription.ended_at),
        latest_invoice_id=invoice.id,
        invoice_url=get_invoice_url(invoice),
    )


def build_failed_subscription_payment_dto_from_invoice(invoice: Invoice) -> Optional[FailedSubscriptionPaymentDTO]:
    stripe_customer_id = invoice.customer

    if not stripe_customer_id:
        return None

    stripe_subscription_id = get_invoice_subscription_id(invoice)
    subscription = retrieve_subscription(stripe_subscription_id)

    return FailedSubscriptionPaymentDTO(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=get_invoice_subscription_id(invoice),
        stripe_status=subscription.status,
        latest_invoice_id=invoice.id,
        invoice_url=get_invoice_url(invoice),
    )


def build_subscription_sync_dto(
        subscription: Subscription,
) -> Optional[StripeSubscriptionSyncDTO]:
    stripe_customer_id = subscription.customer

    if not stripe_customer_id:
        return None

    return StripeSubscriptionSyncDTO(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription.id,
        stripe_status=subscription.status,
        started_at=from_stripe_timestamp(subscription.start_date),
        current_period_end=get_subscription_current_period_end(subscription),
        cancel_at_period_end=subscription.cancel_at_period_end,
        canceled_at=from_stripe_timestamp(subscription.canceled_at),
        ended_at=from_stripe_timestamp(subscription.ended_at),
    )


def build_subscription_deleted_dto(
        subscription: Subscription,
) -> Optional[StripeSubscriptionDeletedDTO]:
    stripe_customer_id = subscription.customer

    if not stripe_customer_id:
        return None

    return StripeSubscriptionDeletedDTO(
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=subscription.id,
        canceled_at=from_stripe_timestamp(subscription.canceled_at),
        ended_at=from_stripe_timestamp(subscription.ended_at),
        current_period_end=get_subscription_current_period_end(subscription),
        cancel_at_period_end=subscription.cancel_at_period_end,
    )
