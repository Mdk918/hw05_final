import shutil
import tempfile

from django.core.cache import cache
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


def context_equal(self, first_object):
    post_text_0 = first_object.text
    post_pub_date_0 = first_object.pub_date
    post_author_0 = first_object.author
    post_image_0 = first_object.image
    self.assertEqual(post_text_0, first_object.text)
    self.assertEqual(post_pub_date_0, first_object.pub_date)
    self.assertEqual(post_author_0, first_object.author)
    self.assertEqual(post_image_0, first_object.image)


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostImage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B')
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-post-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.create_user(username='VG'),
            pub_date='Date',
            image=uploaded,
            group=Group.objects.get(title='Заголовок группы')
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = PostImage.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (
                reverse('group', kwargs={'slug': f'{self.group.slug}'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_new_post_page_shows_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_edit_shows_correct_context(self):
        """Шаблон new_post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={'username': f'{self.post.author}',
                                         'post_id': f'{self.post.id}'}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test__page_index_contains_records(self):
        "Запись с указанной группой отображается на главной"
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test__page_group_contains_records(self):
        "Запись с указанной группой отображается в группе"
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': f'{PostImage.group.slug}'}))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test__page_other_group_no_contains_records(self):
        "Запись с указанной группой не отображается в другой группе"
        group = Group.objects.create(
            title='Заголовок',
            description='Тестовый текст',
            slug='test-post-slug_other'
        )
        Post.objects.create(
            text='Тестовый',
            author=User.objects.get(username='VG'),
            group=Group.objects.get(title='Заголовок')
        )
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': f'{group.slug}'}))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def context_equal(self):
        post_text_0 = self.text
        post_pub_date_0 = self.pub_date
        post_author_0 = self.author
        post_image_0 = self.image
        self.assertEqual(post_text_0, self.text)
        self.assertEqual(post_pub_date_0, self.pub_date)
        self.assertEqual(post_author_0, self.author)
        self.assertEqual(post_image_0, self.image)

    def test_index_image_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        context_equal(self, first_object)

    def test_profile_image_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={
                'username': f'{PostImage.post.author}'}))
        first_object = response.context['page'][0]
        context_equal(self, first_object)

    def test_post_id_page_image_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': f'{PostImage.post.author}',
                                    'post_id': f'{PostImage.post.id}'}))
        first_object = response.context['post']
        context_equal(self, first_object)

    def test_group_page_image_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': f'{PostImage.group.slug}'}))
        first_object = response.context['page'][0]
        context_equal(self, first_object)


class PagViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='VG')

        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-post-slug'
        )
        posts_count = 13
        for posts in range(posts_count):
            cls.post = Post.objects.create(
                text=f'Тестовый {posts}',
                author=User.objects.get(username='VG'),
                group=Group.objects.get(title='Заголовок группы')
            )

    def setUp(self):
        self.guest_client = Client()
        cache.clear()

    def test_paginator(self):
        """ Страницы паджинатора отображает
        верное количество записей."""
        page_post = {
            '/': 10,
            '/?page=2': 3,
            f'/group/{PagViewsTest.group.slug}/': 10,
            f'/group/{PagViewsTest.group.slug}/?page=2': 3,
            f'/{PagViewsTest.post.author}/': 10,
            f'/{PagViewsTest.post.author}/?page=2': 3,
        }
        for page, post in page_post.items():
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context.get('page').object_list),
                                 post)

    def test_cache_index_page(self):
        response = self.guest_client.get(reverse('index'))
        start_test_count = len(response.context.get('page').object_list)
        Post.objects.create(text='Тест',
                            author=User.objects.get(username='VG'),
                            group=Group.objects.get(title='Заголовок группы'))
        end_test_count = len(response.context.get('page').object_list)
        self.assertEqual(start_test_count, end_test_count)


class PostFollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='1')
        User.objects.create_user(username='2')
        User.objects.create_user(username='3')
        Follow.objects.create(user=User.objects.get(username='1'),
                              author=User.objects.get(username='2'))

        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.get(username='2'),
        )

    def setUp(self):
        self.user = User.objects.get(username='1')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_following_follow(self):
        """follow_index показывает посты избранных авторов подписчикам."""
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test_follow_delete(self):
        count = Follow.objects.count()
        self.authorized_client.get(reverse('profile_unfollow',
                                           kwargs={'username': '2'}))
        count_new = Follow.objects.count()
        self.assertEqual(count - 1, count_new)


class PostUnFollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='1')
        User.objects.create_user(username='2')
        User.objects.create_user(username='3')
        Follow.objects.create(user=User.objects.get(username='1'),
                              author=User.objects.get(username='2'))

        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.get(username='2'),
        )

    def setUp(self):
        self.user = User.objects.get(username='3')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_following_unfollow(self):
        """follow_index не показывает посты избранных авторов
        не подписчикам."""
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context.get('page').object_list), 0)

    def test_follow_create(self):
        count = Follow.objects.count()
        self.authorized_client.get(reverse('profile_follow',
                                           kwargs={'username': '2'}))
        count_new = Follow.objects.count()
        self.assertEqual(count + 1, count_new)
