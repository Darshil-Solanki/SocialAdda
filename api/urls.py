from django.urls import path

from .views.accounts import (
    CurrentUserView,
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
)
from .views.chat import ConversationListView, ConversationMessagesView, ConversationReadView
from .views.notifications import NotificationListView, NotificationReadView, NotificationUnreadCountView
from .views.posts import (
    FollowingFeedView,
    PostBookmarkView,
    PostCommentListCreateView,
    PostDetailView,
    PostLikeView,
    PostListCreateView,
    SavedPostsView,
)
from .views.users import SuggestionsView, UserDetailView, UserFollowView, UserSearchView

urlpatterns = [
    path('auth/register/', RegisterView.as_view(), name='api-register'),
    path('auth/token/', LoginView.as_view(), name='api-token'),
    path('auth/token/refresh/', RefreshView.as_view(), name='api-token-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='api-password-reset'),
    path('auth/password-reset/confirm/', PasswordResetConfirmView.as_view(), name='api-password-reset-confirm'),
    path('me/', CurrentUserView.as_view(), name='api-me'),

    path('posts/', PostListCreateView.as_view(), name='api-posts'),
    path('posts/<int:pk>/', PostDetailView.as_view(), name='api-post-detail'),
    path('posts/<int:pk>/like/', PostLikeView.as_view(), name='api-post-like'),
    path('posts/<int:pk>/bookmark/', PostBookmarkView.as_view(), name='api-post-bookmark'),
    path('posts/<int:pk>/comments/', PostCommentListCreateView.as_view(), name='api-post-comments'),
    path('feed/following/', FollowingFeedView.as_view(), name='api-feed-following'),
    path('saved/', SavedPostsView.as_view(), name='api-saved'),

    # 'suggestions' must come before the <username> route so it is not read as a username.
    path('users/', UserSearchView.as_view(), name='api-users'),
    path('users/suggestions/', SuggestionsView.as_view(), name='api-suggestions'),
    path('users/<str:username>/', UserDetailView.as_view(), name='api-user-detail'),
    path('users/<str:username>/follow/', UserFollowView.as_view(), name='api-user-follow'),

    path('notifications/', NotificationListView.as_view(), name='api-notifications'),
    path('notifications/unread-count/', NotificationUnreadCountView.as_view(), name='api-notifications-unread'),
    path('notifications/read/', NotificationReadView.as_view(), name='api-notifications-read'),

    path('conversations/', ConversationListView.as_view(), name='api-conversations'),
    path('conversations/<str:username>/messages/', ConversationMessagesView.as_view(), name='api-messages'),
    path('conversations/<str:username>/read/', ConversationReadView.as_view(), name='api-conversation-read'),
]
