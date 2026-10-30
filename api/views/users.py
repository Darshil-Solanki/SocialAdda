from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from main.models import User
from main.selectors import suggestion_queryset, user_search_queryset
from main.services import SelfFollowError, set_follow

from ..pagination import SuggestionPagination
from ..serializers import UserProfileSerializer, UserSearchSerializer, UserSummarySerializer


class UserSearchView(generics.ListAPIView):
    serializer_class = UserSearchSerializer
    pagination_class = SuggestionPagination

    def get_queryset(self):
        return user_search_queryset(self.request.user, self.request.query_params.get('q', '').strip())


class SuggestionsView(generics.ListAPIView):
    serializer_class = UserSummarySerializer
    pagination_class = SuggestionPagination

    def get_queryset(self):
        return suggestion_queryset(self.request.user)


class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserProfileSerializer
    lookup_field = 'username'
    queryset = User.objects.all()


@extend_schema(request=None, responses={204: None})
class UserFollowView(APIView):
    def post(self, request, username):
        target = get_object_or_404(User, username=username)
        try:
            set_follow(request.user, target, follow=True)
        except SelfFollowError as error:
            return Response({'detail': str(error)}, status=400)
        return Response(status=204)

    def delete(self, request, username):
        target = get_object_or_404(User, username=username)
        set_follow(request.user, target, follow=False)
        return Response(status=204)
