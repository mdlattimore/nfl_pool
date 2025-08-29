import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from pool.models import Team, Game, Pick

User = get_user_model()

# Usage
# python manage.py create_past_week 0 --games 5
# 0 → week number
#--games 5 → number of games to create (default is 5)

class Command(BaseCommand):
    help = "Quickly generate a past week's games, picks, and winners for testing."

    def add_arguments(self, parser):
        parser.add_argument('week', type=int, help='Week number (e.g., 0)')
        parser.add_argument(
            '--games', type=int, default=5, help='Number of games to create (default 5)'
        )
        parser.add_argument('--num_weeks', type=int, default=5,
            help='Number of games to create (default 5)'
        )

    def handle(self, *args, **options):
        week_number = options['week']
        num_games = options['games']
        num_weeks = options['num_weeks']

        teams = list(Team.objects.all())
        if len(teams) < num_games * 2:
            self.stdout.write(self.style.ERROR(
                f"Not enough teams for {num_games} games. Add more teams first."
            ))
            return

        users = User.objects.all()
        if not users:
            self.stdout.write(self.style.ERROR("No users found. Create some test users first."))
            return

        # past
        # week_start = timezone.now() - timedelta(weeks=0)
        # future
        week_start = timezone.now() + timedelta(weeks=0)


        games = []

        # Create games
        for i in range(num_games):
            home = teams[i * 2]
            away = teams[i * 2 + 1]
            game_time = week_start + timedelta(hours=i*3)  # stagger times
            game = Game.objects.create(
                week=week_number,
                home_team=home,
                away_team=away,
                game_time=game_time,
                points=1  # default points per game
            )
            games.append(game)

        self.stdout.write(self.style.SUCCESS(
            f"Created {num_games} games for week {week_number} without picks "
            f"or winners."
        ))