from django.conf import settings

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View

from apps.chat.constants.redis_keys import REDIS_USERNAME_KEY
from apps.chat.utils.redis_connection import redis_connection


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


class ChatView(View):
    def get(self, request):
        username = self.request.COOKIES.get("username", "")
        if not username or not redis_connection.sismember(REDIS_USERNAME_KEY, username.lower()):
            response = redirect("chat:home")
            response.delete_cookie("username")
            return response
        return render(request, "chat/chat.html", context={"username": username, "groups": GROUPS})

    def post(self, request):
        username = request.POST.get("username")
        if not username:
            messages.error(request, "You need to put an username")
            # Redirect to home page
            return redirect("chat:home")

        # Check if username already exists in Redis
        lower_username = username.lower()
        if redis_connection.sismember(REDIS_USERNAME_KEY, lower_username):
            messages.error(request, "Username already taken")
            return redirect("chat:home")

        # Add the username to the Redis set
        redis_connection.sadd("asgi:usernames", lower_username)

        response = render(
            request, 
            "chat/chat.html", 
            context={
                "username": username,
                "groups": GROUPS,
            }
        )
        response.set_cookie("username", username, httponly=True, secure=settings.COOKIES_SECURE)
        return response
