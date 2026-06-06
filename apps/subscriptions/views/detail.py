from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus


@login_required
def subscription_detail_view(request):
    user_subscription = (
        UserSubscription.objects
        .filter(user=request.user)
        .first()
    )

    is_active = False
    is_pro = False
    needs_payment_configuration = False

    if user_subscription:
        is_active = user_subscription.status == UserSubscriptionStatus.ACTIVE
        is_pro = user_subscription.pro
        needs_payment_configuration = (
                user_subscription.status == UserSubscriptionStatus.PAST_DUE
        )

    subscription = {
        "instance": user_subscription,
        "is_active": is_active,
        "is_pro": is_pro,
        "needs_payment_configuration": needs_payment_configuration,
        "status": user_subscription.status if user_subscription else UserSubscriptionStatus.INACTIVE,
        "plan_name": "PRO",
        "started_at": user_subscription.started_at if user_subscription else None,
        "current_period_start": user_subscription.current_period_start if user_subscription else None,
        "current_period_end": user_subscription.current_period_end if user_subscription else None,
        "cancel_at_period_end": user_subscription.cancel_at_period_end if user_subscription else False,
        "canceled_at": user_subscription.canceled_at if user_subscription else None,
        "ended_at": user_subscription.ended_at if user_subscription else None,
    }

    return render(
        request,
        "subscriptions/subscription_detail.html",
        {
            "subscription": subscription,
        },
    )
