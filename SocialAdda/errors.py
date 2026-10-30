"""JSON error pages for the API. Other paths keep Django's default pages (the admin and the docs)."""
from django.http import JsonResponse
from django.views import defaults

API_PREFIX = '/api/'


def _is_api(request):
    return request.path.startswith(API_PREFIX)


def bad_request(request, exception, *args, **kwargs):
    if _is_api(request):
        return JsonResponse({'detail': 'This request was rejected. Check the host name and the request data.'}, status=400)
    return defaults.bad_request(request, exception)


def page_not_found(request, exception, *args, **kwargs):
    if _is_api(request):
        return JsonResponse({'detail': 'Not found.'}, status=404)
    return defaults.page_not_found(request, exception)


def server_error(request, *args, **kwargs):
    if _is_api(request):
        return JsonResponse({'detail': 'The server could not complete this request. Please try again.'}, status=500)
    return defaults.server_error(request)
