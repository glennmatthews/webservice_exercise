import json
import logging

from django.http import JsonResponse

logger = logging.getLogger(__name__)


def urlinfo_v1(request, hostname_and_port, path):
    """Query the database to determine whether it's safe to access the given URL.

    Args:
      request (HttpRequest): GET request
      hostname_and_port (str): Such as "example.com:8080"
      path (str): Such as "secure/resources/article"

    Returns:
      JsonResponse: Currently a simple {safe: true} or {safe: false} value.
    """
    if request.method != "GET":
        return JsonResponse({}, status="400")
    logger.debug("hostname_and_port: \"%s\"", hostname_and_port)
    logger.debug("path: \"%s\"", path)
    logger.debug("GET parameters: %s", request.GET)
    return JsonResponse({"safe": True})
