from django.urls import path

from . import views

urlpatterns = [
    path("1/<hostname_and_port>/", views.urlinfo_v1, name="urlinfo_v1"),
    path("1/<hostname_and_port>/<path:path>", views.urlinfo_v1, name="urlinfo_v1"),
]
