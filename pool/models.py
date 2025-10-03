from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import (
    TextField,
    F,
    ExpressionWrapper,
    FloatField,
    Case,
    When,
    Value,
    Q)
from markdownx.models import MarkdownxField

User = get_user_model()


class Team(models.Model):
    CONFERENCE_CHOICES = (
    ("AFC", "AFC"),
    ("NFC", "NFC"),
    )
    DIVISION_CHOICES = (
    ("North", "North"),
    ("South", "South"),
    ("East", "East"),
    ("West", "West"),
    )

    name = models.CharField(max_length=100)
    conference = models.CharField(max_length=10, choices=CONFERENCE_CHOICES,
                                  blank=True, null=True)
    division = models.CharField(max_length=10, choices=DIVISION_CHOICES, blank=True, null=True)
    alias = models.CharField(max_length=100)
    wins = models.IntegerField(default=0)
    losses = models.IntegerField(default=0)
    ties = models.IntegerField(default=0)

    @property
    def record(self):
        return f"{self.wins}-{self.losses}-{self.ties}"

    @property
    def winning_percentage(self):
        total = self.wins + self.losses + self.ties
        if total == 0:
            return 0.0
        return (self.wins + 0.5 * self.ties) / total

    @property
    def division_full(self):
        return f"{self.conference} {self.division}"

    def __str__(self):
        return self.name


class Game(models.Model):
    week = models.PositiveSmallIntegerField()
    home_team = models.ForeignKey(Team, related_name="home_team",
                                  on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name="away_team",
                                  on_delete=models.CASCADE)
    game_time = models.DateTimeField()
    winner = models.ForeignKey(Team, null=True, blank=True,
                               related_name="winner",
                               on_delete=models.SET_NULL)
    is_tie = models.BooleanField(default=False)
    points = models.PositiveIntegerField(default=1)

    # def save(self, *args, **kwargs):
    #     winner_changed = False
    #     if self.pk:  # existing game
    #         old = Game.objects.filter(pk=self.pk).first()
    #         if old and old.winner != self.winner:
    #             winner_changed = True
    #
    #     super().save(*args, **kwargs)  # save game first
    #
    #     if winner_changed:
    #         from .models import Pick
    #
    #         if self.winner:
    #             # Set correct picks
    #             Pick.objects.filter(game=self, picked_team=self.winner).update(
    #                 points_earned=self.points)
    #             # Set incorrect picks
    #             Pick.objects.filter(game=self).exclude(
    #                 picked_team=self.winner).update(points_earned=0)
    #         else:
    #             # Winner cleared — reset all points
    #             Pick.objects.filter(game=self).update(points_earned=0)

    def save(self, *args, **kwargs):
        winner_changed = False
        tie_changed = False

        if self.pk:  # existing game
            old = Game.objects.get(pk=self.pk).first()
            if old:
                if old.winner != self.winner:
                    winner_changed = True
                if old.is_tie != self.is_tie:
                    tie_changed = True
        super().save(*args, **kwargs)  # save game first

        # ----- Pick Scoring -----
        if winner_changed or tie_changed:
            from .models import Pick

            if self.is_tie:
                # All picks = 0 points
                Pick.objects.filter(game=self).update(points_earned=0)
            elif self.winner:
                # Correct picks
                Pick.objects.filter(game=self, picked_team=self.winner).update(points_earned=self.points)
                # Incorrect picks
                Pick.objects.filter(game=self).exclude(
                    picked_team=self.winner
                ).update(points_earned=0)
            else:
                # Undecided -- reset all points
                Pick.objects.filter(game=self).update(points_earned=0)

    def __str__(self):
        return f"Week {self.week}: {self.away_team} @ {self.home_team}"


class Pick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    picked_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    points_earned = models.PositiveIntegerField(default=0)
    bonus_points = models.PositiveIntegerField(default=0)
    is_correct = models.BooleanField(null=True, blank=True)

    @property
    def total_points(self):
        return self.points_earned + self.bonus_points

    class Meta:
        unique_together = ("user", "game")

    def __str__(self):
        return f"{self.user.username} picked {self.picked_team} for {self.game}"


class PoolSettings(models.Model):
    enforce_pick_window = models.BooleanField(default=True)
    site_maintenance = models.BooleanField(
        default=False,
        help_text="If enabled, only superusers can access the site. Others see a maintenance page."
    )

    def save(self, *args, **kwargs):
        # enforce only one row
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # prevent deletion
        pass

    def __str__(self):
        return "Pool Settings"

    class Meta:
        verbose_name = "Pool Settings"
        verbose_name_plural = "Pool Settings"


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week = models.PositiveSmallIntegerField()
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "week")


class Email(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    pool_data = models.JSONField(null=True, blank=True)
    game_recap_input_tokens = models.IntegerField(default=0)
    game_recap_output_tokens = models.IntegerField(default=0)
    game_recap_total_tokens = models.IntegerField(default=0)
    game_recap_results = models.TextField(null=True, blank=True)
    truncated_game_recap_results = models.TextField(null=True, blank=True)
    email_response_input_tokens = models.IntegerField(default=0)
    email_response_output_tokens = models.IntegerField(default=0)
    email_response_total_tokens = models.IntegerField(default=0)
    # text = models.TextField()
    email_text = MarkdownxField()
    total_input_tokens = models.IntegerField(default=0)
    total_output_tokens = models.IntegerField(default=0)
    total_combined_tokens = models.IntegerField(default=0)

    def __str__(self):
        return f"Email generated {self.date}"


class WeeklyNote(models.Model):
    week = models.PositiveSmallIntegerField()
    notes = TextField()

    def __str__(self):
        return f"Week {self.week} Notes"
