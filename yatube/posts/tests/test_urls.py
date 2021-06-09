from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.core.cache import cache

from ..models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.create_user(username='VG'),
        )
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-post-slug'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = PostURLTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_public_pages(self):
        """Публичные страницы доступна любому пользователю."""
        response_status = {
            HTTPStatus.OK: '/',
            HTTPStatus.OK: f'/group/{self.group.slug}/',
            HTTPStatus.OK: f'/{self.post.author}/',
            HTTPStatus.OK: f'/{self.post.author}/{self.post.id}/',
        }
        for response_s, adress in response_status.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, response_s)

    def test_404(self):
        """Возвращает 404 если страница не найдена."""
        response = self.guest_client.get('1234')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_new_post_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_post_url_redirect_anonymous(self):
        """Страница /new/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/new/')
        self.assertEqual(response.status_code, 302)

    def test_post_id_edit_anon_url(self):
        """Страница редактирования перенаправляет неавторизванного юзера."""
        response = self.guest_client.get(
            f'/{self.post.author}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_id_edit_url(self):
        """Страница редактирования недоступна другому юзеру."""
        self.user = User.objects.create_user(username='VGV')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            f'/{self.post.author}/{self.post.id}/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу '<str:username>/<int:post_id>/edit/'
         перенаправит анонимного пользователя на страницу поста.
        """
        response = self.guest_client.get(
            f'/{self.post.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/{self.post.author}/{self.post.id}/')

    def test_post_edit_url_redirect_other_user_on_post(self):
        """Страница по адресу '<str:username>/<int:post_id>/edit/'
         перенаправит другого пользователя на страницу поста.
        """
        self.user = User.objects.create_user(username='VGV')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get(
            f'/{self.post.author}/{self.post.id}/edit/', follow=True)
        self.assertRedirects(
            response, f'/{self.post.author}/{self.post.id}/')

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': '/',
            'new.html': '/new/',
            'group.html': f'/group/{self.group.slug}/',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
