from django.contrib.auth import get_user_model
from django.forms import ModelForm, Textarea

from .models import Post, User, Comment

User = get_user_model()


class PostForm(ModelForm):
    """ Создаем форму для создания/редактирования постов. """

    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': 'Введите текст', 'group': 'Выберите группу'}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': Textarea}
        labels = {'text': 'Введите текст комментария'}
