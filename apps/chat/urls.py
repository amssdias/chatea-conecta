from django.urls import path
from django.contrib.auth import views as auth_views

from .views import test_request

app_name = "chat"

urlpatterns = [
    path("testing/", test_request, name="test"),
]