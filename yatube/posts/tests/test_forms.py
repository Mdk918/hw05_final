import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Заголовок',
            description='Тестовый текст',
            slug='test-post-slug')

        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.create_user(username='VG'),
            group=Group.objects.get(title='Заголовок')
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = PostsFormTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_anon_user_create_post(self):
        """Страница созадния новой записи перенаправит анонима на
        страницу авторизации."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
        }
        response = self.guest_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/new/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_create_post_with_image(self):
        """Создание новой записи с изображением."""
        posts_count = Post.objects.count()
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
            content_type='image/gif')

        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=None,
                image='posts/small.gif').exists())

    def test_edit_post(self):
        """Редактирование записи."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={'username': f'{self.user}',
                                         'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': f'{self.user}',
                            'post_id': f'{self.post.id}'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_author_edit_post(self):
        """Друго пользователь не может отредактировать чужой пост."""
        self.author = User.objects.create_user(username='VG1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        post_user = PostsFormTests.post
        form_data = {
            'text': 'Тестовый',
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={'username': f'{self.user}',
                                         'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'post', kwargs={'username': f'{self.user}',
                            'post_id': f'{self.post.id}'}))
        self.assertEqual(PostsFormTests.post, post_user)
        self.assertEqual(response.status_code, HTTPStatus.OK)
