import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post
from yatube.settings import PAGE_COUNT

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user_1 = User.objects.create_user(username='User1')
        cls.user_2 = User.objects.create_user(username='User2')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.group_2 = Group.objects.create(
            title='Тестовое название группы 2',
            slug='test-group-2',
            description='Тестовое описание группы 2'
        )
        for i in range(13):
            cls.post = Post.objects.create(
                text='Тестовый текст поста',
                author=cls.user_1,
                group=cls.group
            )
        for i in range(13):
            cls.post_2 = Post.objects.create(
                text='Тестовый текст поста 2',
                author=cls.user_2,
                group=cls.group_2,
                image=uploaded
            )
        cls.comment = Comment.objects.create(
            post=Post.objects.get(pk=cls.post.pk),
            author=cls.user_1,
            text='Тестовый комментарий'
        )
        cls.guest_client = Client()
        cls.following = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_2
        )
        cls.follow_cnt = Follow.objects.count()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user_1)
        self.another_authorized_client = Client()
        self.another_authorized_client.force_login(self.user_2)
        self.padgination_const = PAGE_COUNT

    def test_posts_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон"""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/post_create.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def check_context_is_correct(self, response, context, is_paginated=True):
        """Проверка первого элемента в контексте"""
        if not is_paginated:
            self.assertEqual(
                response.context.get(context).text,
                self.post.text
            )
            self.assertEqual(
                response.context.get(context).author,
                self.post.author
            )
            self.assertEqual(
                response.context.get(context).group,
                self.post.group
            )
            self.assertEqual(
                response.context.get(context).image,
                self.post.image
            )
        else:
            first_object = response.context[context][0]
            post_text_0 = first_object.text
            post_author_0 = first_object.author
            post_image_0 = first_object.image
            self.assertEqual(post_text_0, self.post_2.text)
            self.assertEqual(post_author_0, self.post_2.author)
            self.assertEqual(post_image_0, self.post_2.image)
            if self.post_2.group:
                post_group_0 = first_object.group
                self.assertEqual(post_group_0, self.post_2.group)
            elif self.post_2.image:
                post_image_0 = first_object.image
                self.assertEqual(post_image_0, self.post_2.image)

    def test_index__page_show_correct_context_and_paginate(self):
        """Шаблон index сформирован с правильным контекстом"""
        posts_cnt = Post.objects.count()
        last_page_num = int((posts_cnt / self.padgination_const) + 1)
        response = self.authorized_client.get(reverse('posts:index'))
        response_last_page = self.authorized_client.get(
            reverse('posts:index') + '?page=' + str(last_page_num)
        )
        last_page_posts_cnt = (
            posts_cnt % response.context['page_obj'].paginator.per_page
        )
        self.check_context_is_correct(response, 'page_obj')
        self.assertEqual(
            len(response.context['page_obj']), self.padgination_const
        )
        self.assertEqual(
            len(response_last_page.context['page_obj']), last_page_posts_cnt
        )

    def test_group_list_page_show_correct_contextand_paginate(self):
        """Шаблон group_list сформирован с правильным контекстом"""
        posts_cnt = Post.objects.filter(group=self.group_2).count()
        last_page_num = int((posts_cnt / self.padgination_const) + 1)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug})
        )
        response_last_page = self.client.get(
            reverse(
                ('posts:group_list'), kwargs={'slug': self.group_2.slug}
            ) + '?page=' + str(last_page_num)
        )
        last_page_posts_cnt = (
            posts_cnt % response.context['page_obj'].paginator.per_page
        )
        self.check_context_is_correct(response, 'page_obj')
        # проверяю что пост не попал в группу, для которой не был предназначен.
        self.assertNotEqual(
            response.context['page_obj'][0].text, self.post.text
        )
        for post in response.context['page_obj']:
            self.assertEqual(post.group, self.post_2.group)
        self.assertEqual(
            len(response.context['page_obj']), self.padgination_const
        )
        self.assertEqual(
            len(response_last_page.context['page_obj']), last_page_posts_cnt
        )

    def test_profile_page_show_correct_contextand_paginate(self):
        """Шаблон profie сформирован с правильным контекстом"""
        posts_cnt = Post.objects.filter(author=self.user_2).count()
        last_page_num = int((posts_cnt / self.padgination_const) + 1)
        response = self.client.get(
            reverse(('posts:profile'), kwargs={'username': self.user_2})
        )
        response_last_page = self.client.get(
            reverse(
                ('posts:profile'), kwargs={'username': self.user_2}
            ) + '?page=' + str(last_page_num)
        )
        last_page_posts_cnt = (
            posts_cnt % response.context['page_obj'].paginator.per_page
        )
        self.check_context_is_correct(response, 'page_obj')
        for post in response.context['page_obj']:
            self.assertEqual(post.author, self.post_2.author)
        self.assertEqual(
            len(response.context['page_obj']), self.padgination_const
        )
        self.assertEqual(
            len(response_last_page.context['page_obj']), last_page_posts_cnt
        )

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        comment = response.context.get('comments')[0]
        self.check_context_is_correct(response, 'post', False)
        self.assertEqual(comment, self.comment)

    def check_template_is_correct(self, response):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_create_post_page_show_corrext_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.check_template_is_correct(response)

    def test_edit_post_page_show_corrext_context(self):
        """Шаблон post_create сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        self.check_template_is_correct(response)

    def test_cache_index(self):
        """Проверка кеширования главной страницы index."""
        response = self.client.get(reverse('posts:index'))
        content_1 = response.content
        Post.objects.all().delete()
        response_2 = self.client.get(reverse('posts:index'))
        content_2 = response_2.content
        self.assertEqual(content_1, content_2)
        cache.clear()
        response_3 = self.client.get(reverse('posts:index'))
        content_3 = response_3.content
        self.assertNotEqual(content_1, content_3)

    def test_following_authorized_only(self):
        """Проверка подписок авторизованным пользователем"""
        # попытка подписки неавторизованным пользователем
        self.client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user_1})
        )
        self.assertEqual(Follow.objects.count(), self.follow_cnt)
        self.another_authorized_client.post(
            reverse('posts:profile_follow', kwargs={'username': self.user_1})
        )
        self.assertTrue(
            Follow.objects.filter(
                user=self.user_2,
                author=self.user_1
            ).exists()
        )

    def test_unfollowing(self):
        """Проверка отписки от автора"""
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={'username': self.user_2})
        )
        self.assertFalse(
            Follow.objects.filter(
                user=self.user_1,
                author=self.user_2
            ).exists()
        )

    def test_follower_context(self):
        """Проверка ленты фоловеров"""
        Follow.objects.create(
            user=self.user_1,
            author=self.user_1
        )
        Follow.objects.create(
            user=self.user_2,
            author=self.user_2
        )
        post = Post.objects.create(
            text='Проверка ленты подписчика',
            author=self.user_1
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        new_post = response.context['page_obj'][0]
        self.assertEqual(post.text, new_post.text)
        response_2 = self.another_authorized_client.get(
            reverse('posts:follow_index')
        )
        new_post_2 = response_2.context['page_obj'][0]
        self.assertNotEqual(post.text, new_post_2.text)
