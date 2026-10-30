from django.test import override_settings

from chat.models import Conversation, Message

from .base import ApiTestCase, make_user

IN_MEMORY_LAYERS = {'default': {'BACKEND': 'channels.layers.InMemoryChannelLayer'}}


@override_settings(CHANNEL_LAYERS=IN_MEMORY_LAYERS)
class ChatApiTests(ApiTestCase):
    def setUp(self):
        super().setUp()
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.carol = make_user('carol')
        self.api.force_authenticate(self.alice)

    def test_send_and_list_messages(self):
        response = self.api.post('/api/v1/conversations/bob/messages/', {'body': 'hi bob'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['sender']['username'], 'alice')
        self.assertEqual(Message.objects.count(), 1)

        self.api.force_authenticate(self.bob)
        messages = self.api.get('/api/v1/conversations/alice/messages/').json()['results']
        self.assertEqual([m['body'] for m in messages], ['hi bob'])

    def test_third_party_cannot_see_a_direct_thread(self):
        self.api.post('/api/v1/conversations/bob/messages/', {'body': 'private'}, format='json')
        self.api.force_authenticate(self.carol)
        self.assertEqual(self.api.get('/api/v1/conversations/bob/messages/').json()['results'], [])

    def test_cannot_message_yourself(self):
        response = self.api.post('/api/v1/conversations/alice/messages/', {'body': 'me'}, format='json')
        self.assertEqual(response.status_code, 400)

    def test_unread_count_and_mark_as_read(self):
        self.api.post('/api/v1/conversations/bob/messages/', {'body': 'one'}, format='json')
        self.api.post('/api/v1/conversations/bob/messages/', {'body': 'two'}, format='json')

        self.api.force_authenticate(self.bob)
        conversations = self.api.get('/api/v1/conversations/').json()['results']
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]['other_user']['username'], 'alice')
        self.assertEqual(conversations[0]['unread_count'], 2)

        self.assertEqual(self.api.post('/api/v1/conversations/alice/read/').status_code, 204)
        conversations = self.api.get('/api/v1/conversations/').json()['results']
        self.assertEqual(conversations[0]['unread_count'], 0)

    def test_sender_does_not_count_own_messages_as_unread(self):
        self.api.post('/api/v1/conversations/bob/messages/', {'body': 'mine'}, format='json')
        conversations = self.api.get('/api/v1/conversations/').json()['results']
        self.assertEqual(conversations[0]['unread_count'], 0)
        self.assertEqual(Conversation.objects.count(), 1)
