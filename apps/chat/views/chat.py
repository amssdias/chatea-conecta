from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.utils.translation import gettext_lazy as _
from django.views import View

from apps.chat.constants.redis_keys import REDIS_ALL_USERNAMES_KEY
from apps.chat.constants.username import USERNAME_REGEX
from apps.chat.infrastructure.redis.sync_redis_service import RedisService
from apps.chat.services.guest_session import (
    GUEST_SESSION_COOKIE,
    claim_guest_identity,
    issue_guest_token,
    read_guest_token,
)
from apps.chat.services.register_user import register_user_on_redis

User = get_user_model()


class ChatView(View):
    template_name = "chat/chat.html"
    home_route = "chat:home"

    username_cookie_name = "username"
    user_id_cookie_name = "user_id"

    def get(self, request):
        if request.user.is_authenticated:
            return self._register_and_render_chat(
                request=request,
                username=request.user.username,
                user_id=request.user.id,
                set_cookies=True,
            )

        username, user_id = self._get_cookie_user_data(request)

        if not self._has_valid_guest_session(username, user_id):
            return self._redirect_home_and_clear_cookies()

        return self._register_and_render_chat(
            request=request,
            username=username,
            user_id=user_id,
            is_guest=True,
        )

    def post(self, request):
        if request.user.is_authenticated:
            return self._register_and_render_chat(
                request=request,
                username=request.user.username,
                user_id=request.user.id,
            )

        username = self._get_submitted_username(request)
        validation_error = self._validate_guest_username(username)

        if validation_error:
            return self._redirect_home_with_error(request, validation_error)

        return self._register_and_render_chat(
            request=request,
            username=username,
            user_id=None,
            is_guest=True,
        )

    def _register_and_render_chat(self, request, username, user_id=None, is_guest=False):
        redis_user_id = register_user_on_redis(username, user_id=user_id)

        response = render(
            request,
            self.template_name,
            context=self._build_context(
                username=username,
                user_id=redis_user_id,
                is_user_pro=(request.user.is_authenticated and request.user.is_pro),
            ),
        )

        if is_guest:
            self._set_guest_session_cookie(request, response, username, redis_user_id)
        else:
            self._set_chat_cookies(response, username, redis_user_id)

        return self._add_noindex_header(response)

    def _build_context(self, username, user_id, is_user_pro=False):
        return {
            "username": username,
            "user_id": user_id,
            "is_user_pro": is_user_pro,
            "groups": None,
        }

    def _get_submitted_username(self, request):
        return request.POST.get("username", "").strip()

    def _get_guest_session_data(self, request):
        identity = read_guest_token(
            request.COOKIES.get(self.guest_session_cookie_name, "")
        )

        if identity is None:
            return "", ""

        return identity

    def _validate_guest_username(self, username):
        if not username:
            return _("You need to put an username")

        if not USERNAME_REGEX.fullmatch(username):
            return _("Username must be 3-20 characters and can only contain letters, numbers, '_' and '-'")

        if self._username_already_exists(username):
            return _("Username already taken")

        return None

    def _username_already_exists(self, username):
        return (
                RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username)
                or User.objects.filter(username__iexact=username).exists()
        )

    def _has_valid_guest_session(self, username, user_id):
        return bool(
            username
            and user_id
            and RedisService.is_member(REDIS_ALL_USERNAMES_KEY, username)
        )

    def _redirect_home_with_error(self, request, error_message):
        messages.error(request, error_message)
        return self._add_noindex_header(redirect(self.home_route))

    def _redirect_home_and_clear_cookies(self):
        response = redirect(self.home_route)
        response.delete_cookie(self.username_cookie_name)
        response.delete_cookie(self.user_id_cookie_name)
        return self._add_noindex_header(response)

    def _set_chat_cookies(self, response, username, user_id):
        cookie_options = {
            "httponly": True,
            "secure": settings.COOKIES_SECURE,
            "samesite": "Lax",
        }

        response.set_cookie(self.username_cookie_name, username, **cookie_options)
        response.set_cookie(self.user_id_cookie_name, user_id, **cookie_options)

    @staticmethod
    def _add_noindex_header(response):
        response["X-Robots-Tag"] = "noindex, nofollow"
        return response
