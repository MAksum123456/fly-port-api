from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")
TOKEN_REFRESH_URL = reverse("user:token_refresh")
TOKEN_VERIFY_URL = reverse("user:token_verify")
MANAGE_USER_URL = reverse("user:manage")


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class UserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_success(self):
        """Test creating user with valid payload is successful"""
        payload = {
            "email": "test@example.com",
            "password": "testpass123",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_email_required(self):
        """Test that email is required"""
        payload = {
            "email": "",
            "password": "testpass123",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_password_too_short(self):
        """Test that password must be more than 5 characters"""
        payload = {
            "email": "test2@example.com",
            "password": "123",
        }
        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    def test_create_token_for_user(self):
        """Test that a token is created for the user"""
        payload = {"email": "test@example.com", "password": "testpass123"}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Test token is not created if invalid credentials are given"""
        create_user(email="test@example.com", password="testpass123")
        payload = {"email": "test@example.com", "password": "wrongpass"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_token_no_user(self):
        """Test token is not created if user doesn't exist"""
        payload = {"email": "nouser@example.com", "password": "testpass123"}
        res = self.client.post(TOKEN_URL, payload)
        self.assertNotIn("access", res.data)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for users"""
        res = self.client.get(MANAGE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_profile(self):
        """Test retrieving profile for logged in user"""
        user = create_user(email="test@example.com", password="testpass123")
        self.client.force_authenticate(user=user)
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)
        self.assertEqual(res.data["is_staff"], user.is_staff)
        self.assertEqual(res.data["id"], user.id)

    def test_post_not_allowed_on_manage(self):
        """Test that POST is not allowed on the manage endpoint"""
        user = create_user(email="test@example.com", password="testpass123")
        self.client.force_authenticate(user=user)
        res = self.client.post(MANAGE_USER_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
