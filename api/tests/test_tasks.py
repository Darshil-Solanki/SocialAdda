from unittest import mock

from django.core import mail

from main.tasks import send_welcome_email_task

from .base import ApiTestCase, make_user


class BackgroundJobTests(ApiTestCase):
    def test_registration_queues_the_welcome_email(self):
        with mock.patch.object(send_welcome_email_task, 'delay') as delay:
            response = self.api.post('/api/v1/auth/register/', {
                'username': 'queued', 'email': 'queued@example.test', 'password': 'Sturdy-pass-9x',
            }, format='json')
        self.assertEqual(response.status_code, 201)
        delay.assert_called_once()

    def test_welcome_email_content(self):
        user = make_user('carol', first_name='Carol')
        send_welcome_email_task.apply(args=(user.pk,))
        self.assertEqual(mail.outbox[-1].subject, 'Welcome to SocialAdda')
        self.assertIn('Dear Carol', mail.outbox[-1].body)

    def test_missing_user_is_ignored(self):
        send_welcome_email_task.apply(args=(999999,))
        self.assertEqual(len(mail.outbox), 0)
