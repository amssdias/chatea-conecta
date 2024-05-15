from django.conf import settings

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View


class ChatView(View):
    def get(self, request):
        username = self.request.COOKIES.get("username")
        if not username:
            return redirect("chat:home")

        return render(request, "chat/chat.html", context={"username": username})

    def post(self, request):
        username = request.POST.get("username")
        if not username:
            messages.error(request, "You need to put an username")
            # Redirect to home page
            return redirect("chat:home")

        response = render(request, "chat.html", context={"username": username})
        response.set_cookie("username", username, httponly=True, secure=settings.COOKIES_SECURE)
        return response
