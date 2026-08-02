"""
End to end guest session flow, exercising the real Redis service code against an
in-memory stand-in for the Redis client.

The unit tests mock the ownership check out; these tests keep it in, so the
signed cookie, the ID <-> username mapping and the nickname availability rules
are checked together.
"""

from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.chat.constants.redis_keys import ID_TO_USERNAME_KEY, USERNAME_TO_UUID_KEY
from apps.chat.services.guest_session import GUEST_SESSION_COOKIE, issue_guest_token


class InMemoryRedis:
    """The handful of Redis commands RedisService actually issues."""

    def __init__(self):
        self.values = {}
        self.sets = {}

    def set(self, name=None, value=None, ex=None, nx=False):
        if nx and name in self.values:
            return None

        self.values[name] = str(value)
        return True

    def get(self, key):
        return self.values.get(key)

    def delete(self, key):
        return int(self.values.pop(key, None) is not None)

    def expire(self, key, ttl):
        return key in self.values

    def incr(self, key):
        self.values[key] = str(int(self.values.get(key, 0)) + 1)
        return int(self.values[key])

    def sadd(self, key, *values):
        members = self.sets.setdefault(key, set())
        new = {value for value in values if value not in members}
        members.update(new)
        return len(new)

    def srem(self, key, value):
        members = self.sets.setdefault(key, set())
        removed = value in members
        members.discard(value)
        return int(removed)

    def sismember(self, key, value):
        return value in self.sets.get(key, set())

    def scard(self, key):
        return len(self.sets.get(key, set()))

    def expire_key(self, key):
        """Test helper: simulate a key reaching its TTL."""
        self.values.pop(key, None)


@override_settings(COOKIES_SECURE=False)
class GuestSessionFlowTests(TestCase):
    def setUp(self):
        self.url = reverse("chat:live-chat")
        self.home_url = reverse("chat:home")
        self.redis = InMemoryRedis()

        patcher = patch(
            "apps.chat.infrastructure.redis.sync_redis_service.RedisService.redis_client",
            self.redis,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def join_as_guest(self, username, client=None):
        client = client or self.client
        return client.post(self.url, data={"username": username})

    def test_guest_can_join_and_come_back(self):
        response = self.join_as_guest("alice")

        self.assertEqual(response.status_code, 200)
        user_id = response.context["user_id"]

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["username"], "alice")
        self.assertEqual(response.context["user_id"], user_id)

    def test_registration_records_the_ownership_mapping(self):
        response = self.join_as_guest("Alice")
        user_id = response.context["user_id"]

        self.assertEqual(
            self.redis.get(USERNAME_TO_UUID_KEY.format(username="alice")),
            user_id,
        )
        self.assertEqual(
            self.redis.get(ID_TO_USERNAME_KEY.format(user_id=user_id)),
            "Alice",
        )

    def test_forged_plaintext_cookies_do_not_grant_a_session(self):
        """Regression: this pair of cookies used to be enough to become alice."""
        self.join_as_guest("alice")

        attacker = self.client_class()
        attacker.cookies["username"] = "alice"
        attacker.cookies["user_id"] = "u_00001"

        response = attacker.get(self.url)

        self.assertRedirects(response, self.home_url)

    def test_a_token_cannot_be_minted_for_someone_elses_nickname(self):
        self.join_as_guest("alice")

        attacker = self.client_class()
        attacker.cookies[GUEST_SESSION_COOKIE] = "alice:u_00001"

        response = attacker.get(self.url)

        self.assertRedirects(response, self.home_url)

    def test_a_stolen_id_is_rejected_because_the_mapping_disagrees(self):
        """
        Even holding a validly signed token, pairing it with another guest's id
        fails: that id is mapped to a different nickname.
        """
        alice = self.join_as_guest("alice")
        alice_id = alice.context["user_id"]

        attacker = self.client_class()
        self.join_as_guest("mallory", client=attacker)
        attacker.cookies[GUEST_SESSION_COOKIE] = issue_guest_token("mallory", alice_id)

        response = attacker.get(self.url)

        self.assertRedirects(response, self.home_url)
        self.assertEqual(
            self.redis.get(ID_TO_USERNAME_KEY.format(user_id=alice_id)),
            "alice",
        )

    def test_session_is_readopted_when_the_mapping_expired(self):
        response = self.join_as_guest("alice")
        user_id = response.context["user_id"]

        self.redis.expire_key(USERNAME_TO_UUID_KEY.format(username="alice"))
        self.redis.expire_key(ID_TO_USERNAME_KEY.format(user_id=user_id))

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user_id"], user_id)

    def test_nickname_taken_over_after_logout_locks_out_the_old_token(self):
        self.join_as_guest("alice")
        old_token = self.client.cookies[GUEST_SESSION_COOKIE].value

        self.client.post(reverse("users:logout"))

        newcomer = self.client_class()
        self.join_as_guest("alice", client=newcomer)

        stale = self.client_class()
        stale.cookies[GUEST_SESSION_COOKIE] = old_token

        response = stale.get(self.url)

        self.assertRedirects(response, self.home_url)

    def test_nickname_is_rejected_while_another_guest_holds_it(self):
        self.join_as_guest("alice")

        newcomer = self.client_class()
        response = self.join_as_guest("alice", client=newcomer)

        self.assertRedirects(response, self.home_url)
