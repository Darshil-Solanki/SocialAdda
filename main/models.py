from django.db import models
from django.db.models.functions import Lower
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    profile_pic = models.ImageField(upload_to='profile_pic/', blank=True)
    bio = models.TextField(max_length=160, blank=True, null=True)
    cover = models.ImageField(upload_to='covers/', blank=True)
    # Access tokens carry this value; changing it signs the account out everywhere (see api/auth.py).
    session_version = models.PositiveIntegerField(default=0)

    class Meta(AbstractUser.Meta):
        constraints = [
            # One account per email address, ignoring case. Accounts without an email are exempt.
            models.UniqueConstraint(Lower('email'), condition=~models.Q(email=''), name='user_email_unique_ci'),
        ]

    def __str__(self):
        return self.username


class Post(models.Model):
    creater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    date_created = models.DateTimeField(default=timezone.now)
    content_text = models.TextField(max_length=140, blank=True)
    content_image = models.ImageField(upload_to='posts/', blank=True)
    # Smaller WebP copy made by a background task; the feed uses it when present.
    content_thumbnail = models.ImageField(upload_to='posts/thumbs/', blank=True)
    # Denormalized counters, updated atomically with F() expressions.
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date_created', '-id']
        indexes = [
            models.Index(fields=['-date_created'], name='post_created_idx'),
            models.Index(fields=['creater', '-date_created'], name='post_author_created_idx'),
        ]

    def __str__(self):
        return f'Post ID: {self.id} (creater: {self.creater})'


class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_likes')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_like'),
        ]


class PostBookmark(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_bookmarks')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='post_bookmarks')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['post', 'user'], name='unique_post_bookmark'),
        ]


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    commenter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='commenters')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    comment_content = models.TextField(max_length=90)
    comment_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Post: {self.post} | Commenter: {self.commenter}'


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_relations')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower_relations')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['follower', 'following'], name='unique_follow'),
            models.CheckConstraint(condition=~models.Q(follower=models.F('following')), name='no_self_follow'),
        ]
        indexes = [
            models.Index(fields=['following', 'created_at'], name='follow_target_idx'),
        ]

    def __str__(self):
        return f'{self.follower} follows {self.following}'


class Notification(models.Model):
    class Verb(models.TextChoices):
        LIKE = 'like', 'liked your post'
        COMMENT = 'comment', 'commented on your post'
        FOLLOW = 'follow', 'started following you'

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    verb = models.CharField(max_length=20, choices=Verb.choices)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']
        indexes = [
            models.Index(fields=['recipient', 'read_at'], name='notification_unread_idx'),
        ]

    def __str__(self):
        return f'{self.actor} {self.get_verb_display()} ({self.recipient})'
