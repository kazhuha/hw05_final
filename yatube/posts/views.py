from genericpath import exists
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from .forms import CommentForm, PostForm
from .models import Follow, Group, Comment, Post, User
from .utils import paginate


def index(request):
    template = 'posts/index.html'
    paginator = paginate(request, Post.objects.all())
    context = {'page_obj': paginator}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = paginate(request, posts_list)
    context = {
        'group': group,
        'page_obj': paginator,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    paginator = paginate(request, Post.objects.filter(author=author))
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author
        )
        context = {
            'author': author,
            'page_obj': paginator,
            'following': following,
        }
        return render(request, 'posts/profile.html', context)
    else:
        context = {
            'author': author,
            'page_obj': paginator,
            'following': False,
        }
        return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post=post_id)
    form = CommentForm(
        request.POST or None
    )
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author)
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'is_edit': True
    }
    if form.is_valid():
        post = form.save(commit=False)
        post.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follower = request.user
    paginator = paginate(
        request, Post.objects.filter(author__following__user=follower)
    )
    context = {'page_obj': paginator}
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    folower = request.user
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=folower, author=author).exists() or folower == author:
        return redirect('posts:follow_index')
    else:
        Follow.objects.create(
            user=folower,
            author=author
        )
        return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    folower = request.user
    author = get_object_or_404(User, username=username)
    following = Follow.objects.filter(
        user=folower,
        author=author
    )
    following.delete()
    return redirect('posts:follow_index')
