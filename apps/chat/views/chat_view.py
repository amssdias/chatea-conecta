from django.shortcuts import render, redirect
from django.contrib import messages
from django.views import View


class ChatView(View):
    def post(self, request):
        username = request.POST.get("username")
        if not username:
            messages.error(request, "You need to put an username")
            # Redirect to home page
            return redirect("chat:home")

        return render(request, "chat.html", context={"username": username})

