"""
Automated Test Suite for Accounts app: registration, login, logout, and profile.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class AccountsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="student_cse",
            email="student@univ.edu",
            password="SecurePassword2026!"
        )

    def test_user_registration_success(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newstudent',
            'email': 'new@univ.edu',
            'password1': 'NewPass1234!',
            'password2': 'NewPass1234!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newstudent').exists())

    def test_user_registration_password_mismatch(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'mismatchuser',
            'email': 'mis@univ.edu',
            'password1': 'Password123!',
            'password2': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_user_login_valid(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_cse',
            'password': 'SecurePassword2026!'
        })
        self.assertEqual(response.status_code, 302)

    def test_user_login_invalid(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student_cse',
            'password': 'WrongPassword!'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_user_logout(self):
        self.client.login(username='student_cse', password='SecurePassword2026!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)
