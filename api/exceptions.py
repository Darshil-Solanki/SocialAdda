import logging

from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def exception_handler(exc, context):
    """Every API error is JSON. Unexpected exceptions are logged and answered with a generic 500 body."""
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response
    logger.exception('Unhandled error in %s', context['view'].__class__.__name__, exc_info=exc)
    return Response({'detail': 'The server could not complete this request. Please try again.'}, status=500)
