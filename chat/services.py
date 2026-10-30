import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Conversation, ConversationMember, Message

logger = logging.getLogger(__name__)


def direct_key(user_a_id, user_b_id):
    low, high = sorted((int(user_a_id), int(user_b_id)))
    return f'{low}-{high}'


def get_or_create_direct_conversation(user_a_id, user_b_id):
    conversation, _ = Conversation.objects.get_or_create(direct_key=direct_key(user_a_id, user_b_id))
    for user_id in (user_a_id, user_b_id):
        ConversationMember.objects.get_or_create(conversation=conversation, user_id=user_id)
    return conversation


def create_message(conversation_id, sender_id, body):
    return Message.objects.create(conversation_id=conversation_id, sender_id=sender_id, body=body)


def broadcast_message(conversation_id, sender_username, body):
    """Pushes a message to live WebSocket clients, the same event the consumer sends.

    The message is already saved when this runs, so a channel-layer outage is logged instead of failing the request.
    """
    try:
        async_to_sync(get_channel_layer().group_send)(
            f'chat_{conversation_id}',
            {'type': 'chat_message', 'message': body, 'username': sender_username},
        )
    except Exception:
        logger.exception('Could not broadcast a message in conversation %s', conversation_id)
