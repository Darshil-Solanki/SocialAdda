from rest_framework.pagination import CursorPagination, LimitOffsetPagination


class PostCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-id'


class CommentCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-id'


class MessageCursorPagination(CursorPagination):
    page_size = 30
    ordering = '-id'


class NotificationCursorPagination(CursorPagination):
    page_size = 20
    ordering = '-id'


class SuggestionPagination(LimitOffsetPagination):
    default_limit = 6
    max_limit = 50
