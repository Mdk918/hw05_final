from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, settings.PAG_VAL)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'index.html', {'page': page})


def group_posts(request, slug):
    """ Создаем функцию отображения сообществ."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.group.all()
    paginator = Paginator(posts, settings.PAG_VAL)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {"group": group, 'page': page})


def profile(request, username):
    """ Создаем функцию отображения страницы профиля."""
    author = get_object_or_404(User, username=username)
    user = request.user
    posts_author = author.posts.all()
    post_count = posts_author.count()
    paginator = Paginator(posts_author, settings.PAG_VAL)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    if user.is_authenticated:
        follow = user.follower.values_list('author')
        following = User.objects.filter(pk__in=follow)
        return render(request, 'profile.html', {'author': author,
                                                'page': page,
                                                'post_count': post_count,
                                                'following': following})
    return render(request, 'profile.html', {'author': author,
                                            'page': page,
                                            'post_count': post_count})


def post_view(request, username, post_id):
    """ Создаем функцию отображения страницы поста."""
    author = get_object_or_404(User, username=username)
    post_count = Post.objects.filter(author=author).count()
    post = get_object_or_404(Post, author__username=username, id=post_id)
    comments = post.comments.filter(post=post)
    form = CommentForm()
    return render(request, 'post.html', {'author': author,
                                         "post_count": post_count,
                                         'post': post,
                                         'form': form,
                                         'comments': comments})


@login_required
def post_new(request):
    """ Создаем функцию отображения создания поста."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        new_post = form.save(commit=False)
        new_post.author = request.user
        new_post.save()
        return redirect('index')
    return render(request, 'new.html', {'form': form})


def post_edit(request, username, post_id):
    """ Создаем функцию отображения редактирования поста."""
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, username=username)
    if request.user != author:
        return redirect('post', username=author.username, post_id=post.id)
    form = PostForm(request.POST or None, files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('post', username=author.username, post_id=post.id)
    return render(request, 'new.html', {'form': form, 'post': post})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


def add_comment(request, username, post_id):
    """ Создаем функцию отображения комментария поста."""
    post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        new_comment = form.save(commit=False)
        new_comment.author = request.user
        new_comment.post = post
        new_comment.save()
        return redirect('post', username=author.username, post_id=post.id)
    return redirect('post', username=author.username, post_id=post.id)


@login_required
def follow_index(request):
    """ Создаем функцию отображения постов подписок. """
    user = request.user
    follow = Follow.objects.filter(user=user).values_list('author')
    post_follow = Post.objects.filter(author__pk__in=follow)
    paginator = Paginator(post_follow, settings.PAG_VAL)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html', {'page': page})


@login_required
def profile_follow(request, username):
    """ Создаем функцию возможности подписаться на автора. """
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.create(user=user, author=author)
        return redirect('profile', username=author.username)
    return redirect('profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    """ Создаем функцию возможности отписаться от автора. """
    user = request.user
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=user, author=author)
    follow.delete()
    return redirect('profile', username=author.username)
