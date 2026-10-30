"""JWT helpers that tie every access token to the user's session version.

Each token carries `sv`, the user's session_version at the time it was issued. Bumping session_version (on a
password reset) makes all earlier access tokens fail at once, instead of living until they expire.
"""
from django.db.models import F
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from main.models import User


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    refresh['sv'] = user.session_version
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


class SessionTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['sv'] = user.session_version
        return token


def session_is_current(user, validated_token):
    return validated_token.get('sv', 0) == user.session_version


class SessionJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        if not session_is_current(user, validated_token):
            raise AuthenticationFailed('This session has ended. Please sign in again.', code='session_ended')
        return user


class SessionJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    """Tells drf-spectacular how this authenticator works, so /api/docs/ shows a bearer-token "Authorize" button."""

    target_class = 'api.auth.SessionJWTAuthentication'
    name = 'bearerAuth'

    def get_security_definition(self, auto_schema):
        return {'type': 'http', 'scheme': 'bearer', 'bearerFormat': 'JWT'}


def end_all_sessions(user):
    """Invalidates every access token the user holds, immediately."""
    User.objects.filter(pk=user.pk).update(session_version=F('session_version') + 1)
