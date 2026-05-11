from django.db import transaction

from apps.subscriptions.models import UserSubscription
from apps.users.models import Profile


@transaction.atomic
def create_user_account_from_signup_form(*, form):
    user = form.save()

    Profile.objects.get_or_create(user=user)
    return user
