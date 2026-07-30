from django.urls import path

from apps.subscriptions.views import (
    create_pro_checkout_session_view,
    checkout_success_view,
    checkout_cancel_view,
    subscription_detail_view,
    cancel_subscription_view,
    create_billing_portal_session_view,
)

app_name = "subscriptions"

urlpatterns = [
    path(
        "checkout/pro/",
        create_pro_checkout_session_view,
        name="create_pro_checkout_session",
    ),
    path(
        "checkout/success/",
        checkout_success_view,
        name="checkout_success",
    ),
    path(
        "checkout/cancel/",
        checkout_cancel_view,
        name="checkout_cancel",
    ),
    path(
        "detail/",
        subscription_detail_view,
        name="detail",
    ),
    path(
        "cancel/",
        cancel_subscription_view,
        name="cancel",
    ),
    path(
        "billing-portal/",
        create_billing_portal_session_view,
        name="billing_portal",
    ),
]
