from django.contrib import admin

from .models import Conversation, ConversationMember, Message

admin.site.register(Conversation)
admin.site.register(ConversationMember)
admin.site.register(Message)
