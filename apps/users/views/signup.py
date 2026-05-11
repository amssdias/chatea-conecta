from django.contrib.auth import login
from django.shortcuts import redirect, render

from apps.subscriptions.services.create_pro_subscription import create_pro_checkout_session
from apps.users.constants import SignupIntent
from apps.users.forms import SignUpForm
from apps.users.services.create_user import create_user_account_from_signup_form


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    intent = get_signup_intent(request)

    if request.method == "POST":
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = create_user_account_from_signup_form(form=form)

            login(request, user)

            if intent == SignupIntent.PRO:
                session = create_pro_checkout_session(
                    user=user,
                    request=request,
                )
                return redirect(session.url)

            return redirect("home")

    else:
        form = SignUpForm()

    return render(
        request,
        "registration/signup",
        {
            "form": form,
            "intent": intent,
        },
    )


def get_signup_intent(request):
    intent = request.POST.get("intent") or request.GET.get("intent")

    if intent in SignupIntent.CHOICES:
        return intent

    return SignupIntent.NORMAL