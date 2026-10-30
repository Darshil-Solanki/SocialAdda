from io import StringIO
from unittest import mock

import fakeredis
from django.core.management import call_command
from django.test import TestCase

from main.models import Follow, Post, PostLike, User
from main.tasks import deliver_notification_task, fanout_post_task


class SeedDemoTests(TestCase):
    def setUp(self):
        # Background jobs and the feed index are stubbed; these tests check the stored data only.
        feed = mock.patch('main.feeds.get_feed_client', return_value=fakeredis.FakeRedis(decode_responses=True))
        feed.start()
        self.addCleanup(feed.stop)
        for task in (fanout_post_task, deliver_notification_task):
            patcher = mock.patch.object(task, 'delay')
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_seed(self, **options):
        call_command('seed_demo', stdout=StringIO(), **options)

    def test_creates_users_follows_posts_and_engagement(self):
        self.run_seed(users=5, posts_per_user=2)
        self.assertEqual(User.objects.filter(username__startswith='demo').count(), 5)
        self.assertEqual(Post.objects.count(), 10)
        self.assertGreater(Follow.objects.count(), 0)
        self.assertGreater(PostLike.objects.count(), 0)

    def test_is_repeatable_with_the_same_seed(self):
        self.run_seed(users=4, posts_per_user=1, seed=7)
        first = sorted(Follow.objects.values_list('follower__username', 'following__username'))
        Follow.objects.all().delete()
        Post.objects.all().delete()
        PostLike.objects.all().delete()
        self.run_seed(users=4, posts_per_user=1, seed=7)
        second = sorted(Follow.objects.values_list('follower__username', 'following__username'))
        self.assertEqual(first, second)

    def test_demo_users_can_log_in(self):
        self.run_seed(users=2, posts_per_user=1)
        self.assertTrue(User.objects.get(username='demo1').check_password('demo-pass-123'))
