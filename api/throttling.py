from rest_framework.permissions import SAFE_METHODS
from rest_framework.throttling import UserRateThrottle


class WriteThrottle(UserRateThrottle):
    """Caps how often a signed-in user can change data (posts, comments, likes, messages, follows).

    Reads are not limited here; the general per-user and per-anonymous limits still apply.
    """

    scope = 'writes'

    def allow_request(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return super().allow_request(request, view)
