from django.conf import settings
from django.http import Http404

ACCOUNT_NAMESPACES = {"users", "subscriptions"}

# django.contrib.auth.urls is included without a namespace. The admin reuses
# some of these names inside its own namespace and must stay reachable.
ACCOUNT_URL_NAMES = {
    "stripe_webhook",
    "login",
    "logout",
    "password_change",
    "password_change_done",
    "password_reset",
    "password_reset_done",
    "password_reset_confirm",
    "password_reset_complete",
}

# Guests leave the chat through this view, so it is not an account-only route.
ALWAYS_OPEN_VIEW_NAMES = {"users:logout"}


class AccountsFlagMiddleware:
    """
    Answer 404 on account and billing routes while ACCOUNTS_ENABLED is off.

    The routes stay in the URLconf so templates can still reverse them: a link
    that was not hidden leads to a 404 instead of breaking the page it is on.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if settings.ACCOUNTS_ENABLED:
            return None

        if self._is_account_route(request.resolver_match):
            raise Http404

        return None

    @staticmethod
    def _is_account_route(match):
        if match.view_name in ALWAYS_OPEN_VIEW_NAMES:
            return False

        if not match.namespaces:
            return match.url_name in ACCOUNT_URL_NAMES

        return bool(ACCOUNT_NAMESPACES.intersection(match.namespaces))
