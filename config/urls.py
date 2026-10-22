from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path


def healthz(request):
    """Plain-text liveness probe for the hosting platform."""
    return HttpResponse("ok", content_type="text/plain")


urlpatterns = [
    path("healthz/", healthz, name="healthz"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("", include("applications.urls")),
]
