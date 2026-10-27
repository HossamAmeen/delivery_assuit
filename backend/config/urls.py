from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/auth/", include("apps.users.urls")),
    path("api/v1/users/", include("apps.users.admin_urls")),
    path("api/v1/locations/", include("apps.locations.urls")),
    path("api/v1/shop/", include("apps.shops.urls")),
    path("api/v1/shops/", include("apps.shops.public_urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/staff/", include("apps.shops.staff_urls")),
    path("api/v1/staff/", include("apps.orders.staff_urls")),
    path("api/v1/staff/", include("apps.audit.urls")),
    path("api/v1/notifications/", include("apps.notifications.urls")),
    path("api/v1/drivers/", include("apps.orders.driver_urls")),
    path("api/v1/addresses/", include("apps.locations.address_urls")),
]

# API docs: on in development/staging, off (404) in production unless API_DOCS_ENABLED.
if settings.API_DOCS_ENABLED:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"
        ),
        path(
            "api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"
        ),
    ]

handler404 = "common.views.not_found"
handler500 = "common.views.server_error"
