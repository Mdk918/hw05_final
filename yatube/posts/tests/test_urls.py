from django.contrib.auth import get_user_model
from django.test import TestCase, Client

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

    def test_homepage(self):
        """Страница / доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_404(self):
        """Возвращает 404 если страница не найдена."""
        response = self.guest_client.get('1234')
        self.assertEqual(response.status_code, 404)

    def test_new_post_url_exists_at_desired_location(self):
        """Страница /new/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/new/')
        self.assertEqual(response.status_code, 200)

    def test_new_post_url_redirect_anonymous(self):
        """Страница /new/ перенаправляет анонимного пользователя."""
        response = self.guest_client.get('/new/')
        self.assertEqual(response.status_code, 302)

    def test_group_url(self):
        """Страница group доступна любому пользователю."""
        response = self.guest_client.get('/group/test-post-slug/')
        self.assertEqual(response.status_code, 200)

    def test_profile_url(self):
        """Страница profile доступна любому пользователю."""
        response = self.guest_client.get('/VG/')
        self.assertEqual(response.status_code, 200)

    def test_post_id_url(self):
        """Страница отдельного поста доступна любому пользователю."""
        response = self.guest_client.get('/VG/1/')
        self.assertEqual(response.status_code, 200)

    def test_post_id_edit_anon_url(self):
        """Страница редактирования перенаправляет неавторизванного юзера."""
        response = self.guest_client.get('/VG/1/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_id_edit_url(self):
        """Страница редактирования недоступна другому юзеру."""
        self.user = User.objects.create_user(username='VGV')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/VG/1/edit/')
        self.assertEqual(response.status_code, 302)

    def test_post_edit_url_redirect_anonymous_on_admin_login(self):
        """Страница по адресу '<str:username>/<int:post_id>/edit/'
         перенаправит анонимного пользователя на страницу поста.
        """
        response = self.guest_client.get('/VG/1/edit/', follow=True)
        self.assertRedirects(
            response, '/VG/1/')

    def test_post_edit_url_redirect_other_user_on_post(self):
        """Страница по адресу '<str:username>/<int:post_id>/edit/'
         перенаправит другого пользователя на страницу поста.
        """
        self.user = User.objects.create_user(username='VGV')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        response = self.authorized_client.get('/VG/1/edit/', follow=True)
        self.assertRedirects(
            response, '/VG/1/')

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': '/',
            'new.html': '/new/',
            'group.html': '/group/test-post-slug/',
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
