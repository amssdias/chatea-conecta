import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from apps.subscriptions.services.exceptions import (
    UserSubscriptionNotFoundError,
    SubscriptionMissingStripeIdError,
    SubscriptionAlreadyCancellingError,
    SubscriptionCannotBeCancelledError,
    SubscriptionCancellationProviderError,
)
from apps.subscriptions.services.user_subscription import cancel_user_subscription

logger = logging.getLogger(__name__)


@login_required
@require_POST
def cancel_subscription_view(request):
    try:
        cancel_user_subscription(request.user)

    except UserSubscriptionNotFoundError:
        messages.error(request, _("You do not have a subscription to cancel."))

    except SubscriptionMissingStripeIdError:
        messages.error(request, _("Your subscription could not be found."))

    except SubscriptionAlreadyCancellingError:
        messages.info(
            request, _("Your subscription is already scheduled for cancellation.")
        )

    except SubscriptionCannotBeCancelledError:
        messages.error(request, _("Only active subscriptions can be cancelled."))

    except SubscriptionCancellationProviderError:
        messages.error(
            request,
            _("We could not cancel your subscription right now. Please try again later."),
        )

    else:
        messages.success(
            request,
            _("Your subscription has been scheduled for cancellation. You can keep using PRO until the end of your current billing period."),
        )

    return redirect("subscriptions:detail")
