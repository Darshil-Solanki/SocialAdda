from main.models import Notification, Post

from .base import ApiTestCase, make_user


class NotificationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.post = Post.objects.create(creater=self.alice, content_text='hello')

    def test_like_notifies_the_author_once(self):
        self.api.force_authenticate(self.bob)
        self.api.post(f'/api/v1/posts/{self.post.id}/like/')
        self.api.post(f'/api/v1/posts/{self.post.id}/like/')
        self.assertEqual(Notification.objects.filter(recipient=self.alice, verb='like').count(), 1)

    def test_comment_and_follow_notify_their_targets(self):
        self.api.force_authenticate(self.bob)
        self.api.post(f'/api/v1/posts/{self.post.id}/comments/', {'body': 'nice'}, format='json')
        self.api.post('/api/v1/users/alice/follow/')
        verbs = sorted(Notification.objects.filter(recipient=self.alice).values_list('verb', flat=True))
        self.assertEqual(verbs, ['comment', 'follow'])

    def test_liking_your_own_post_does_not_notify_you(self):
        self.api.force_authenticate(self.alice)
        self.api.post(f'/api/v1/posts/{self.post.id}/like/')
        self.assertFalse(Notification.objects.exists())

    def test_notification_list_is_private_to_the_recipient(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, verb='like', post=self.post)
        self.api.force_authenticate(self.bob)
        self.assertEqual(self.api.get('/api/v1/notifications/').json()['results'], [])

        self.api.force_authenticate(self.alice)
        results = self.api.get('/api/v1/notifications/').json()['results']
        self.assertEqual(results[0]['actor']['username'], 'bob')
        self.assertEqual(results[0]['post_id'], self.post.id)

    def test_unread_count_and_mark_all_read(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, verb='like', post=self.post)
        Notification.objects.create(recipient=self.alice, actor=self.bob, verb='follow')
        self.api.force_authenticate(self.alice)
        self.assertEqual(self.api.get('/api/v1/notifications/unread-count/').json()['count'], 2)

        self.assertEqual(self.api.post('/api/v1/notifications/read/').status_code, 204)
        self.assertEqual(self.api.get('/api/v1/notifications/unread-count/').json()['count'], 0)

    def test_deleting_a_post_removes_its_notifications(self):
        Notification.objects.create(recipient=self.alice, actor=self.bob, verb='like', post=self.post)
        self.post.delete()
        self.assertFalse(Notification.objects.exists())
