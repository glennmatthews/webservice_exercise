from django.contrib import admin

from .models import Domain, Port, Path, Query

admin.site.register(Domain)
admin.site.register(Port)
admin.site.register(Path)
admin.site.register(Query)
