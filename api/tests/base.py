import shutil
import tempfile
from unittest import mock

import fakeredis
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from main.models import User
from main.tasks import (
    create_thumbnail_task,
    deliver_notification_task,
    fanout_post_task,
    send_password_reset_email_task,
    send_welcome_email_task,
)


def make_user(username, **extra):
    return User.objects.create_user(
        username,
        f'{username}@example.test',
        'a-strong-pass-123',
        profile_pic='profile_pic/no_pic.png',
        cover='covers/no_covers.png',
        **extra,
    )


def run_tasks_inline(task):
    """Makes .delay() run the task synchronously, so tests can assert on its effects (such as sent emails)."""
    return mock.patch.object(task, 'delay', side_effect=lambda *args, **kwargs: task.apply(args=args, kwargs=kwargs))


class ApiTestCase(TestCase):
    def setUp(self):
        # Throttle counters live in the cache; start every test with a clean slate.
        cache.clear()
        # Uploads in any test go to a throwaway folder, never into the real media/ directory.
        media_root = tempfile.mkdtemp(prefix='sa-test-media-')
        self.addCleanup(shutil.rmtree, media_root, True)
        media_override = override_settings(MEDIA_ROOT=media_root)
        media_override.enable()
        self.addCleanup(media_override.disable)
        self.api = APIClient()
        # Feed index lives in an in-memory Redis stand-in, fresh for each test.
        feed_redis = fakeredis.FakeRedis(decode_responses=True)
        feed_patch = mock.patch('main.feeds.get_feed_client', return_value=feed_redis)
        feed_patch.start()
        self.addCleanup(feed_patch.stop)
        for task in (
            send_welcome_email_task,
            send_password_reset_email_task,
            create_thumbnail_task,
            deliver_notification_task,
            fanout_post_task,
        ):
            patcher = run_tasks_inline(task)
            patcher.start()
            self.addCleanup(patcher.stop)
