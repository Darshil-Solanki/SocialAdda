"""Regression tests for the bugs listed in docs/changes.txt."""
import io
import os
import shutil
import tempfile
from unittest import mock

from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TransactionTestCase, override_settings
from PIL import Image
from rest_framework import serializers as drf_serializers
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.tokens import RefreshToken

from api.validators import MAX_IMAGE_BYTES, validate_image_size
from main.jobs import enqueue
from main.models import Post, User
from main.tasks import send_welcome_email_task
from SocialAdda.middleware import JwtAuthMiddleware
from SocialAdda.routing import websocket_urlpatterns

from .base import ApiTestCase, make_user
from .test_profile_media import png_upload

IN_MEMORY_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


def large_png_upload(name='large.png'):
    """A valid PNG bigger than the upload limit (random pixels do not compress)."""
    side = 1500
    image = Image.frombytes('RGB', (side, side), os.urandom(side * side * 3))
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')


class JsonErrorTests(ApiTestCase):
    def test_unexpected_exception_is_answered_with_json(self):
        self.api.force_authenticate(make_user('alice'))
        with mock.patch('api.views.users.user_search_queryset', side_effect=RuntimeError('database is behind')):
            response = self.api.get('/api/v1/users/?q=a')
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertIn('detail', response.json())

    def test_rejected_host_header_is_answered_with_json(self):
        response = self.api.get('/api/v1/me/', HTTP_HOST='not-allowed.example')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_unknown_api_path_is_answered_with_json(self):
        response = self.api.get('/api/v1/no-such-endpoint/')
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response['Content-Type'], 'application/json')


class FeedCursorTests(ApiTestCase):
    def test_non_numeric_cursor_is_a_400_not_a_crash(self):
        self.api.force_authenticate(make_user('alice'))
        response = self.api.get('/api/v1/feed/following/?before=abc')
        self.assertEqual(response.status_code, 400)
        self.assertIn('before', response.json())


class UserSearchFollowStateTests(ApiTestCase):
    def test_search_results_say_whether_the_viewer_follows_them(self):
        from main.services import set_follow

        alice = make_user('alice')
        bob = make_user('bobby')
        make_user('bobcat')
        set_follow(alice, bob, follow=True)
        self.api.force_authenticate(alice)
        results = {row['username']: row['is_following'] for row in self.api.get('/api/v1/users/?q=bob').json()['results']}
        self.assertEqual(results, {'bobby': True, 'bobcat': False})


class LogoutAndSessionTests(ApiTestCase):
    def login(self):
        make_user('alice')
        return self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'a-strong-pass-123'}, format='json').json()

    def test_logout_revokes_the_refresh_token(self):
        tokens = self.login()
        response = self.api.post('/api/v1/auth/logout/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(response.status_code, 204)
        retry = self.api.post('/api/v1/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(retry.status_code, 401)

    def test_logout_with_an_unknown_token_still_succeeds(self):
        response = self.api.post('/api/v1/auth/logout/', {'refresh': 'garbage'}, format='json')
        self.assertEqual(response.status_code, 204)

    def test_a_refresh_token_cannot_be_reused_after_the_grace_period(self):
        from django.core.cache import cache

        tokens = self.login()
        first = self.api.post('/api/v1/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(first.status_code, 200)
        cache.clear()  # the grace period is over
        reused = self.api.post('/api/v1/auth/token/refresh/', {'refresh': tokens['refresh']}, format='json')
        self.assertEqual(reused.status_code, 401)

    def test_password_reset_ends_existing_sessions(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        user = make_user('alice')
        old_refresh = str(RefreshToken.for_user(user))
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset = self.api.post(
            '/api/v1/auth/password-reset/confirm/',
            {'uid': uid, 'token': token, 'new_password': 'another-strong-pass-9'},
            format='json',
        )
        self.assertEqual(reset.status_code, 204)
        response = self.api.post('/api/v1/auth/token/refresh/', {'refresh': old_refresh}, format='json')
        self.assertEqual(response.status_code, 401)


class UploadLimitTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, True)
        self.api.force_authenticate(make_user('alice'))

    def test_validator_rejects_files_over_the_limit(self):
        with self.assertRaises(drf_serializers.ValidationError):
            validate_image_size(mock.Mock(size=MAX_IMAGE_BYTES + 1))
        validate_image_size(mock.Mock(size=MAX_IMAGE_BYTES))

    def test_oversized_post_image_is_rejected(self):
        response = self.api.post('/api/v1/posts/', {'content_image': large_png_upload()}, format='multipart')
        self.assertEqual(response.status_code, 400)
        self.assertIn('content_image', response.json())
        self.assertFalse(Post.objects.exists())

    def test_deleting_a_post_removes_its_image_from_storage(self):
        response = self.api.post('/api/v1/posts/', {'content_text': 'with image', 'content_image': png_upload('small.png')},
                                 format='multipart')
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get(pk=response.json()['id'])
        stored = os.path.join(self.media_root, post.content_image.name)
        self.assertTrue(os.path.exists(stored))
        self.api.delete(f'/api/v1/posts/{post.id}/')
        self.assertFalse(os.path.exists(stored))


class BackgroundJobFailureTests(ApiTestCase):
    def test_signup_succeeds_when_the_broker_is_down(self):
        with mock.patch.object(send_welcome_email_task, 'delay', side_effect=ConnectionError('broker down')):
            response = self.api.post('/api/v1/auth/register/', {
                'username': 'newcomer', 'email': 'newcomer@example.test', 'password': 'a-strong-pass-123',
                'first_name': 'New', 'last_name': 'Comer',
            }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.json())

    def test_enqueue_reports_failure_without_raising(self):
        with mock.patch.object(send_welcome_email_task, 'delay', side_effect=ConnectionError('broker down')):
            self.assertFalse(enqueue(send_welcome_email_task, 1))


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYERS)
class ChatSocketHardeningTests(TransactionTestCase):
    application = AuthMiddlewareStack(JwtAuthMiddleware(URLRouter(websocket_urlpatterns)))

    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')

    async def open_socket(self, user, other):
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(user))
        communicator = WebsocketCommunicator(
            self.application, f'/ws/{other.id}/', headers=[(b'origin', b'http://localhost')],
            subprotocols=['socialadda', token],
        )
        connected, _ = await communicator.connect()
        return communicator, connected

    def test_cannot_open_a_chat_with_yourself(self):
        _, connected = async_to_sync(self.open_socket)(self.alice, self.alice)
        self.assertFalse(connected)

    def test_non_object_frames_are_ignored_and_the_socket_keeps_working(self):
        async def scenario():
            communicator, connected = await self.open_socket(self.alice, self.bob)
            self.assertTrue(connected)
            await communicator.send_to(text_data='[1, 2, 3]')
            await communicator.send_to(text_data='"just a string"')
            await communicator.send_json_to({'type': 'typing'})
            event = await communicator.receive_json_from()
            await communicator.disconnect()
            return event

        self.assertEqual(async_to_sync(scenario)(), {'event': 'typing', 'username': 'alice'})

    def test_inactive_user_token_does_not_open_a_socket(self):
        from rest_framework_simplejwt.tokens import AccessToken

        token = str(AccessToken.for_user(self.alice))
        self.alice.is_active = False
        self.alice.save(update_fields=['is_active'])

        async def scenario():
            communicator = WebsocketCommunicator(
                self.application, f'/ws/{self.bob.id}/', headers=[(b'origin', b'http://localhost')],
                subprotocols=['socialadda', token],
            )
            connected, _ = await communicator.connect()
            return connected

        self.assertFalse(async_to_sync(scenario)())

    def test_token_in_the_url_is_no_longer_accepted(self):
        token = str(AccessToken.for_user(self.alice))

        async def scenario():
            communicator = WebsocketCommunicator(
                self.application, f'/ws/{self.bob.id}/?token={token}', headers=[(b'origin', b'http://localhost')],
            )
            connected, _ = await communicator.connect()
            return connected

        self.assertFalse(async_to_sync(scenario)())

    def test_socket_echoes_the_socialadda_subprotocol(self):
        token = str(AccessToken.for_user(self.alice))

        async def scenario():
            communicator = WebsocketCommunicator(
                self.application, f'/ws/{self.bob.id}/', headers=[(b'origin', b'http://localhost')],
                subprotocols=['socialadda', token],
            )
            connected, subprotocol = await communicator.connect()
            await communicator.disconnect()
            return connected, subprotocol

        self.assertEqual(async_to_sync(scenario)(), (True, 'socialadda'))


class SignupEnumerationTests(ApiTestCase):
    def test_taken_email_gets_the_same_generic_error(self):
        make_user('alice')
        response = self.api.post('/api/v1/auth/register/', {
            'username': 'someoneelse', 'email': 'ALICE@example.test', 'password': 'a-strong-pass-123',
            'first_name': 'A', 'last_name': 'B',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('already exists', str(response.json()))
        self.assertIn('email', response.json())


class CommentReplyTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.post = Post.objects.create(creater=self.alice, content_text='hello')
        self.api.force_authenticate(self.bob)
        self.url = f'/api/v1/posts/{self.post.id}/comments/'

    def test_reply_is_listed_under_its_parent_and_counted(self):
        parent = self.api.post(self.url, {'body': 'top'}, format='json').json()
        reply = self.api.post(self.url, {'body': 'reply', 'parent': parent['id']}, format='json')
        self.assertEqual(reply.status_code, 201)
        self.assertEqual(reply.json()['parent_id'], parent['id'])

        top = self.api.get(self.url).json()['results']
        self.assertEqual([row['body'] for row in top], ['top'])
        self.assertEqual(top[0]['reply_count'], 1)

        replies = self.api.get(f"{self.url}?parent={parent['id']}").json()['results']
        self.assertEqual([row['body'] for row in replies], ['reply'])

    def test_reply_to_a_reply_is_rejected(self):
        parent = self.api.post(self.url, {'body': 'top'}, format='json').json()
        reply = self.api.post(self.url, {'body': 'reply', 'parent': parent['id']}, format='json').json()
        response = self.api.post(self.url, {'body': 'deeper', 'parent': reply['id']}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('parent', response.json())

    def test_reply_to_a_comment_on_another_post_is_rejected(self):
        other = Post.objects.create(creater=self.alice, content_text='other')
        foreign = self.api.post(f'/api/v1/posts/{other.id}/comments/', {'body': 'elsewhere'}, format='json').json()
        response = self.api.post(self.url, {'body': 'nope', 'parent': foreign['id']}, format='json')
        self.assertEqual(response.status_code, 400)


class PostImageEditTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.media_root = tempfile.mkdtemp()
        override = override_settings(MEDIA_ROOT=self.media_root)
        override.enable()
        self.addCleanup(override.disable)
        self.addCleanup(shutil.rmtree, self.media_root, True)
        self.alice = make_user('alice')
        self.api.force_authenticate(self.alice)

    def test_author_can_remove_the_image_and_its_files(self):
        from .test_profile_media import png_upload

        created = self.api.post('/api/v1/posts/', {'content_text': 'pic', 'content_image': png_upload('p.png')},
                                format='multipart').json()
        post = Post.objects.get(pk=created['id'])
        stored = os.path.join(self.media_root, post.content_image.name)
        self.assertTrue(os.path.exists(stored))

        response = self.api.patch(f"/api/v1/posts/{post.id}/", {'remove_image': True}, format='json')
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertFalse(post.content_image)
        self.assertFalse(os.path.exists(stored))

    def test_removing_the_image_from_an_image_only_post_is_rejected(self):
        from .test_profile_media import png_upload

        created = self.api.post('/api/v1/posts/', {'content_image': png_upload('p.png')}, format='multipart').json()
        response = self.api.patch(f"/api/v1/posts/{created['id']}/", {'remove_image': True}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_replacing_the_photo_clears_the_old_thumbnail_in_the_same_save(self):
        from .test_profile_media import png_upload

        created = self.api.post('/api/v1/posts/', {'content_image': png_upload('old.png')}, format='multipart').json()
        post = Post.objects.get(pk=created['id'])
        post.content_thumbnail = 'posts/thumbs/old-thumb.webp'  # as the thumbnail task would have set it
        post.save(update_fields=['content_thumbnail'])

        # Stub the background job: the state checked here must come from the save itself, not from the task.
        with mock.patch('api.views.posts.enqueue'):
            response = self.api.patch(f"/api/v1/posts/{post.id}/", {'content_image': png_upload('new.png')},
                                      format='multipart')
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertTrue(post.content_image.name)
        self.assertEqual(post.content_thumbnail.name, '')
        self.assertEqual(response.json()['content_thumbnail'], None)


class ContentSecurityPolicyTests(ApiTestCase):
    def test_api_responses_carry_a_restrictive_policy(self):
        response = self.api.get('/healthz/')
        self.assertIn("default-src 'none'", response['Content-Security-Policy'])

    def test_docs_and_admin_have_their_own_policies(self):
        from SocialAdda.security import ADMIN_POLICY, DOCS_POLICY

        self.assertEqual(self.api.get('/api/docs/').get('Content-Security-Policy'), DOCS_POLICY)
        self.assertEqual(self.api.get('/admin/login/').get('Content-Security-Policy'), ADMIN_POLICY)


class SessionRevocationTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')

    def login(self):
        return self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'a-strong-pass-123'}, format='json').json()

    def test_access_token_lives_five_minutes(self):
        from django.conf import settings

        self.assertEqual(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds(), 300)

    def test_password_reset_invalidates_access_tokens_immediately(self):
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.encoding import force_bytes
        from django.utils.http import urlsafe_base64_encode

        tokens = self.login()
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.api.get('/api/v1/me/').status_code, 200)

        uid = urlsafe_base64_encode(force_bytes(self.alice.pk))
        token = default_token_generator.make_token(self.alice)
        self.api.post('/api/v1/auth/password-reset/confirm/', {
            'uid': uid, 'token': token, 'new_password': 'another-strong-pass-9',
        }, format='json')

        response = self.api.get('/api/v1/me/')
        self.assertEqual(response.status_code, 401)

    def test_a_new_login_after_reset_works(self):
        from api.auth import end_all_sessions

        end_all_sessions(self.alice)
        tokens = self.login()
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        self.assertEqual(self.api.get('/api/v1/me/').status_code, 200)


class RefreshGraceTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.tokens = self.api.post('/api/v1/auth/token/', {'username': 'alice', 'password': 'a-strong-pass-123'}, format='json').json()

    def refresh(self, token):
        return self.api.post('/api/v1/auth/token/refresh/', {'refresh': token}, format='json')

    def test_a_second_use_within_the_grace_period_gets_the_same_pair(self):
        first = self.refresh(self.tokens['refresh']).json()
        second = self.refresh(self.tokens['refresh'])
        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json(), first)

    def test_a_revoked_pair_is_not_replayed_from_the_grace_cache(self):
        first = self.refresh(self.tokens['refresh']).json()
        self.api.post('/api/v1/auth/logout/', {'refresh': first['refresh']}, format='json')
        # Within the grace period the old token still maps to the cached pair, but that pair is revoked now.
        self.assertEqual(self.refresh(self.tokens['refresh']).status_code, 401)


class ReadableConsoleEmailTests(SimpleTestCase):
    def test_reset_link_is_printed_without_quoted_printable_encoding(self):
        from django.core.mail import EmailMessage

        from SocialAdda.mail import ReadableConsoleEmailBackend

        link = 'http://localhost:3000/reset-password?uid=MjA&token=dhko7r-0cc4c53bcafec7d5b3af8cef8d56abd8'
        out = io.StringIO()
        message = EmailMessage('Reset', f'Open this link to choose a new password:\n\n{link}\n', 'a@b.test', ['c@d.test'])
        ReadableConsoleEmailBackend(stream=out).send_messages([message])
        self.assertIn(link, out.getvalue())
        self.assertNotIn('=3D', out.getvalue())


class UniqueEmailTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice_e')
        self.bob = make_user('bob_e')

    def test_database_refuses_a_second_account_with_the_same_email_any_case(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user('clone', email='ALICE_E@example.test', password='Str0ng#Pass123')

    def test_accounts_without_an_email_do_not_clash(self):
        User.objects.create_user('noemail1', email='', password='Str0ng#Pass123')
        User.objects.create_user('noemail2', email='', password='Str0ng#Pass123')

    def test_profile_edit_cannot_take_another_members_email(self):
        self.api.force_authenticate(self.bob)
        response = self.api.patch('/api/v1/me/', {'email': 'Alice_E@Example.test'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.bob.refresh_from_db()
        self.assertEqual(self.bob.email, 'bob_e@example.test')

    def test_profile_edit_can_keep_or_change_to_a_free_email(self):
        self.api.force_authenticate(self.bob)
        self.assertEqual(self.api.patch('/api/v1/me/', {'email': 'bob_e@example.test'}, format='json').status_code, 200)
        self.assertEqual(self.api.patch('/api/v1/me/', {'email': 'new@example.test'}, format='json').status_code, 200)
