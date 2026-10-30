from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import Notification

from ..pagination import NotificationCursorPagination
from ..serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = NotificationCursorPagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related('actor').order_by('-id')


class NotificationUnreadCountView(APIView):
    @extend_schema(responses={200: dict})
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
        return Response({'count': count})


@extend_schema(request=None, responses={204: None})
class NotificationReadView(APIView):
    def post(self, request):
        Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
        return Response(status=204)
