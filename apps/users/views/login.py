from django.conf import settings
from django.contrib.auth.views import LoginView
from django.urls import reverse

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY, ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.infrastructure.redis.sync_redis_service import RedisService


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)

        user = form.get_user()
        username = user.username
        user_id = str(user.pk)

        self._prepare_chat_user(username=username, user_id=user_id)

        response.set_cookie(
            "username",
            username,
            httponly=True,
            secure=settings.COOKIES_SECURE,
        )
        response.set_cookie(
            "user_id",
            user_id,
            httponly=True,
            secure=settings.COOKIES_SECURE,
        )

        return response

    def get_success_url(self):
        return reverse("chat:live-chat")

    def _prepare_chat_user(self, username: str, user_id: str):
        RedisService.add_to_set(REDIS_ALL_USERNAMES_KEY, username.lower())
        RedisService.set_unique(ID_TO_USERNAME_KEY.format(user_id=user_id), username)
        RedisService.set_unique(USERNAME_TO_UUID_KEY.format(username=username), user_id)
