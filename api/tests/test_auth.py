from django.core import mail

from .base import ApiTestCase, make_user


class AuthTests(ApiTestCase):
    def test_register_creates_user_and_returns_tokens(self):
        response = self.api.post('/api/v1/auth/register/', {
            'username': 'newbie', 'email': 'newbie@example.test', 'password': 'Sturdy-pass-9x',
            'first_name': 'New', 'last_name': 'Bie',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
        self.assertEqual(response.json()['user']['username'], 'newbie')

        from main.models import User
        user = User.objects.get(username='newbie')
        self.assertTrue(user.check_password('Sturdy-pass-9x'))
        self.assertEqual(len(mail.outbox), 1)

    def test_register_rejects_weak_password_and_duplicate_email(self):
        make_user('taken')
        weak = self.api.post('/api/v1/auth/register/', {
            'username': 'weak', 'email': 'weak@example.test', 'password': '123',
        }, format='json')
        self.assertEqual(weak.status_code, 400)
        self.assertIn('password', weak.json())

        duplicate = self.api.post('/api/v1/auth/register/', {
            'username': 'other', 'email': 'TAKEN@example.test', 'password': 'Sturdy-pass-9x',
        }, format='json')
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn('email', duplicate.json())

    def test_token_flow(self):
        make_user('alice')
        token = self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'a-strong-pass-123'}, format='json')
        self.assertEqual(token.status_code, 200)

        refreshed = self.api.post('/api/v1/auth/token/refresh/', {'refresh': token.json()['refresh']}, format='json')
        self.assertEqual(refreshed.status_code, 200)
        self.assertIn('access', refreshed.json())

    def test_wrong_password_is_rejected(self):
        make_user('alice')
        response = self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'nope'}, format='json')
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_requires_a_token(self):
        self.assertEqual(self.api.get('/api/v1/posts/').status_code, 401)

        make_user('alice')
        token = self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'a-strong-pass-123'}, format='json')
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token.json()['access']}")
        self.assertEqual(self.api.get('/api/v1/me/').json()['username'], 'alice')

    def test_login_is_throttled(self):
        make_user('alice')
        statuses = [
            self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'wrong'}, format='json').status_code
            for _ in range(11)
        ]
        self.assertEqual(statuses[-1], 429)

    def test_current_user_can_update_profile_but_not_username(self):
        alice = make_user('alice')
        self.api.force_authenticate(alice)
        response = self.api.patch('/api/v1/me/', {'bio': 'Hello there', 'username': 'hijack'}, format='json')
        self.assertEqual(response.status_code, 200)
        alice.refresh_from_db()
        self.assertEqual(alice.bio, 'Hello there')
        self.assertEqual(alice.username, 'alice')
