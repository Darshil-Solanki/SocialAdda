from io import BytesIO

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from celery import shared_task
from django.core.files.base import ContentFile
from PIL import Image

from .feeds import fan_out_post
from .models import Notification, Post, User
from .notifications import notification_payload, user_group
from .services import send_password_reset_email, send_welcome_email

THUMBNAIL_SIZE = (480, 480)


# Retries cover transient SMTP failures; after the last retry the error is logged.
@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_welcome_email_task(self, user_id):
    user = User.objects.filter(pk=user_id).first()
    if user is not None:
        send_welcome_email(user)


@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def send_password_reset_email_task(self, user_id):
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if user is not None:
        send_password_reset_email(user)


@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def deliver_notification_task(self, notification_id):
    notification = (
        Notification.objects.select_related('actor', 'recipient').filter(pk=notification_id).first()
    )
    if notification is None:
        return
    async_to_sync(get_channel_layer().group_send)(
        user_group(notification.recipient_id),
        {'type': 'notification', 'notification': notification_payload(notification)},
    )


@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def create_thumbnail_task(self, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if post is None or not post.content_image:
        return

    with post.content_image.open('rb') as source:
        image = Image.open(source)
        image.thumbnail(THUMBNAIL_SIZE)
        if image.mode not in ('RGB', 'RGBA'):
            image = image.convert('RGB')
        buffer = BytesIO()
        image.save(buffer, format='WEBP', quality=80)

    stem = post.content_image.name.rsplit('/', 1)[-1].rsplit('.', 1)[0]
    post.content_thumbnail.save(f'{stem}.webp', ContentFile(buffer.getvalue()), save=False)
    Post.objects.filter(pk=post.pk).update(content_thumbnail=post.content_thumbnail.name)


@shared_task(
    bind=True,
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def fanout_post_task(self, post_id):
    post = Post.objects.filter(pk=post_id).first()
    if post is not None:
        fan_out_post(post)
