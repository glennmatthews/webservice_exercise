import json
import logging
import re

from django.http import JsonResponse, HttpResponseNotAllowed, HttpResponseBadRequest
from django.utils.http import urlencode

from .models import Domain, Port, Path, Query

logger = logging.getLogger(__name__)


def urlinfo_v1(request, hostname_and_port, path=""):
    """Query the database to determine whether it's safe to access the given URL.

    Args:
      request (HttpRequest): GET request
      hostname_and_port (str): Such as "example.com:8080"
      path (str): Such as "secure/resources/article"

    Returns:
      JsonResponse: Currently a simple {safe: true} or {safe: false} value.
    """
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET"])
    logger.debug("hostname_and_port: \"%s\"", hostname_and_port)
    logger.debug("path: \"%s\"", path)
    logger.debug("GET parameters: %s", request.GET)

    m = re.match(r"^([^:]+)(?::(\d+))?$", hostname_and_port)
    if not m:
        return HttpResponseBadRequest(reason="Malformed domain-name and/or port")
    domain_name = m.group(1)
    port_number = m.group(2) or 80

    # First, do we have the whole domain flagged as unsafe?
    try:
        domain = Domain.objects.get(domain_name=domain_name)
    except Domain.DoesNotExist:
        domain = None

    if domain is not None and domain.unsafe:
        return JsonResponse({"safe": False})

    # If there is no entry for my.subdomain.example.com, but there is an entry
    # for its parent domains subdomain.example.com or example.com, and the
    # closest parent domain is globally blacklisted, then blacklist the
    # subdomain as well. However, we do NOT inherit more specific blacklists
    # (port, path, query) from a parent domain.
    if domain is None and '.' in domain_name:
        _, parent_domain = domain_name.split('.', 1)
        while '.' in parent_domain:
            try:
                parent = Domain.objects.get(domain_name=parent_domain)
                if parent.unsafe:
                    return JsonResponse({"safe": False})
            except Domain.DoesNotExist:
                # Try the next level of generality
                _, parent_domain = parent_domain.split('.', 1)

    if not domain:
        # No entries for this domain, so we must assume it's safe
        return JsonResponse({"safe": True})

    # The domain isn't flagged as globally unsafe.
    # Is the particular port in use on this domain flagged?

    try:
        port = Port.objects.get(domain=domain, port=port_number)
    except Port.DoesNotExist:
        # No entries for this port on this domain, so we assume it's safe
        return JsonResponse({"safe": True})

    if port.unsafe:
        return JsonResponse({"safe": False})

    # The domain:port isn't flagged as globally unsafe.
    # Is the particular path on this server flagged?

    try:
        path_obj = Path.objects.get(port=port, path=path)
    except Path.DoesNotExist:
        # No entries for this path, so we must assume it's safe
        # TODO: check for matches against parent directories?
        return JsonResponse({"safe": True})

    if path_obj.unsafe:
        return JsonResponse({"safe": False})

    # Normalize the query args to an alphabetically ordered string
    query = urlencode(sorted(request.GET.items(), key=lambda tup: tup[0]))

    try:
        query_obj = Query.objects.get(path=path_obj, query=query)
    except Query.DoesNotExist:
        # No entries for this query, so we must assume it's safe
        # TODO: check for partial matches?
        return JsonResponse({"safe": True})

    if query_obj.unsafe:
        return JsonResponse({"safe": False})

    return JsonResponse({"safe": True})
