import factory
from django.utils import timezone

from apps.subscriptions.models import UserSubscription
from apps.subscriptions.models.choices import UserSubscriptionStatus
from apps.users.tests.factories import UserFactory


class UserSubscriptionFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)

    status = UserSubscriptionStatus.INACTIVE

    stripe_customer_id = factory.Sequence(lambda n: f"cus_{n}")
    stripe_subscription_id = None

    started_at = None
    current_period_start = None
    current_period_end = None

    cancel_at_period_end = False
    canceled_at = None
    ended_at = None

    class Meta:
        model = UserSubscription

    class Params:
        with_subscription = factory.Trait(
            stripe_subscription_id=factory.Sequence(lambda n: f"sub_{n}"),
        )

        active = factory.Trait(
            status=UserSubscriptionStatus.ACTIVE,
            stripe_subscription_id=factory.Sequence(lambda n: f"sub_{n}"),
            started_at=factory.LazyFunction(timezone.now),
            current_period_start=factory.LazyFunction(timezone.now),
            current_period_end=factory.LazyFunction(
                lambda: timezone.now() + timezone.timedelta(days=30)
            ),
        )

        cancel_at_period_end_active = factory.Trait(
            status=UserSubscriptionStatus.ACTIVE,
            stripe_subscription_id=factory.Sequence(lambda n: f"sub_{n}"),
            started_at=factory.LazyFunction(timezone.now),
            current_period_start=factory.LazyFunction(timezone.now),
            current_period_end=factory.LazyFunction(
                lambda: timezone.now() + timezone.timedelta(days=30)
            ),
            cancel_at_period_end=True,
        )

        canceled = factory.Trait(
            status=UserSubscriptionStatus.CANCELED,
            stripe_subscription_id=factory.Sequence(lambda n: f"sub_{n}"),
            started_at=factory.LazyFunction(
                lambda: timezone.now() - timezone.timedelta(days=30)
            ),
            current_period_start=factory.LazyFunction(timezone.now),
            current_period_end=factory.LazyFunction(timezone.now),
            cancel_at_period_end=False,
            canceled_at=factory.LazyFunction(timezone.now),
            ended_at=factory.LazyFunction(timezone.now),
        )
