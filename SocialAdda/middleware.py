from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from api.auth import session_is_current
from main.models import User


# The token travels as a WebSocket subprotocol: new WebSocket(url, ['socialadda', token]).
# Browsers cannot send an Authorization header on a WebSocket, and URLs end up in proxy and server logs.
SUBPROTOCOL = 'socialadda'


def accepted_subprotocol(scope):
    """The subprotocol to echo when accepting the socket: only when the client offered ours."""
    return SUBPROTOCOL if SUBPROTOCOL in scope.get('subprotocols', []) else None


class JwtAuthMiddleware(BaseMiddleware):
    """Authenticates a WebSocket with the access JWT sent as a subprotocol (see SUBPROTOCOL)."""

    async def __call__(self, scope, receive, send):
        offered = scope.get('subprotocols', [])
        if SUBPROTOCOL in offered:
            tokens = [protocol for protocol in offered if protocol != SUBPROTOCOL]
            if tokens:
                scope['user'] = await self.get_user(tokens[0])
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_user(self, raw_token):
        try:
            token = AccessToken(raw_token)
            user = User.objects.get(id=token['user_id'], is_active=True)
        except (TokenError, KeyError, User.DoesNotExist):
            return AnonymousUser()
        # Same rule as REST: a token from before the last session reset is refused.
        if not session_is_current(user, token):
            return AnonymousUser()
        return user
