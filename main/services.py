from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.core.cache import cache
from django.db import transaction
from django.db.models import F
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

from .models import Comment, Follow, Notification, Post, PostBookmark, PostLike
from .feeds import on_follow
from .notifications import notify
from .selectors import user_counts_key


class SelfFollowError(ValueError):
    pass


def set_like(post, user, liked):
    """Idempotent like/unlike; the counter moves only when a row actually changes."""
    with transaction.atomic():
        if liked:
            _, created = PostLike.objects.get_or_create(post=post, user=user)
            if created:
                Post.objects.filter(pk=post.pk).update(like_count=F('like_count') + 1)
                notify(post.creater, user, Notification.Verb.LIKE, post)
        else:
            deleted, _ = PostLike.objects.filter(post=post, user=user).delete()
            if deleted:
                Post.objects.filter(pk=post.pk).update(like_count=F('like_count') - 1)


def set_bookmark(post, user, saved):
    if saved:
        PostBookmark.objects.get_or_create(post=post, user=user)
    else:
        PostBookmark.objects.filter(post=post, user=user).delete()


def set_follow(follower, following, follow):
    if follower.pk == following.pk:
        raise SelfFollowError('You cannot follow yourself.')
    if follow:
        _, created = Follow.objects.get_or_create(follower=follower, following=following)
        if created:
            on_follow(follower, following)
            notify(following, follower, Notification.Verb.FOLLOW)
    else:
        Follow.objects.filter(follower=follower, following=following).delete()
    # Follower/following counts are cached per user, so both sides must be refreshed.
    cache.delete_many([user_counts_key(follower.id), user_counts_key(following.id)])


def add_comment(post, author, body, parent=None):
    """Adds a comment, or a reply when `parent` is a top-level comment on the same post. Replies cannot be nested."""
    if parent is not None and (parent.post_id != post.pk or parent.parent_id is not None):
        raise ValueError('A reply must target a top-level comment on the same post.')
    with transaction.atomic():
        comment = Comment.objects.create(post=post, commenter=author, comment_content=body, parent=parent)
        Post.objects.filter(pk=post.pk).update(comment_count=F('comment_count') + 1)
        notify(post.creater, author, Notification.Verb.COMMENT, post)
    return comment



def remove_stored_files(post, names):
    """Deletes image files a post no longer references (after an edit or a delete)."""
    storage = Post._meta.get_field('content_image').storage
    for name in names:
        storage.delete(name)


def revoke_user_tokens(user):
    """Blacklists every refresh token the user holds, ending all of their sessions."""
    for token in OutstandingToken.objects.filter(user=user):
        BlacklistedToken.objects.get_or_create(token=token)


def build_password_reset_link(user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    return f'{settings.FRONTEND_URL}/reset-password?uid={uid}&token={token}'


def send_password_reset_email(user):
    link = build_password_reset_link(user)
    body = (
        f'Hi {user.first_name or user.username},\n\n'
        'Someone asked to reset the password for your SocialAdda account. '
        f'To choose a new password, open this link:\n\n{link}\n\n'
        'If you did not ask for this, you can ignore this email.\n\n'
        'The SocialAdda team'
    )
    send_mail('Reset your SocialAdda password', body, settings.DEFAULT_FROM_EMAIL, [user.email])


def send_welcome_email(user):
    body = (
        f'Dear {user.first_name or user.username},\n\n'
        'Thank you for signing up to SocialAdda. Your account is ready.\n\n'
        'The SocialAdda team'
    )
    send_mail('Welcome to SocialAdda', body, settings.DEFAULT_FROM_EMAIL, [user.email])
