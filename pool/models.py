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

    def __str__(self):
        return f"Week {self.week}: {self.away_team} @ {self.home_team}"


class Pick(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    picked_team = models.ForeignKey(Team, on_delete=models.CASCADE)

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