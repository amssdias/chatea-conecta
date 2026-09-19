from django.conf import settings
from django.contrib.auth.views import LoginView
from django.urls import reverse

from apps.chat.services.register_user import register_user_on_redis


class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)

        user = form.get_user()
        username = user.username
        user_id = str(user.pk)

        register_user_on_redis(username=username, user_id=user_id)

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
