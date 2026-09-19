import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.edit import FormView

from apps.chat.services.register_user import register_user_on_redis
from apps.subscriptions.services.create_pro_subscription import create_pro_checkout_session
from apps.subscriptions.services.exceptions import SubscriptionServiceError
from apps.users.constants import SignupIntent
from apps.users.forms import SignUpForm
from apps.users.services.create_user import create_user_account_from_signup_form

logger = logging.getLogger(__name__)


class SignUpView(FormView):
    template_name = "registration/signup.html"
    form_class = SignUpForm
    success_url = reverse_lazy("chat:home")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("chat:home")

        return super().dispatch(request, *args, **kwargs)

    def get_signup_intent(self):
        intent = self.request.POST.get("intent") or self.request.GET.get("intent")

        valid_intents = {
            choice[0] if isinstance(choice, (tuple, list)) else choice
            for choice in SignupIntent.CHOICES
        }

        if intent in valid_intents:
            return intent

        return SignupIntent.NORMAL

    def form_valid(self, form):
        user = create_user_account_from_signup_form(form=form)

        login(self.request, user)
        register_user_on_redis(user.username)
        intent = self.get_signup_intent()

        if intent == SignupIntent.PRO:
            response = self._start_pro_checkout(user)
        else:
            response = redirect("chat:live-chat")

        response.set_cookie(
            key="username",
            value=user.username,
            httponly=True,
            secure=settings.COOKIES_SECURE,
            samesite="Lax",
        )

        response.set_cookie(
            key="user_id",
            value=user.id,
            httponly=True,
            secure=settings.COOKIES_SECURE,
            samesite="Lax",
        )

        return response

    def _start_pro_checkout(self, user):
        """
        Send the new user to Stripe Checkout, or to their subscription page if
        Checkout cannot be started.

        The account already exists and is logged in at this point, so a failure
        here must not surface as a server error: the user would try to sign up
        again and hit username/email uniqueness errors on an account that is
        already theirs. The subscription page shows the message and offers a retry.
        """
        try:
            session = create_pro_checkout_session(
                user=user,
                request=self.request,
            )
        except SubscriptionServiceError:
            logger.exception(
                "Could not start PRO checkout after signup. user_id=%s",
                user.id,
            )
            messages.error(
                self.request,
                _(
                    "Your account was created, but we could not start the PRO "
                    "checkout. You are signed in and can try upgrading again below."
                ),
            )
            return redirect("subscriptions:detail")

        return redirect(session.url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["intent"] = self.get_signup_intent()
        return context
