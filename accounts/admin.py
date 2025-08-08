from django.contrib import admin # type: ignore
from django.contrib.auth import get_user_model # type: ignore
from django.contrib.auth.admin import UserAdmin # type: ignore

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = [
        "email",
        "username",
    ]

    # Explicitly define add_fieldsets to prevent unexpected fields
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)

# admin.site.site_title = ""
admin.site.site_header = "NFL Pool"
# admin.site.index_title = ""