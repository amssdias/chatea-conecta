from django.urls import path

from apps.users import views

app_name = "users"

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
]