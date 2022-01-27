from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus


User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_clietn = Client()

    def test_author_page(self):
        response = self.guest_clietn.get('/about/author/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_tech_page(self):
        response = self.guest_clietn.get('/about/tech/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
