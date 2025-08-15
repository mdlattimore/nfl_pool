from django.contrib import admin

from .models import Team, Game, Pick, Score


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name",)
    ordering = ("name",)
    search_fields = ("name",)

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ("home_team", "away_team", "week")

@admin.register(Pick)
class PickAdmin(admin.ModelAdmin):
    list_display = ("game", "picked_team", "user")

@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ("week", "points")