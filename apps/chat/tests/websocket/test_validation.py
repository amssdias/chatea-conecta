from django.test import SimpleTestCase

from apps.chat.websocket.exceptions import WebSocketValidationError
from apps.chat.websocket.validation import validate_group_payload


class ValidateGroupPayloadTests(SimpleTestCase):
    def test_returns_normalized_group(self):
        data = {"group": "  My-Group  "}

        result = validate_group_payload(data)

        self.assertEqual(result, "my-group")

    def test_raises_error_when_group_is_missing(self):
        data = {}

        with self.assertRaisesMessage(WebSocketValidationError, "Invalid group"):
            validate_group_payload(data)

    def test_raises_error_when_group_is_none(self):
        data = {"group": None}

        with self.assertRaisesMessage(WebSocketValidationError, "Invalid group"):
            validate_group_payload(data)

    def test_raises_error_when_group_is_not_string(self):
        data = {"group": 123}

        with self.assertRaisesMessage(WebSocketValidationError, "Invalid group"):
            validate_group_payload(data)

    def test_raises_error_when_group_is_empty_string(self):
        data = {"group": ""}

        with self.assertRaisesMessage(WebSocketValidationError, "Missing group"):
            validate_group_payload(data)

    def test_raises_error_when_group_only_has_spaces(self):
        data = {"group": "   "}

        with self.assertRaisesMessage(WebSocketValidationError, "Missing group"):
            validate_group_payload(data)
