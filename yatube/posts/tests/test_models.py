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
        cls.group = Group.objects.create(
            title='Заголовок группы',
            description='Тестовый текст',
            slug='test-task'
        )
        user = User.objects.create_user(username='1')
        author = User.objects.create_user(username='2')

        cls.follow = Follow.objects.create(
            user=user,
            author=author)

    def test_object_name_is_models(self):
        """__str__   - это строчка с содержимым модели."""
        post = PostModelTest.post
        group = PostModelTest.group
        follow = PostModelTest.follow
        objects_name = {
            f'{post}': f'{post.text}',
            f'{group}': f'{group.title}',
            f'{follow}': f'{follow.author}'
        }
        for clas, object in objects_name.items():
            with self.subTest(clas=clas):
                self.assertEqual(object, str(clas))
