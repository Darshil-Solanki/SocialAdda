from django.test import Client

from main.models import Post

from .base import ApiTestCase, make_user


class SecurityTests(ApiTestCase):
    def test_session_write_without_csrf_token_is_rejected(self):
        # Session-authenticated browsers must send the CSRF token; JWT clients are not affected.
        user = make_user('alice')
        post = Post.objects.create(creater=user, content_text='hi')
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(user)
        response = browser.post(f'/api/v1/posts/{post.id}/like/')
        self.assertEqual(response.status_code, 403)

    def test_anonymous_chat_is_rejected(self):
        make_user('bob')
        self.assertEqual(self.api.get('/api/v1/conversations/').status_code, 401)

    def test_unknown_profile_returns_404(self):
        make_user('alice')
        self.api.force_authenticate(make_user('viewer'))
        self.assertEqual(self.api.get('/api/v1/users/nobody_here/').status_code, 404)


class OperationsTests(ApiTestCase):
    def test_health_endpoint_reports_ok(self):
        response = self.api.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['checks']['database'], 'ok')

    def test_write_requests_are_rate_limited(self):
        from unittest import mock

        from api.throttling import WriteThrottle

        user = make_user('busy')
        self.api.force_authenticate(user)
        with mock.patch.dict(WriteThrottle.THROTTLE_RATES, {'writes': '3/minute'}):
            statuses = [self.api.post('/api/v1/posts/', {'content_text': f'p{i}'}, format='json').status_code
                        for i in range(5)]
        self.assertEqual(statuses[:3], [201, 201, 201])
        self.assertEqual(statuses[3], 429)

    def test_reads_are_not_counted_against_the_write_limit(self):
        from unittest import mock

        from api.throttling import WriteThrottle

        self.api.force_authenticate(make_user('reader'))
        with mock.patch.dict(WriteThrottle.THROTTLE_RATES, {'writes': '1/minute'}):
            statuses = [self.api.get('/api/v1/posts/').status_code for _ in range(3)]
        self.assertEqual(statuses, [200, 200, 200])
