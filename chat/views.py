from django.shortcuts import render
from main.models import User
from .models import ChatModel
# Create your views here.
def home(request):
    user_obj = User.objects.get(username=request.user.username)
    users = User.objects.exclude(username=request.user.username) 
    return render(request,'chat_index.html',context={'user':user_obj,'users':users,'page':'chat-index'})
def chat(request, username):
    user_obj = User.objects.get(username=username)
    user=User.objects.get(username=request.user.username)
    if request.user.id > user_obj.id:
        thread_name = f'chat_{request.user.id}-{user_obj.id}'
    else:
        thread_name = f'chat_{user_obj.id}-{request.user.id}'
    message_objs = ChatModel.objects.filter(thread_name=thread_name)
    return render(request, 'main_chat.html', context={'user': user,'ruser':user_obj,'messages': message_objs,'page':'chat-messages'})