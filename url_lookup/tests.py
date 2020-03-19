from django.test import TestCase
from django.urls import reverse
from django.utils.http import urlencode

from .models import Domain, Port, Path, Query
from .views import urlinfo_v1


class UrlinfoV1Tests(TestCase):
    """Test cases for the urlinfo_v1 view function."""

    @staticmethod
    def get_url(hostname_and_port, path="", args=None):
        """Construct the URL for the given parameters."""
        if path:
            url = reverse("urlinfo_v1", args=(hostname_and_port, path))
        else:
            url = reverse("urlinfo_v1", args=(hostname_and_port,))
        if args:
            url += "?" + urlencode(args)
        return url

    def assert_safe(self, url):
        """The given URL should report as safe."""
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"safe": True})

    def assert_unsafe(self, url):
        """The given URL should report as unsafe."""
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"safe": False})

    def test_get_only(self):
        """Only GET requests are supported presently."""
        url = self.get_url("example.com")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Everything else should return an HTTP 405 error
        response = self.client.post(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.patch(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.put(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 405)

    def test_empty_db(self):
        """If there's nothing in the database, all URLs are assumed safe."""
        for url in [
            self.get_url("example.com"),
            self.get_url("example.com:8080"),
            self.get_url("example.com", "examples"),
            self.get_url("example.com:8080", "examples/more_examples/"),
            self.get_url("example.com", "examples", {"example": "my_example"}),
        ]:
            self.assert_safe(url)

    def test_match_domain(self):
        """An entire domain can be blacklisted."""
        Domain.objects.create(domain_name="malware.bad")
        for url in [
            self.get_url("malware.bad"),
            # TODO self.get_url("subdomain.malware.bad"),
            self.get_url("malware.bad:8080"),
            self.get_url("malware.bad", "path/is/irrelevant"),
            self.get_url("malware.bad", "path/is/irrelevant", {"param": "irrelevant"}),
        ]:
            self.assert_unsafe(url)

        # Make sure other domains are still presumed safe
        for url in [
            self.get_url("example.com"),
            self.get_url("example.com", "malware.bad"),
            self.get_url("example.com", "", {"domain_name": "malware.bad"}),
        ]:
            self.assert_safe(url)

    def test_match_domain_and_port(self):
        """A specific port on a domain can be blacklisted."""
        domain = Domain.objects.create(domain_name="mixed.bag", unsafe=False)
        Port.objects.create(domain=domain, port="666")

        # The domain as a whole is not blacklisted
        self.assert_safe(self.get_url("mixed.bag"))
        # Nor are other ports on this domain
        self.assert_safe(self.get_url("mixed.bag:6666"))

        # But any path and parameters on this host+port are blacklisted
        for url in [
            self.get_url("mixed.bag:666"),
            self.get_url("mixed.bag:666", "path/is/irrelevant"),
            self.get_url("mixed.bag:666", "path/is/irrelevant", {"param": "irrelevant"}),
        ]:
            self.assert_unsafe(url)

        # The port is mapped to a specific domain
        self.assert_safe(self.get_url("example.com:666"))

    def test_match_path(self):
        """A specific path on a domain can be blacklisted."""
        domain = Domain.objects.create(domain_name="mixed.bag", unsafe=False)
        port = Port.objects.create(domain=domain, unsafe=False) # port defaults to 80
        Path.objects.create(port=port, path="files/malware")

        # The domain and port as a whole are not blacklisted
        self.assert_safe(self.get_url("mixed.bag"))
        self.assert_safe(self.get_url("mixed.bag:80"))

        # But matches for this path on this server are blacklisted
        self.assert_unsafe(self.get_url("mixed.bag", "files/malware"))
        self.assert_unsafe(self.get_url("mixed.bag", "files/malware", {"param": "irrelevant"}))
        # TODO? self.get_url("mixed.bag", "files/malware/specific")

        # The path is mapped to a specific domain and port
        self.assert_safe(self.get_url("example.com", "files/malware"))
        self.assert_safe(self.get_url("mixed.bag:8080", "files/malware"))

    def test_match_query(self):
        """A specific GET query on a specific path can be blacklisted."""
        domain = Domain.objects.create(domain_name="mixed.bag", unsafe=False)
        port = Port.objects.create(domain=domain, unsafe=False)
        path = Path.objects.create(port=port, path="files", unsafe=False)
        Query.objects.create(path=path, query="unsafe=true&malware=true")

        # The domain, port, and path are not blacklisted
        self.assert_safe(self.get_url("mixed.bag"))
        self.assert_safe(self.get_url("mixed.bag:80"))
        self.assert_safe(self.get_url("mixed.bag:80", "files"))

        # But matches for this query on this path are blacklisted
        self.assert_unsafe(self.get_url("mixed.bag", "files",
                                        {"malware": "true", "unsafe": "true"}))
        # Ordering of query parameters shouldn't matter
        self.assert_unsafe(self.get_url("mixed.bag", "files",
                                        {"unsafe": "true", "malware": "true"}))

        # Partial matches do not get blacklisted
        self.assert_safe(self.get_url("mixed.bag", "files", {"unsafe": "true"}))

        # TODO - extra parameters shouldn't avoid blacklisting?
        # self.assert_unsafe(self.get_url("mixed.bag", "files",
        #                                 {"unsafe": "true", "malware": "true", "extra": 0}))
