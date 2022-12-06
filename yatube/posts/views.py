from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.cache import cache_page

from .global_constants import LIM_POSTS_PAGE
from .forms import PostForm, CommentForm
from .models import Comment, Follow, Group, Post, User


def page_context(queryset, request):
    paginator = Paginator(queryset, LIM_POSTS_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


@cache_page(20, key_prefix='index_page')
def index(request):
    title = 'Последние обновления на сайте.'
    text_index = 'Главная страница'
    post_list = Post.objects.all()
    context = {
        'title': title,
        'text_index': text_index,
        'page_obj': post_list,
    }
    context.update(page_context(post_list, request))
    template = "posts/index.html"
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.group_list.select_related("author", "group")
    text = group.description
    title = group.title
    title_text = 'Записи сообщества: '
    context = {
        'title': title_text + title,
        'page_obj': post_list,
        'group': group,
        'text': text,
    }
    context.update(page_context(post_list, request))
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related("group", "author")
    template = 'posts/profile.html'
    following = False
    if request.user.is_authenticated is True:
        check_filter = Follow.objects.filter(user=request.user, author=author)
        if check_filter:
            following = True
        else:
            following = False
    context = {
        'page_obj': post_list,
        'author': author,
        'following': following,
    }
    context.update(page_context(post_list, request))
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post, active=True)
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, template, context)


@login_required
def create_post(request):
    form = PostForm(request.POST or None,
                    files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user.username)
    context = {
        'form': form,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        form = PostForm(request.POST or None,
                        files=request.FILES or None,
                        instance=post
                        )
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post.pk)
        context = {
            'form': form,
            'is_edit': True,
            'post': post,
        }
        return render(request, 'posts/create_post.html', context)
    return redirect('posts:post_detail', post.pk)


@login_required
def add_comment(request, post_id):
    post = Post.objects.get(pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post.pk)


@login_required
def follow_index(request):
    title = 'Мои подписки'
    following = request.user
    post_list = Post.objects.filter(author__following__user=following)
    context = {
        'title': title,
        'page_obj': post_list
    }
    context.update(page_context(post_list, request))
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author_follow = get_object_or_404(User, username=username)
    if request.user != author_follow:
        follower = Follow.objects.filter(
            user=request.user,
            author=author_follow
        ).exists()
        if follower is False:
            Follow.objects.create(
                user=request.user,
                author=author_follow
            )
            return redirect('posts:profile', author_follow)
        else:
            return redirect('posts:index')
    else:
        return redirect('posts:profile', author_follow)


@login_required
def profile_unfollow(request, username):
    user = get_object_or_404(User, username=request.user.username)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('posts:profile', author.username)
