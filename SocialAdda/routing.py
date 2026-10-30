from django.urls import path

from . import consumers

websocket_urlpatterns = [
    path('ws/<int:id>/', consumers.PersonalChatConsumer.as_asgi()),
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
]
