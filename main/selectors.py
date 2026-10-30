from django.core.cache import cache
from django.db.models import Exists, OuterRef, Q

from .models import Follow, Post, PostBookmark, PostLike, User


def annotate_viewer_state(posts, user):
    """Adds is_liked / is_saved so templates and serializers need no extra query per post."""
    if not user.is_authenticated:
        return posts
    return posts.annotate(
        is_liked=Exists(PostLike.objects.filter(post=OuterRef('pk'), user=user)),
        is_saved=Exists(PostBookmark.objects.filter(post=OuterRef('pk'), user=user)),
    )


def posts_with_viewer_state(user):
    return annotate_viewer_state(Post.objects.select_related('creater'), user)


def saved_posts(user):
    return posts_with_viewer_state(user).filter(post_bookmarks__user=user)


def followed_user_ids(user):
    return Follow.objects.filter(follower=user).values('following_id')


def suggestion_queryset(user, exclude_usernames=()):
    """Users the viewer does not follow yet, newest first, in a stable order so pagination never repeats."""
    queryset = User.objects.exclude(pk=user.pk).exclude(pk__in=followed_user_ids(user))
    if exclude_usernames:
        queryset = queryset.exclude(username__in=exclude_usernames)
    return queryset.order_by('-date_joined', '-id')


def user_search_queryset(user, query):
    queryset = User.objects.exclude(pk=user.pk)
    if query:
        queryset = queryset.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
        )
    queryset = queryset.annotate(
        is_following=Exists(Follow.objects.filter(follower=user, following=OuterRef('pk'))),
    )
    return queryset.order_by('username')


USER_COUNTS_TIMEOUT = 300


def user_counts_key(user_id):
    return f'user-counts:{user_id}'


def user_counts(user):
    """Follower and following counts, cached for a few minutes. Follow changes invalidate them."""
    def load():
        return {
            'followers': Follow.objects.filter(following=user).count(),
            'following': Follow.objects.filter(follower=user).count(),
        }
    return cache.get_or_set(user_counts_key(user.id), load, USER_COUNTS_TIMEOUT)
