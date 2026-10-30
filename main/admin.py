from django.contrib import admin

from .models import Comment, Follow, Post, PostBookmark, PostLike, User

admin.site.register(User)
admin.site.register(Post)
admin.site.register(PostLike)
admin.site.register(PostBookmark)
admin.site.register(Follow)
admin.site.register(Comment)
