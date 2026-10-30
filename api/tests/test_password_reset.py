import re

from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .base import ApiTestCase, make_user


class PasswordResetTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.alice.email = 'alice@example.test'
        self.alice.save()

    def reset_params(self):
        """Pulls uid and token out of the email, the same way a user would follow the link."""
        link = re.search(r'https?://\S+', mail.outbox[-1].body).group(0)
        query = dict(part.split('=', 1) for part in link.split('?', 1)[1].split('&'))
        return query['uid'], query['token']

    def test_request_emails_a_link_to_the_frontend(self):
        response = self.api.post('/api/v1/auth/password-reset/', {'email': 'alice@example.test'}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('http://localhost:3000/reset-password?uid=', mail.outbox[0].body)

    def test_unknown_email_gets_the_same_answer_and_no_email(self):
        response = self.api.post('/api/v1/auth/password-reset/', {'email': 'nobody@example.test'}, format='json')
        self.assertEqual(response.status_code, 202)
        self.assertEqual(len(mail.outbox), 0)

    def test_confirm_sets_the_new_password(self):
        self.api.post('/api/v1/auth/password-reset/', {'email': 'alice@example.test'}, format='json')
        uid, token = self.reset_params()

        response = self.api.post('/api/v1/auth/password-reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': 'Brand-new-pass-7',
        }, format='json')

        self.assertEqual(response.status_code, 204)
        self.alice.refresh_from_db()
        self.assertTrue(self.alice.check_password('Brand-new-pass-7'))
        self.assertFalse(self.alice.check_password('a-strong-pass-123'))

    def test_link_cannot_be_reused(self):
        self.api.post('/api/v1/auth/password-reset/', {'email': 'alice@example.test'}, format='json')
        uid, token = self.reset_params()
        payload = {'uid': uid, 'token': token, 'new_password': 'Brand-new-pass-7'}
        self.assertEqual(self.api.post('/api/v1/auth/password-reset/confirm/', payload, format='json').status_code, 204)
        self.assertEqual(self.api.post('/api/v1/auth/password-reset/confirm/', payload, format='json').status_code, 400)

    def test_weak_new_password_is_rejected_with_a_field_error(self):
        self.api.post('/api/v1/auth/password-reset/', {'email': 'alice@example.test'}, format='json')
        uid, token = self.reset_params()
        response = self.api.post('/api/v1/auth/password-reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': '123',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('new_password', response.json())

    def test_forged_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.alice.pk))
        response = self.api.post('/api/v1/auth/password-reset/confirm/', {
            'uid': uid, 'token': 'forged-token', 'new_password': 'Brand-new-pass-7',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('token', response.json())
