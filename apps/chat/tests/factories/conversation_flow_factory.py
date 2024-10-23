import factory

from apps.chat.models import ConversationFlow
from apps.chat.tests.factories.topic_factory import TopicFactory


class ConversationFlowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConversationFlow

    message = factory.Faker("sentence")
    topic = factory.SubFactory(TopicFactory)
