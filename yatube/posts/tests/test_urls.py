from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_for_all_users(self):
        """"Проверка доступности страниц для любого пользователя"""
        url_list = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.post.author}/',
            f'/posts/{self.post.pk}/'
        }
        for url in url_list:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_for_autorized_users(self):
        """Проверка доступности страниц для авторизованных пользователей"""
        url_list = {
            f'/posts/{self.post.pk}/edit/',
            '/create/'
        }
        for url in url_list:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_non_exist_url_is_not_found(self):
        """Проверка недоступности не существующих страниц"""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """Проверка соотвествия URL и шаблонов."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.post.author}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/post_create.html',
            f'/posts/{self.post.pk}/edit/': 'posts/post_create.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
