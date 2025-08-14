from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Team(models.Model):
    name = models.CharField(max_length=100)
    alias = models.CharField(max_length=100)

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
    points = models.PositiveIntegerField(default=1)

    # def save(self, *args, **kwargs):
    #     # Keep track of whether winner was just set/changed
    #     winner_changed = False
    #     if self.pk:  # existing game
    #         old = Game.objects.filter(pk=self.pk).first()
    #         if old and old.winner != self.winner:
    #             winner_changed = True
    #
    #     super().save(*args, **kwargs)  # save the game first
    #
    #     # If winner changed, update all related picks
    #     if self.winner and winner_changed:
    #         from .models import Pick
    #         picks = Pick.objects.filter(game=self)
    #         for pick in picks:
    #             pick.points_earned = self.points if pick.picked_team == self.winner else 0
    #             pick.save()
    def save(self, *args, **kwargs):
        winner_changed = False
        if self.pk:  # existing game
            old = Game.objects.filter(pk=self.pk).first()
            if old and old.winner != self.winner:
                winner_changed = True

        super().save(*args, **kwargs)  # save game first

        if winner_changed:
            from .models import Pick

            if self.winner:
                # Set correct picks
                Pick.objects.filter(game=self, picked_team=self.winner).update(
                    points_earned=self.points)
                # Set incorrect picks
                Pick.objects.filter(game=self).exclude(
                    picked_team=self.winner).update(points_earned=0)
            else:
                # Winner cleared — reset all points
                Pick.objects.filter(game=self).update(points_earned=0)

    def __str__(self):
        return f"Week {self.week}: {self.away_team} @ {self.home_team}"


class Pick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    picked_team = models.ForeignKey(Team, on_delete=models.CASCADE)
    points_earned = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "game")

    def __str__(self):
        return f"{self.user.username} picked {self.picked_team} for {self.game}"


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    week = models.PositiveSmallIntegerField()
    points = models.IntegerField(default=0)

    class Meta:
        unique_together = ("user", "week")