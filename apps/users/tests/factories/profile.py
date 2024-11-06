import factory
from faker import Faker

from apps.users.models import Profile
from apps.users.tests.factories.user_factory import UserFactory

fake = Faker()


class ProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Profile

    user = factory.SubFactory(UserFactory)
    gender = factory.Faker("random_element", elements=[choice[0] for choice in Profile.GENDERS])
    link = None

    @factory.lazy_attribute
    def link(self):
        return None  # Default value to ensure no URL unless requested

    @factory.post_generation
    def with_link(self, create, extracted, **kwargs):
        # If `with_link=True` is passed, `extracted` will be True, so generate a random URL.
        if extracted:
            self.link = fake.url()  # Generate a random URL
