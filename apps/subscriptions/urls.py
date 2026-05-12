from django.urls import path

from apps.subscriptions.views import create_pro_checkout_session_view, checkout_success_view, checkout_cancel_view

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
    # path(
    #     "webhooks/stripe/",
    #     webhooks.stripe_webhook_view,
    #     name="stripe_webhook",
    # ),
]