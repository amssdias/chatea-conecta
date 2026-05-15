from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.subscriptions.services.create_pro_subscription import create_pro_checkout_session


@login_required
@require_POST
def create_pro_checkout_session_view(request):
    session = create_pro_checkout_session(
        user=request.user,
        request=request,
    )

    return redirect(session.url)


@login_required
def checkout_success_view(request):
    return render(request, "subscriptions/checkout_success.html")


@login_required
def checkout_cancel_view(request):
    return render(request, "subscriptions/checkout_cancel.html")
