from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.captcha import make_captcha_token
from apps.accounts.models import User, UserRole
from apps.accounts.serializers import _FAIL_PREFIX, _MAX_FAILURES, _LOCKOUT_SECONDS
from apps.core.models import Campus, CampusMembership


@override_settings(
    SECRET_KEY="test-secret-key-that-is-at-least-32-bytes-long",
    REST_FRAMEWORK={
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    },
)
class LoginCaptchaTests(APITestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.school = Campus.objects.create(name="Login Test School", code="LOGIN")
        self.user = User.objects.create_user(
            username="login.admin",
            password="Passw0rd!Admin1",
            role=UserRole.SCHOOL_ADMIN,
            school=self.school,
            is_staff=True,
        )
        CampusMembership.objects.create(
            campus=self.school,
            user=self.user,
            role="it_admin",
            is_primary=True,
            can_manage_users=True,
            can_configure_attendance=True,
        )

    # ── Captcha endpoint ──────────────────────────────────────────────────────

    def test_captcha_challenge_is_public_and_contains_question(self):
        response = self.client.get("/api/v1/auth/captcha/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("challenge_id", response.data)
        self.assertIn("expires_in", response.data)
        self.assertIn("question", response.data)
        # Plaintext code must NOT be present in the response.
        self.assertNotIn("code", response.data)
        # Question should look like "23 + 47 = ?" or "50 - 12 = ?"
        self.assertRegex(response.data["question"], r"^\d+ [+\-] \d+ = \?$")

    def test_captcha_does_not_expose_answer(self):
        """The numeric answer must not appear anywhere in the API response."""
        response = self.client.get("/api/v1/auth/captcha/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        question = response.data["question"]
        # Parse the question to find the expected answer.
        import re
        m = re.match(r"(\d+) ([+\-]) (\d+) = \?", question)
        self.assertIsNotNone(m)
        a, op, b = int(m.group(1)), m.group(2), int(m.group(3))
        answer = str(a + b) if op == "+" else str(a - b)
        # The raw answer string must not appear in challenge_id or expires_at.
        self.assertNotIn(answer, str(response.data.get("challenge_id", "")))

    # ── Login validation ──────────────────────────────────────────────────────

    def test_login_requires_valid_captcha(self):
        missing = self.client.post(
            "/api/v1/auth/token/",
            {"username": "login.admin", "password": "Passw0rd!Admin1"},
            format="json",
        )
        invalid = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "999",
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
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["username"], "login.admin")

    def test_captcha_token_cannot_be_reused(self):
        """A valid captcha token is consumed after one successful use."""
        token = make_captcha_token("25")
        payload = {
            "username": "login.admin",
            "password": "Passw0rd!Admin1",
            "captcha_id": token,
            "captcha_answer": "25",
        }
        first = self.client.post("/api/v1/auth/token/", payload, format="json")
        second = self.client.post("/api/v1/auth/token/", payload, format="json")

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        # Second attempt must fail because the captcha token was already consumed.
        self.assertEqual(second.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_rejects_inactive_school(self):
        self.school.status = "inactive"
        self.school.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_inactive_school_error_does_not_reveal_school_name(self):
        """Error message must not expose the school name or status."""
        self.school.status = "inactive"
        self.school.save(update_fields=["status", "updated_at"])

        response = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )

        error_text = str(response.data)
        self.assertNotIn(self.school.name, error_text)
        self.assertNotIn("inactive", error_text)

    # ── Brute-force lockout ───────────────────────────────────────────────────

    def test_account_locked_after_max_failures(self):
        from django.core.cache import cache

        cache.clear()
        username = "login.admin"

        for _ in range(_MAX_FAILURES):
            self.client.post(
                "/api/v1/auth/token/",
                {
                    "username": username,
                    "password": "WrongPassword!1",
                    "captcha_id": make_captcha_token("25"),
                    "captcha_answer": "25",
                },
                format="json",
            )

        # The next attempt should be refused due to lockout.
        locked_response = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": username,
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )
        self.assertEqual(locked_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("locked", str(locked_response.data).lower())

        cache.clear()

    def test_successful_login_clears_failure_counter(self):
        from django.core.cache import cache

        cache.clear()
        username = "login.admin"

        # Two failures
        for _ in range(2):
            self.client.post(
                "/api/v1/auth/token/",
                {
                    "username": username,
                    "password": "WrongPassword!1",
                    "captcha_id": make_captcha_token("25"),
                    "captcha_answer": "25",
                },
                format="json",
            )
        self.assertEqual(int(cache.get(f"{_FAIL_PREFIX}{username}") or 0), 2)

        # Successful login clears the counter
        self.client.post(
            "/api/v1/auth/token/",
            {
                "username": username,
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )
        self.assertEqual(int(cache.get(f"{_FAIL_PREFIX}{username}") or 0), 0)

        cache.clear()

    # ── Logout ────────────────────────────────────────────────────────────────

    def test_logout_blacklists_refresh_token(self):
        login = self.client.post(
            "/api/v1/auth/token/",
            {
                "username": "login.admin",
                "password": "Passw0rd!Admin1",
                "captcha_id": make_captcha_token("25"),
                "captcha_answer": "25",
            },
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        access = login.data["access"]
        refresh = login.data["refresh"]

        # Logout
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        logout_response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # The blacklisted refresh token must no longer produce new access tokens.
        refresh_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": refresh},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_requires_authentication(self):
        response = self.client.post(
            "/api/v1/auth/logout/",
            {"refresh": "invalid-token"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SuperAdminProtectionTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username="protected.super",
            password="Passw0rd!Admin1",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=self.super_admin)

    def test_super_admin_cannot_be_disabled_or_deleted(self):
        disable_response = self.client.patch(
            f"/api/v1/auth/users/{self.super_admin.id}/",
            {"is_active": False},
            format="json",
        )
        delete_response = self.client.delete(f"/api/v1/auth/users/{self.super_admin.id}/")

        self.assertEqual(disable_response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(delete_response.status_code, status.HTTP_403_FORBIDDEN)

        self.super_admin.refresh_from_db()
        self.assertTrue(self.super_admin.is_active)
        self.assertEqual(self.super_admin.role, UserRole.SUPER_ADMIN)

    def test_super_admin_cannot_be_modified_by_another_user(self):
        other_super_admin = User.objects.create_user(
            username="other.super",
            password="Passw0rd!Admin1",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_authenticate(user=other_super_admin)

        response = self.client.patch(
            f"/api/v1/auth/users/{self.super_admin.id}/",
            {"first_name": "Tampered"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.super_admin.refresh_from_db()
        self.assertEqual(self.super_admin.first_name, "")


class PasswordPolicyTests(APITestCase):
    def setUp(self):
        self.super_admin = User.objects.create_user(
            username="pw.policy.super",
            password="Passw0rd!Admin1",
            role=UserRole.SUPER_ADMIN,
            is_staff=True,
            is_superuser=True,
        )
        self.school = Campus.objects.create(name="PW Test School", code="PWTEST")
        self.client.force_authenticate(user=self.super_admin)

    def _create_payload(self, password: str) -> dict:
        return {
            "username": "newuser.test",
            "password": password,
            "role": "school_admin",
            "school": self.school.id,
            "campus_ids": [self.school.id],
        }

    def test_rejects_short_password(self):
        response = self.client.post(
            "/api/v1/auth/users/",
            self._create_payload("Short1!"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_password_without_uppercase(self):
        response = self.client.post(
            "/api/v1/auth/users/",
            self._create_payload("nouppercase1!"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_password_without_special_char(self):
        response = self.client.post(
            "/api/v1/auth/users/",
            self._create_payload("NoSpecial1234"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_accepts_strong_password(self):
        response = self.client.post(
            "/api/v1/auth/users/",
            self._create_payload("Str0ng!Pass#2"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
