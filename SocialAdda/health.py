from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness and dependency check for load balancers and uptime monitors."""
    checks = {}
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'ok'
    except Exception:
        checks['database'] = 'error'

    try:
        cache.set('healthz', '1', 10)
        checks['cache'] = 'ok' if cache.get('healthz') == '1' else 'error'
    except Exception:
        checks['cache'] = 'error'

    healthy = all(value == 'ok' for value in checks.values())
    return JsonResponse({'status': 'ok' if healthy else 'degraded', 'checks': checks}, status=200 if healthy else 503)
