import shutil
import tempfile
from django.test import override_settings
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.create_user(username='VG'),
            pub_date='Date'
        )
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-post-slug'
        )

    def setUp(self):
        self.user = PostViewTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('index'),
            'new.html': reverse('new_post'),
            'group.html': (
                reverse('group', kwargs={'slug': 'test-post-slug'})
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
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_new_post_edit_shows_correct_context(self):
        """Шаблон new_post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={'username': 'VG', 'post_id': '1'}))
        form_fields = {
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_pages_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-post-slug'})
        )
        self.assertEqual(response.context['group'].title, 'Заголовок группы')
        self.assertEqual(response.context['group'].description,
                         'Тестовый текст')
        self.assertEqual(response.context['group'].slug, 'test-post-slug')


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
                text='Тестовый%s' % posts,
                author=User.objects.get(username='VG'),
                group=Group.objects.get(title='Заголовок группы')
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_index_page_contains_ten_records(self):
        """Index - 1 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_index_page_contains_three_records(self):
        """Index - 2 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_page_group_contains_ten_records(self):
        """Group - 1 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': 'test-post-slug'}))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_group_contains_three_records(self):
        """Group - 2 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': 'test-post-slug'}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_profile_page_profile_contains_ten_records(self):
        """Profile - 1 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': 'VG'}))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_profile_contains_three_records(self):
        """Profile - 1 страница паджинатора отображает
        верное количество записей."""
        response = self.guest_client.get(
            reverse('profile', kwargs={'username': 'VG'}) + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_cache_index_page(self):
        response = self.guest_client.get(reverse('index'))
        start_test_count = len(response.context.get('page').object_list)
        Post.objects.create(text='Тест',
                            author=User.objects.get(username='VG'),
                            group=Group.objects.get(title='Заголовок группы'))
        end_test_count = len(response.context.get('page').object_list)
        self.assertEqual(start_test_count, end_test_count)


class PostGroupViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='VG')

        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-post-slug'
        )
        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.get(username='VG'),
            group=Group.objects.get(title='Заголовок группы')
        )

    def setUp(self):
        self.guest_client = Client()

    def test__page_index_contains_records(self):
        "Запись с указанной группой отображается на главной"
        response = self.guest_client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test__page_group_contains_records(self):
        "Запись с указанной группой отображается в группе"
        response = self.guest_client.get(
            reverse('group', kwargs={'slug': 'test-post-slug'}))
        self.assertEqual(len(response.context.get('page').object_list), 1)

    def test__page_other_group_no_contains_records(self):
        "Запись с указанной группой не отображается в другой группе"
        Group.objects.create(
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
            reverse('group', kwargs={'slug': 'test-post-slug_other'}))
        self.assertEqual(len(response.context.get('page').object_list), 1)


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


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class PostImageViewTests(TestCase):
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
        self.user = PostImageViewTests.post.author
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_image_page_shows_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый')
        self.assertEqual(post_pub_date_0, first_object.pub_date)
        self.assertEqual(post_author_0, first_object.author)
        self.assertEqual(post_image_0, first_object.image)

    def test_profile_image_page_shows_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': 'VG'}))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый')
        self.assertEqual(post_pub_date_0, first_object.pub_date)
        self.assertEqual(post_author_0, first_object.author)
        self.assertEqual(post_image_0, first_object.image)

    def test_post_id_page_image_shows_correct_context(self):
        """Шаблон post сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'VG', 'post_id': '1'}))
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый')
        self.assertEqual(post_pub_date_0, first_object.pub_date)
        self.assertEqual(post_author_0, first_object.author)
        self.assertEqual(post_image_0, first_object.image)

    def test_group_page_image_shows_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('group', kwargs={'slug': 'test-post-slug'}))
        first_object = response.context['page'][0]
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, 'Тестовый')
        self.assertEqual(post_pub_date_0, first_object.pub_date)
        self.assertEqual(post_author_0, first_object.author)
        self.assertEqual(post_image_0, first_object.image)
