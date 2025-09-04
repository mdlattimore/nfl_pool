# pool/admin.py

from django.contrib import admin, messages
from .models import Team, Game, Pick, Score, PoolSettings, Email
from django import forms
from django.urls import path
from django.http import JsonResponse
from django.core.management import call_command
from io import StringIO

class PoolAdmin(admin.AdminSite):
    site_header = 'NFL Pool Administration'
    site_title = 'NFL Pool Administration'
    site_index_title = 'NFL Pool Administration'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "update_points/",
                self.admin_view(self.update_points_view),
                name="update_points",
            ),
        ]
        return custom_urls + urls

    def update_points_view(self, request):
        """AJAX view to run the command and return JSON output."""
        output = StringIO()
        try:
            call_command("update_points_earned", stdout=output)
            status = "success"
        except Exception as e:
            output.write(str(e))
            status = "error"

        return JsonResponse({
            "status": status,
            "output": output.getvalue(),
        })


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)
    search_fields = ("name",)

class GameAdminForm(forms.ModelForm):
    class Meta:
        model = Game
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Limit the winner choices to just home_team and away_team
            self.fields['winner'].queryset = self.fields['winner'].queryset.filter(
                pk__in=[self.instance.home_team_id, self.instance.away_team_id]
            )


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    form = GameAdminForm
    list_display = ("home_team", "away_team", "week")
    list_filter = ("week",)  # adds a sidebar filter for weeks




@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ("game", "picked_team", "user")


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("week", "points")

@admin.register(PoolSettings)
class PoolSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # only allow adding if no instance exists
        return not PoolSettings.objects.exists()

@admin.register(Email)
class EmailAdmin(admin.ModelAdmin):
    list_display = ("date",)


# Register models with custom admin site
pool_admin_site = PoolAdmin(name="pooladmin")
pool_admin_site.register(Pick)
pool_admin_site.register(Game)
