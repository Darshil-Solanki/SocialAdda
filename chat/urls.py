from . import views
from django.urls import path

urlpatterns = [
    path('chat/',views.home,name="chathome" ),
    path('chat/<str:username>',views.chat,name="chat")
]