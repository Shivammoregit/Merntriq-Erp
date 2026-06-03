from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.captcha import make_captcha_token
from apps.accounts.models import User, UserRole


@override_settings(SECRET_KEY="test-secret-key-that-is-at-least-32-bytes")
class LoginCaptchaTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="login.admin",
            password="Passw0rd!123",
            role=UserRole.ADMIN,
            is_staff=True,
        )

    def test_captcha_challenge_is_public_and_contains_numeric_code(self):
        response = self.client.get("/api/v1/auth/captcha/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("challenge_id", response.data)
        self.assertIn("expires_in", response.data)
        self.assertIn("code", response.data)
        self.assertRegex(response.data["code"], r"^\d{5}$")

    def test_login_requires_valid_captcha(self):
        missing = self.client.post(
            "/api/v1/auth/token/",
            {"username": "login.admin", "password": "Passw0rd!123"},
            format="json",
        )
        invalid = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!123",
                "captcha_id": make_captcha_token("73941"),
                "captcha_answer": "WRONG",
            },
            format="json",
        )

        self.assertEqual(missing.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_accepts_valid_captcha(self):
        response = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!123",
                "captcha_id": make_captcha_token("73941"),
                "captcha_answer": "73941",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["username"], "login.admin")
