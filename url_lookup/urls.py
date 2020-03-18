from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^1/(?P<hostname_and_port>[^/]+)/(?P<path>.*)",
        views.urlinfo_v1, name="urlinfo_v1"),
]
