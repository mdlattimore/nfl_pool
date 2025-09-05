# pool/middleware.py
from django.shortcuts import render
from django.urls import resolve

from .models import PoolSettings

class SiteMaintenanceMiddleware:
    """
    Shows a maintenance page if site_maintenance is True in PoolSettings.
    Exempts superusers and all admin/login pages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get current settings
        settings = PoolSettings.objects.first()
        site_maintenance = getattr(settings, "site_maintenance", False)

        # Safely check if user is superuser
        user_is_super = getattr(getattr(request, "user", None), "is_superuser", False)

        # Resolve current path to see if it's in admin
        try:
            resolver_match = resolve(request.path)
            is_admin = resolver_match.app_name == "admin"
        except:
            is_admin = False

        # Show maintenance page if maintenance is on and user is not super + not admin
        if site_maintenance and not user_is_super and not is_admin:
            return render(request, "maintenance.html")

        # Otherwise continue normally
        return self.get_response(request)
