from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PaidSubscriptionDTO:
    stripe_customer_id: str
    stripe_subscription_id: str
    stripe_status: str
    started_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    ended_at: datetime | None
    latest_invoice_id: str
    invoice_url: str | None


@dataclass(frozen=True)
class FailedSubscriptionPaymentDTO:
    stripe_customer_id: str
    stripe_subscription_id: str | None
    stripe_status: str
    latest_invoice_id: str
    invoice_url: str | None


@dataclass(frozen=True)
class StripeSubscriptionSyncDTO:
    stripe_customer_id: str
    stripe_subscription_id: str
    stripe_status: str
    started_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    canceled_at: datetime | None
    ended_at: datetime | None


@dataclass(frozen=True)
class StripeSubscriptionDeletedDTO:
    stripe_customer_id: str
    stripe_subscription_id: str
    canceled_at: datetime | None
    ended_at: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
