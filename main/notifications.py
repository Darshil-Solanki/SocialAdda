from django.db import transaction

from .models import Notification


def user_group(user_id):
    """Channel-layer group that carries one user's live notifications."""
    return f'user_{user_id}'


def notify(recipient, actor, verb, post=None):
    """Stores a notification and pushes it to the recipient's open sockets after commit. Self-actions are skipped."""
    if recipient.pk == actor.pk:
        return None
    from .jobs import enqueue
    from .tasks import deliver_notification_task

    notification = Notification.objects.create(recipient=recipient, actor=actor, verb=verb, post=post)
    transaction.on_commit(lambda: enqueue(deliver_notification_task, notification.pk))
    return notification


def notification_payload(notification):
    """The JSON shape shared by the REST API and the live socket."""
    return {
        'id': notification.id,
        'verb': notification.verb,
        'actor': {
            'id': notification.actor.id,
            'username': notification.actor.username,
            'first_name': notification.actor.first_name,
            'last_name': notification.actor.last_name,
        },
        'post_id': notification.post_id,
        'created_at': notification.created_at.isoformat(),
        'read_at': notification.read_at.isoformat() if notification.read_at else None,
    }
