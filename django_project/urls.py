from django.conf import settings
from django.contrib import admin
from django.urls import path, include

from accounts.views import CustomPasswordChangeView  # wherever your view is
from pool.admin import pool_admin_site

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/password/change/", CustomPasswordChangeView.as_view(),
         name="account_change_password"),
    path('markdownx/', include('markdownx.urls')),
    path("accounts/", include("allauth.urls")),
    # Disabling to make home a generic home page in the off season
    # path("", include("pool.urls")),
    path("", include("pages.urls")),
    path("pooladmin/", pool_admin_site.urls),  # <- important

]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path("__debug__/", include(debug_toolbar.urls)),
                  ] + urlpatterns
