from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from accounts.views import CustomPasswordChangeView  # wherever your view is


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/password/change/", CustomPasswordChangeView.as_view(),
         name="account_change_password"),

    path("accounts/", include("allauth.urls")),
    path("", include("pages.urls")),
    path("pool/", include("pool.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
        path("__debug__/", include(debug_toolbar.urls)),
    ] + urlpatterns
