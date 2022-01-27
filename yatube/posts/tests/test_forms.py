import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='User1')
        cls.user_2 = User.objects.create_user(username='User2')
        cls.group = Group.objects.create(
            title='Тестовое название группы',
            slug='test-group',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            text='тестовый комментарий',
            author=cls.user,
            post=cls.post
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.redirect_profile_page = reverse(
            'posts:profile', kwargs={'username': self.post.author}
        )
        self.redirect_post_detail_page = reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        )
        self.redirect_post_edit_page = reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}
        )
        self.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        self.uploaded_1 = SimpleUploadedFile(
            name='small.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.uploaded_2 = SimpleUploadedFile(
            name='small2.gif',
            content=self.small_gif,
            content_type='image/gif'
        )
        self.form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded_1
        }
        self.form_data_2 = {
            'text': 'Тестовый пост',
            'group': self.group.id,
            'image': self.uploaded_2
        }
        self.form_data_3 = {
            'text': 'Тест кеша',
        }

    def test_post_create_by_authorized(self):
        """Форма создает запись в Post только авторизованным пользователем"""
        post_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, self.redirect_profile_page)
        last_post = Post.objects.latest('id')
        self.assertTrue(
            Post.objects.filter(
                pk=last_post.pk,
                text=self.form_data['text'],
                group=self.form_data['group'],
                image='posts/small.gif'
            ).exists()
        )

    def test_post_create_by_not_authorized(self):
        post_count = Post.objects.count()
        self.client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)

    def post_editor(self, editor, text, is_edit, image):
        """функция для редактрования и проверки постов"""
        edited_post = {
            'text': text,
            'group': self.group.id,
            'image': image
        }
        response = editor.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=edited_post,
            follow=True
        )
        self.post.refresh_from_db()
        if is_edit:
            self.assertRedirects(response, self.redirect_post_detail_page)
            self.assertEqual(self.post.text, edited_post['text'])
            self.assertEqual(self.post.group.id, edited_post['group'])
            self.assertEqual(
                self.post.image.name,
                'posts/' + edited_post['image'].name
            )
        else:
            self.assertNotEqual(self.post.text, edited_post['text'])
            self.assertEqual(self.post.group.id, edited_post['group'])

    def test_post_edit(self):
        """Пост меняется при отправке формы только его автором"""
        different_editors_and_posts = {
            'author': [
                self.authorized_client,
                'Изменения поста его автором',
                True,
                self.uploaded_2
            ],
            'anonim': [
                self.client,
                'Изменение поста анонимом',
                False,
                self.uploaded_2
            ],
            'not author': [
                self.authorized_client_2,
                'Изменение поста не автором',
                False,
                self.uploaded_2
            ]
        }
        for author in different_editors_and_posts:
            self.post_editor(*different_editors_and_posts[author])

    def test_comment_create(self):
        """Комментировать посты может только авторизованный пользователь"""
        comment_count = Comment.objects.count()
        data = {'text': 'Тестовый комментарий'}
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=data,
            follow=True
        )
        last_comment = Comment.objects.latest('pk')
        self.assertTrue(
            Comment.objects.filter(
                pk=last_comment.pk,
                text=data['text']
            ).exists()
        )
