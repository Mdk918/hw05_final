from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group, Follow

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='Тестовый',
            author=User.objects.create_user(username='VG'),
        )

    def test_object_name_is_text_field(self):
        """__str__  post - это строчка с содержимым post.text."""
        post = PostModelTest.post
        expected_object_name = post.text
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-task'
        )

    def test_object_name_is_title_field(self):
        """__str__  group - это строчка с содержимым group.title."""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))


class FollowModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create_user(username='1')
        author = User.objects.create_user(username='2')

        cls.follow = Follow.objects.create(
            user=user,
            author=author
        )

    def test_object_name_is_title_field(self):
        """Ожидаемое значения автора совпадеает с содержимым"""
        follow = FollowModelTest.follow
        expected_object_name = str(follow.author)
        self.assertEqual(expected_object_name, str(follow))
