"""Content-Security-Policy for responses that Django serves itself (API, admin, API docs).

This is a plain middleware, so it works on Django 5.x and 6.x alike. Django 6 added a built-in CSP setting; the
project does not use it, so the policy stays the same when the Django version changes.
The Next.js pages get their own policy from frontend/proxy.ts.
"""

API_POLICY = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
# Swagger UI loads its assets from jsdelivr (drf-spectacular default) and runs one inline setup script.
DOCS_POLICY = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; "
    "frame-ancestors 'none'; base-uri 'self'"
)
ADMIN_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


class ContentSecurityPolicyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = self.policy_for(request.path)
        return response

    @staticmethod
    def policy_for(path):
        if path.startswith('/api/docs/'):
            return DOCS_POLICY
        if path.startswith('/admin/'):
            return ADMIN_POLICY
        return API_POLICY
