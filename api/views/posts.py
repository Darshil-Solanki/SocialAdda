from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from django.db.models import Count
from rest_framework import generics
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from main.feeds import following_page_ids
from main.jobs import enqueue
from main.models import Comment, Post
from main.selectors import posts_with_viewer_state, saved_posts
from main.services import add_comment, remove_stored_files, set_bookmark, set_like

from main.tasks import create_thumbnail_task, fanout_post_task

from ..pagination import CommentCursorPagination, PostCursorPagination
from ..permissions import IsAuthorOrReadOnly
from ..serializers import CommentSerializer, PostSerializer


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = PostCursorPagination

    def get_queryset(self):
        queryset = posts_with_viewer_state(self.request.user)
        author = self.request.query_params.get('author')
        if author:
            queryset = queryset.filter(creater__username=author)
        return queryset

    def perform_create(self, serializer):
        post = serializer.save(creater=self.request.user)
        enqueue(fanout_post_task, post.pk)
        if post.content_image:
            enqueue(create_thumbnail_task, post.pk)


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        return posts_with_viewer_state(self.request.user)

    def perform_update(self, serializer):
        previous = [serializer.instance.content_image.name, serializer.instance.content_thumbnail.name]
        remove = serializer.validated_data.pop('remove_image', False)
        replacing = bool(serializer.validated_data.get('content_image'))
        if remove and not replacing:
            post = serializer.save(content_image='', content_thumbnail='')
            remove_stored_files(post, [name for name in previous if name])
            return
        if replacing:
            # Clear the old thumbnail in the same save. Otherwise the feed keeps pointing at a file that is
            # about to be deleted until the background task replaces it.
            post = serializer.save(content_thumbnail='')
            remove_stored_files(post, [name for name in previous if name])
            enqueue(create_thumbnail_task, post.pk)
            return
        serializer.save()

    def perform_destroy(self, instance):
        files = [instance.content_image.name, instance.content_thumbnail.name]
        instance.delete()
        remove_stored_files(instance, [name for name in files if name])


class FollowingFeedView(APIView):
    """Posts from people the viewer follows, read from the Redis feed index (see main/feeds.py)."""

    page_size = 10

    @extend_schema(responses=PostSerializer(many=True))
    def get(self, request):
        before = request.query_params.get('before')
        if before is not None and not before.isdigit():
            raise ValidationError({'before': ['Expected a post id.']})
        ids = following_page_ids(request.user, before=int(before) if before else None, limit=self.page_size)
        posts = posts_with_viewer_state(request.user).in_bulk(ids)
        ordered = [posts[post_id] for post_id in ids if post_id in posts]
        next_url = None
        if len(ids) == self.page_size:
            next_url = request.build_absolute_uri(f'?before={ids[-1]}')
        return Response({
            'next': next_url,
            'previous': None,
            'results': PostSerializer(ordered, many=True, context={'request': request}).data,
        })


class SavedPostsView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = PostCursorPagination

    def get_queryset(self):
        return saved_posts(self.request.user)


@extend_schema(request=None, responses={204: None})
class PostLikeView(APIView):
    def post(self, request, pk):
        set_like(get_object_or_404(Post, pk=pk), request.user, liked=True)
        return Response(status=204)

    def delete(self, request, pk):
        set_like(get_object_or_404(Post, pk=pk), request.user, liked=False)
        return Response(status=204)


@extend_schema(request=None, responses={204: None})
class PostBookmarkView(APIView):
    def post(self, request, pk):
        set_bookmark(get_object_or_404(Post, pk=pk), request.user, saved=True)
        return Response(status=204)

    def delete(self, request, pk):
        set_bookmark(get_object_or_404(Post, pk=pk), request.user, saved=False)
        return Response(status=204)


class PostCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    pagination_class = CommentCursorPagination

    def get_post(self):
        if not hasattr(self, '_post'):
            self._post = get_object_or_404(Post, pk=self.kwargs['pk'])
        return self._post

    def get_queryset(self):
        # Top-level comments by default; ?parent=<id> lists the replies to one comment.
        queryset = Comment.objects.filter(post=self.get_post()).select_related('commenter').annotate(
            reply_count=Count('replies'),
        )
        parent = self.request.query_params.get('parent')
        if parent is None:
            return queryset.filter(parent__isnull=True)
        if not parent.isdigit():
            raise ValidationError({'parent': ['Expected a comment id.']})
        return queryset.filter(parent_id=int(parent))

    def perform_create(self, serializer):
        parent = serializer.validated_data.get('parent')
        try:
            comment = add_comment(self.get_post(), self.request.user, serializer.validated_data['comment_content'], parent)
        except ValueError as error:
            raise ValidationError({'parent': [str(error)]})
        serializer.instance = comment
        serializer.instance.reply_count = 0
