from django.contrib import admin

from .models import Team, Game, Pick, Score
from django import forms


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




@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ("game", "picked_team", "user")






@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("week", "points")