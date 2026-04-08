from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse


def healthz(_request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("api/", include("reports.api_urls")),
    path("", include("reports.urls")),
    path("imports/", include("imports.urls")),
    path("publishing/", include("publishing.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
