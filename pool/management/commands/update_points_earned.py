# pool/management/commands/update_points_earned.py

from django.core.management.base import BaseCommand
from pool.models import Game, Pick

class Command(BaseCommand):
    help = "Update points_earned for all Picks based on the Game winner."

    def handle(self, *args, **options):
        updated_count = 0

        # Iterate over all games that have a winner set
        games_with_winner = Game.objects.exclude(winner__isnull=True)

        for game in games_with_winner:
            picks = Pick.objects.filter(game=game)
            for pick in picks:
                correct = pick.picked_team == game.winner
                new_points = game.points if correct else 0

                if pick.points_earned != new_points:
                    pick.points_earned = new_points
                    pick.save()
                    updated_count += 1
                    self.stdout.write(
                        f"Updated Pick(id={pick.id}) for Game(week={game.week}, {game.away_team} @ {game.home_team}): "
                        f"{'correct' if correct else 'incorrect'}, points_earned={new_points}"
                    )

        self.stdout.write(self.style.SUCCESS(f"Finished updating {updated_count} picks."))
