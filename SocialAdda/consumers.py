import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone

from chat.models import ConversationMember
from chat.services import create_message, get_or_create_direct_conversation
from main.models import User
from main.notifications import user_group

from .middleware import accepted_subprotocol

MAX_MESSAGE_LENGTH = 1000


class PersonalChatConsumer(AsyncWebsocketConsumer):
    """One direct conversation. Messages, typing and read receipts all go through the same group."""

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        other_user_id = self.scope['url_route']['kwargs']['id']
        if other_user_id == user.id or not await self.user_exists(other_user_id):
            # No chatting with yourself, and no thread for a user that does not exist.
            await self.close()
            return

        self.conversation_id = await self.open_conversation(user.id, other_user_id)
        self.room_group_name = f'chat_{self.conversation_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept(accepted_subprotocol(self.scope))

    async def disconnect(self, code):
        room_group_name = getattr(self, 'room_group_name', None)
        if room_group_name:
            await self.channel_layer.group_discard(room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        try:
            data = json.loads(text_data or '')
        except ValueError:
            return
        # Every frame must be a JSON object; anything else is ignored rather than crashing the consumer.
        if not isinstance(data, dict):
            return

        # The sender is always the authenticated user, never a client-supplied name.
        sender = self.scope['user']
        kind = data.get('type', 'message')

        if kind == 'typing':
            await self.group_event({'event': 'typing', 'username': sender.username})
        elif kind == 'read':
            read_at = await self.mark_read(sender.id)
            await self.group_event({'event': 'read', 'username': sender.username, 'read_at': read_at.isoformat()})
        elif kind == 'message':
            body = str(data.get('message', '')).strip()
            if not body or len(body) > MAX_MESSAGE_LENGTH:
                return
            await self.save_message(sender.id, body)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'chat_message', 'message': body, 'username': sender.username},
            )

    async def group_event(self, payload):
        await self.channel_layer.group_send(self.room_group_name, {'type': 'chat_event', **payload})

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
        }))

    async def chat_event(self, event):
        payload = {key: value for key, value in event.items() if key != 'type'}
        await self.send(text_data=json.dumps(payload))

    @database_sync_to_async
    def user_exists(self, user_id):
        return User.objects.filter(id=user_id).exists()

    @database_sync_to_async
    def open_conversation(self, user_id, other_user_id):
        return get_or_create_direct_conversation(user_id, other_user_id).id

    @database_sync_to_async
    def save_message(self, sender_id, body):
        create_message(self.conversation_id, sender_id, body)

    @database_sync_to_async
    def mark_read(self, user_id):
        now = timezone.now()
        ConversationMember.objects.filter(conversation_id=self.conversation_id, user_id=user_id).update(last_read_at=now)
        return now


class NotificationConsumer(AsyncWebsocketConsumer):
    """Pushes a user's new notifications to every open tab they have."""

    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return
        self.group_name = user_group(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept(accepted_subprotocol(self.scope))

    async def disconnect(self, code):
        group_name = getattr(self, 'group_name', None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def notification(self, event):
        await self.send(text_data=json.dumps(event['notification']))
