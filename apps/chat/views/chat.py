from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.services import RedisService

GROUPS = [
    ("Galicia", "galicia"),
    ("Asturias", "asturias"),
    ("Cantabria", "cantabria"),
    ("País Vasco", "pais_vasco"),
    ("Navarra", "navarra"),
    ("La Rioja", "la_rioja"),
    ("Castilla y León", "castilla_leon"),
    ("Aragón", "aragon"),
    ("Cataluña", "cataluna"),
    ("Madrid", "madrid"),
    ("Extremadura", "extremadura"),
    ("Castilla-La Mancha", "castilla_la_mancha"),
    ("Comunidad Valenciana", "valencia"),
    ("Región de Murcia", "region_murcia"),
    ("Andalucía", "andalucia"),
]

User = get_user_model()


class ChatView(View):
    def get(self, request):
        username = self.request.COOKIES.get("username", "")
        if not username or not RedisService.is_member(
            REDIS_USERNAME_KEY, username.lower()
        ):
            response = redirect("chat:home")
            response.delete_cookie("username")
            return response
        return render(
            request, "chat/chat.html", context={"username": username, "groups": None}
        )

    def post(self, request):
        username = request.POST.get("username", "").strip()
        if not username:
            messages.error(request, _("You need to put an username"))
            # Redirect to home page
            return redirect("chat:home")

        # Check if username already exists in Redis
        lower_username = username.lower()
        if (
            RedisService.is_member(REDIS_USERNAME_KEY, lower_username) or
            User.objects.filter(username__iexact=lower_username).exists()
        ):
            messages.error(request, _("Username already taken"))
            return redirect("chat:home")

        # Add the username to the Redis set
        RedisService.add_to_set(REDIS_USERNAME_KEY, lower_username)

        response = render(
            request,
            "chat/chat.html",
            context={
                "username": username,
                "groups": None,
            },
        )
        response.set_cookie(
            "username", username, httponly=True, secure=settings.COOKIES_SECURE
        )
        return response
