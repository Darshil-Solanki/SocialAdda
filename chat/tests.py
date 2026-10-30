from asgiref.sync import async_to_sync
from channels.auth import AuthMiddlewareStack
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import Client, TransactionTestCase, override_settings

from SocialAdda.routing import websocket_urlpatterns
from main.models import User

from .models import Conversation, Message

application = AuthMiddlewareStack(URLRouter(websocket_urlpatterns))
ORIGIN = (b'origin', b'http://localhost')


def make_user(username):
    return User.objects.create_user(
        username,
        f'{username}@example.test',
        'a-strong-pass-123',
        profile_pic='profile_pic/no_pic.png',
        cover='covers/no_covers.png',
    )


@override_settings(CHANNEL_LAYERS={'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}})
class ChatConsumerTests(TransactionTestCase):
    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')

    def session_cookie(self, user):
        client = Client()
        client.force_login(user)
        return f"sessionid={client.cookies['sessionid'].value}".encode()

    async def exchange(self, cookie, text):
        communicator = WebsocketCommunicator(
            application, f'/ws/{self.bob.id}/', headers=[ORIGIN, (b'cookie', cookie)])
        connected, _ = await communicator.connect()
        assert connected
        # The client claims to be "bob"; the server must ignore that.
        await communicator.send_json_to({'message': text, 'username': 'bob'})
        reply = await communicator.receive_json_from()
        await communicator.disconnect()
        return reply

    async def anonymous_connect(self):
        communicator = WebsocketCommunicator(
            application, f'/ws/{self.bob.id}/', headers=[ORIGIN])
        connected, _ = await communicator.connect()
        return connected

    def test_anonymous_connection_is_rejected(self):
        self.assertFalse(async_to_sync(self.anonymous_connect)())

    def test_sender_is_the_authenticated_user(self):
        reply = async_to_sync(self.exchange)(self.session_cookie(self.alice), 'hello')
        self.assertEqual(reply, {'message': 'hello', 'username': 'alice'})

        saved = Message.objects.get()
        self.assertEqual(saved.sender, self.alice)
        self.assertEqual(saved.body, 'hello')
        low, high = sorted((self.alice.id, self.bob.id))
        self.assertEqual(Conversation.objects.get().direct_key, f'{low}-{high}')
