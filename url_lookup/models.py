from django.db import models
from django.http import QueryDict
from django.utils.http import urlencode


class Domain(models.Model):
    """A given web domain - is it globally unsafe?"""
    domain_name = models.CharField(max_length=253, unique=True)
    unsafe = models.BooleanField(default=True)

    def __str__(self):
        return "{}{}".format(self.domain_name, " 👿" if self.unsafe else "")


class Port(models.Model):
    """A given port on a given domain - is it unsafe?"""
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    port = models.IntegerField(default=80)
    unsafe = models.BooleanField(default=True)

    def __str__(self):
        return "{}:{}{}".format(self.domain.domain_name, self.port,
                                " 👿" if self.unsafe else "")


class Path(models.Model):
    """A given path on a given domain/port - is it unsafe?"""
    port = models.ForeignKey(Port, on_delete=models.CASCADE)
    path = models.CharField(max_length=2000)
    unsafe = models.BooleanField(default=True)

    def __str__(self):
        return "{}:{}/{}{}".format(self.port.domain.domain_name, self.port.port,
                                   self.path, " 👿" if self.unsafe else "")


class Query(models.Model):
    """A given GET parameters query on a given domain/port/path - is it unsafe?"""
    path = models.ForeignKey(Path, on_delete=models.CASCADE)
    query = models.CharField(max_length=2000)
    unsafe = models.BooleanField(default=True)

    def __str__(self):
        return "{}:{}/{}?{}{}".format(self.path.port.domain.domain_name,
                                      self.path.port.port,
                                      self.path.path,
                                      self.query,
                                      " 👿" if self.unsafe else "")

    def save(self, *args, **kwargs):
        """Ensure the query string is normalized before saving it."""
        qd = QueryDict(self.query)
        self.query = urlencode(sorted(qd.items(), key=lambda tup: tup[0]))
        super().save(*args, **kwargs)
