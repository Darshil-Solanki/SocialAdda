from unittest import mock

from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TransactionTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from channels.db import database_sync_to_async
from django.test import Client
from rest_framework.test import APIClient

from SocialAdda.middleware import JwtAuthMiddleware
from SocialAdda.routing import websocket_urlpatterns
from chat.models import ConversationMember
from main.models import Post
from main.tasks import deliver_notification_task

from .base import make_user

IN_MEMORY_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}
application = AuthMiddlewareStack(JwtAuthMiddleware(URLRouter(websocket_urlpatterns)))


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYERS)
class JwtWebSocketTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')

    async def connect(self, subprotocols):
        communicator = WebsocketCommunicator(
            application, f'/ws/{self.bob.id}/', headers=[(b'origin', b'http://localhost')], subprotocols=subprotocols,
        )
        connected, _ = await communicator.connect()
        return communicator, connected

    async def check_token_connection(self, token):
        communicator, connected = await self.connect(['socialadda', token])
        if connected:
            await communicator.disconnect()
        return connected

    def test_valid_access_token_connects(self):
        token = str(AccessToken.for_user(self.alice))
        self.assertTrue(async_to_sync(self.check_token_connection)(token))

    def test_invalid_token_is_rejected(self):
        self.assertFalse(async_to_sync(self.check_token_connection)('not-a-real-token'))


def session_cookie(user):
    browser = Client()
    browser.force_login(user)
    return f"sessionid={browser.cookies['sessionid'].value}".encode()


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYERS)
class LiveEventTests(TransactionTestCase):
    """Typing, read receipts and notifications over WebSocket, with a fresh in-memory channel layer."""

    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        # Cookies are built here, in sync code; the async scenarios below must not touch the database.
        self.alice_cookie = session_cookie(self.alice)
        self.bob_cookie = session_cookie(self.bob)

    async def open_socket(self, path, cookie):
        communicator = WebsocketCommunicator(
            application, path, headers=[(b'origin', b'http://localhost'), (b'cookie', cookie)],
        )
        connected, _ = await communicator.connect()
        assert connected
        return communicator

    async def typing_and_read_scenario(self):
        alice_socket = await self.open_socket(f'/ws/{self.bob.id}/', self.alice_cookie)
        bob_socket = await self.open_socket(f'/ws/{self.alice.id}/', self.bob_cookie)

        await alice_socket.send_json_to({'type': 'typing'})
        typing = await bob_socket.receive_json_from()

        # Events go to the whole group, so Alice also gets her own typing event; clients ignore their own.
        own_echo = await alice_socket.receive_json_from()
        assert own_echo['event'] == 'typing'

        await bob_socket.send_json_to({'type': 'read'})
        read = await alice_socket.receive_json_from()

        await alice_socket.disconnect()
        await bob_socket.disconnect()
        return typing, read

    def test_typing_and_read_receipts_reach_the_other_person(self):
        typing, read = async_to_sync(self.typing_and_read_scenario)()
        self.assertEqual(typing, {'event': 'typing', 'username': 'alice'})
        self.assertEqual(read['event'], 'read')
        self.assertEqual(read['username'], 'bob')
        self.assertTrue(ConversationMember.objects.filter(user=self.bob, last_read_at__isnull=False).exists())

    async def notification_scenario(self, post_id):
        socket = await self.open_socket('/ws/notifications/', self.alice_cookie)
        await database_sync_to_async(self.like_as_bob)(post_id)
        received = await socket.receive_json_from()
        await socket.disconnect()
        return received

    def like_as_bob(self, post_id):
        api = APIClient()
        api.force_authenticate(self.bob)
        api.post(f'/api/v1/posts/{post_id}/like/')

    def test_like_pushes_a_live_notification_to_the_author(self):
        post = Post.objects.create(creater=self.alice, content_text='push me')
        # Run the delivery task inline; on_commit fires immediately in this transactional test.
        inline = mock.patch.object(
            deliver_notification_task, 'delay',
            side_effect=lambda pk: deliver_notification_task.apply(args=(pk,)),
        )
        with inline:
            received = async_to_sync(self.notification_scenario)(post.id)
        self.assertEqual(received['verb'], 'like')
        self.assertEqual(received['actor']['username'], 'bob')
        self.assertEqual(received['post_id'], post.id)
