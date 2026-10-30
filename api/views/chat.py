from datetime import datetime, timezone as dt_timezone

from django.db.models import Count, DateTimeField, F, OuterRef, Prefetch, Subquery, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from chat.models import Conversation, ConversationMember, Message
from chat.services import broadcast_message, create_message, direct_key, get_or_create_direct_conversation
from main.models import User

from ..pagination import MessageCursorPagination
from ..serializers import ConversationSerializer, MessageSerializer

EPOCH = datetime(1970, 1, 1, tzinfo=dt_timezone.utc)


class ConversationListView(generics.ListAPIView):
    serializer_class = ConversationSerializer

    def get_queryset(self):
        user = self.request.user
        my_last_read = ConversationMember.objects.filter(conversation=OuterRef('pk'), user=user).values('last_read_at')[:1]
        messages = Message.objects.filter(conversation=OuterRef('pk'))
        unread = (
            messages.exclude(sender=user)
            .filter(created_at__gt=Coalesce(OuterRef('my_last_read'), Value(EPOCH, output_field=DateTimeField())))
            .values('conversation')
            .annotate(total=Count('id'))
            .values('total')
        )
        return (
            Conversation.objects.filter(memberships__user=user)
            .annotate(
                my_last_read=Subquery(my_last_read),
                last_message_at=Subquery(messages.order_by('-created_at').values('created_at')[:1]),
                unread_count=Coalesce(Subquery(unread), Value(0)),
            )
            .prefetch_related(Prefetch('memberships', queryset=ConversationMember.objects.select_related('user')))
            .order_by(F('last_message_at').desc(nulls_last=True), '-id')
        )


class ConversationMessagesView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    pagination_class = MessageCursorPagination

    def get_other_user(self):
        return get_object_or_404(User, username=self.kwargs['username'])

    def get_queryset(self):
        key = direct_key(self.request.user.id, self.get_other_user().id)
        return Message.objects.filter(conversation__direct_key=key).select_related('sender').order_by('-id')

    def perform_create(self, serializer):
        viewer = self.request.user
        other = self.get_other_user()
        if other.pk == viewer.pk:
            raise ValidationError('You cannot message yourself.')
        conversation = get_or_create_direct_conversation(viewer.id, other.id)
        message = create_message(conversation.id, viewer.id, serializer.validated_data['body'])
        broadcast_message(conversation.id, viewer.username, message.body)
        serializer.instance = message


@extend_schema(request=None, responses={204: None})
class ConversationReadView(APIView):
    def post(self, request, username):
        other = get_object_or_404(User, username=username)
        ConversationMember.objects.filter(
            conversation__direct_key=direct_key(request.user.id, other.id),
            user=request.user,
        ).update(last_read_at=timezone.now())
        return Response(status=204)
