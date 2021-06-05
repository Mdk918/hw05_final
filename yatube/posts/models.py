from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Post(models.Model):
    text = models.TextField()
    pub_date = models.DateTimeField("date published", auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="posts")
    group = models.ForeignKey("Group", on_delete=models.SET_NULL, blank=True,
                              null=True, related_name="group")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        """ Создаем класс для сортировки по умолчанию. """

        ordering = ["-pub_date"]

    def __str__(self):
        return self.text[:15]


class Group(models.Model):
    """ Создаем модель для сообществ. """

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        """ Возвращаем поле title при печати объекта. """
        return self.title


class Comment(models.Model):
    """ Создаем модель для комментария. """
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.text


class Follow(models.Model):
    """ Создаем модель для подписок. """
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             related_name="follower")
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="following")

    def __str__(self):
        return str(self.author)
