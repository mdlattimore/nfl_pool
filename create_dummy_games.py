from django.utils import timezone
from pool.models import Team, Game, Pick
from django.contrib.auth import get_user_model

User = get_user_model()

# Pick a user to assign the pick to
user = User.objects.first()  # or filter for your test user

# Pick any two existing teams
home_team = Team.objects.first()
away_team = Team.objects.exclude(id=home_team.id).first()

# Create a past game (yesterday) in week 0
past_game = Game.objects.create(
    week=0,
    home_team=home_team,
    away_team=away_team,
    game_time=timezone.now() - timezone.timedelta(days=1),
    winner=home_team  # optional, only if you want to test win/loss coloring
)

# Create a pick for that game
Pick.objects.create(
    user=user,
    game=past_game,
    picked_team=home_team
)

print("Created week 0 game and pick for testing Past Picks.")
