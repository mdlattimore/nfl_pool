# pool/management/commands/audit_picks.py
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from pool.models import Game, Pick, User

class Command(BaseCommand):
    help = "Audit picks, selections, and scoring for all weeks."

    def handle(self, *args, **options):
        users = User.objects.all()
        weeks = Game.objects.values_list('week', flat=True).distinct().order_by('-week')  # most recent first

        # Prepare CSV
        today_str = datetime.now().strftime("%Y%m%d")
        filename = f"pick_audit_{today_str}.csv"

        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Week', 'Game', 'Winner', 'Points', 'User', 'Picked_Team', 'Status', 'Points_Earned']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for week in weeks:
                self.stdout.write(f"=== Week {week} ===")
                games = Game.objects.filter(week=week).order_by('game_time')

                for game in games:
                    winner_name = game.winner.alias if game.winner else 'TBD'
                    self.stdout.write(f"{game.away_team.alias} @ {game.home_team.alias} (Winner: {winner_name}, Points: {game.points})")
                    picks = Pick.objects.filter(game=game).select_related('user', 'picked_team')

                    for pick in picks:
                        correct = pick.picked_team == game.winner if game.winner else None
                        points = pick.points_earned
                        status = "Correct" if correct else ("Incorrect" if correct == False else "Pending")
                        self.stdout.write(f"  {pick.user.username}: Picked {pick.picked_team.alias}, {status}, Points: {points}")

                        # Write to CSV
                        writer.writerow({
                            'Week': week,
                            'Game': f"{game.away_team.alias} @ {game.home_team.alias}",
                            'Winner': winner_name,
                            'Points': game.points,
                            'User': pick.user.username,
                            'Picked_Team': pick.picked_team.alias,
                            'Status': status,
                            'Points_Earned': points,
                        })

                self.stdout.write("")  # blank line between weeks

        self.stdout.write(f"\nAudit saved to {filename}")
