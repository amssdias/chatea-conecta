from django.views.generic import TemplateView

from apps.chat.views.home_chat import presence_count


class ContentPageView(TemplateView):
    """A static content page that also needs the live headcount.

    Used by the FAQ, whose sidebar carries a "N in the room" card and a call to
    action. Pages without that card can stay on a plain TemplateView.
    """

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["n_persons"] = presence_count()
        return context
