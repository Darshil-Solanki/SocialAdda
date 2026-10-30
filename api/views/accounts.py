import hashlib

from django.core.cache import cache
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.utils import extend_schema

from main.jobs import enqueue
from main.models import User
from main.services import revoke_user_tokens

from ..auth import end_all_sessions, issue_tokens
from main.tasks import send_password_reset_email_task

from ..serializers import (
    CurrentUserSerializer,
    LogoutSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSummarySerializer,
)


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tokens = issue_tokens(user)
        return Response({'user': UserSummarySerializer(user).data, **tokens}, status=201)


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


# Rotation grace: when two requests use the same refresh token within this many seconds (for example two browser
# tabs or two Next.js processes), both get the same new pair. The second use does not fail or log the user out.
REFRESH_GRACE_SECONDS = 30


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        raw = request.data.get('refresh')
        if not isinstance(raw, str):
            return super().post(request, *args, **kwargs)
        key = 'refresh-rotated:' + hashlib.sha256(raw.encode()).hexdigest()
        cached = cache.get(key)
        if cached and not _is_revoked(cached['refresh']):
            return Response(cached)
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            cache.set(key, dict(response.data), REFRESH_GRACE_SECONDS)
        return response


def _is_revoked(refresh_token):
    try:
        jti = RefreshToken(refresh_token)['jti']
    except TokenError:
        return True
    return OutstandingToken.objects.filter(jti=jti, blacklistedtoken__isnull=False).exists()


class LogoutView(APIView):
    """Ends the session by revoking its refresh token. Access tokens expire within five minutes."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(request=LogoutSerializer, responses={204: None})
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data['refresh']).blacklist()
        except TokenError:
            pass  # Already expired or revoked: the session is over either way.
        return Response(status=204)


class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = CurrentUserSerializer

    def get_object(self):
        return self.request.user


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(request=PasswordResetRequestSerializer, responses={202: None})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Always answer the same way, so the endpoint cannot be used to find registered emails.
        for user in User.objects.filter(email__iexact=serializer.validated_data['email'], is_active=True):
            enqueue(send_password_reset_email_task, user.pk)
        return Response(status=202)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(request=PasswordResetConfirmSerializer, responses={204: None})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])
        # A reset is usually a response to a compromised password, so every existing session ends too.
        revoke_user_tokens(user)
        end_all_sessions(user)
        return Response(status=204)
