from django.urls import path

from apps.users import views

app_name = "users"

urlpatterns = [
    path("signup/", views.SignUpView.as_view(), name="signup"),
    path("login/", views.CustomLoginView.as_view(), name="login"),
    path("logout/", views.CloseChatSessionView.as_view(), name="logout"),
]
