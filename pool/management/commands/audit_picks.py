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
                        self.stdout.write(f"  {pick.user.username}: Picked "
                                          f"{pick.picked_team.alias}, "
                                          f"{status}, Points: "
                                          f"{points + pick.bonus_points}")

                        # Write to CSV
                        writer.writerow({
                            'Week': week,
                            'Game': f"{game.away_team.alias} @ {game.home_team.alias}",
                            'Winner': winner_name,
                            'Points': game.points,
                            'User': pick.user.username,
                            'Picked_Team': pick.picked_team.alias,
                            'Status': status,
                            'Points_Earned': points + pick.bonus_points,
                        })

                self.stdout.write("")  # blank line between weeks


        self.stdout.write(f"\nAudit saved to {filename}")

# from django.core.management.base import BaseCommand
# from django.contrib.auth import get_user_model
# from pool.models import Game, Pick
#
# class Command(BaseCommand):
#     help = "Audit picks without modifying any data."
#
#     def handle(self, *args, **options):
#         User = get_user_model()
#         users = User.objects.all()
#         weeks = Game.objects.values_list("week", flat=True).distinct().order_by("week")
#
#         self.stdout.write(self.style.SUCCESS("Starting audit of picks..."))
#
#         for user in users:
#             self.stdout.write(f"\nUser: {user.username}")
#             total_points = 0
#             issues_found = False
#
#             for week in weeks:
#                 picks = Pick.objects.filter(user=user, game__week=week)
#                 week_points = 0
#
#                 for pick in picks:
#                     game = pick.game
#                     correct = (game.winner_id == pick.picked_team_id)
#
#                     # what the points *should* be
#                     expected_points = 1 if correct else 0
#
#                     # compare stored values
#                     if pick.points_earned != expected_points:
#                         self.stdout.write(
#                             self.style.WARNING(
#                                 f"  Week {week} - Game {game.id}: "
#                                 f"Picked {pick.picked_team}, Winner {game.winner} → "
#                                 f"Expected points={expected_points}, Found={pick.points_earned}"
#                             )
#                         )
#                         issues_found = True
#
#                     week_points += pick.points_earned + pick.bonus_points
#
#                 total_points += week_points
#
#             if not issues_found:
#                 self.stdout.write(self.style.SUCCESS(f"  No issues found. Total points = {total_points}"))
#
#         # Audit unique pick bonus logic
#         self.stdout.write("\nChecking unique pick bonus logic...")
#         for week in weeks:
#             for game in Game.objects.filter(week=week, winner__isnull=False):
#                 picks = Pick.objects.filter(game=game)
#                 pick_counts = {}
#
#                 for pick in picks:
#                     if game.winner_id == pick.picked_team_id:
#                         pick_counts[pick.picked_team_id] = pick_counts.get(pick.picked_team_id, 0) + 1
#
#                 # identify unique winners
#                 for team_id, count in pick_counts.items():
#                     if count == 1:  # unique correct pick
#                         unique_pick = picks.filter(picked_team_id=team_id).first()
#                         if unique_pick and unique_pick.bonus_points != 1:
#                             self.stdout.write(
#                                 self.style.WARNING(
#                                     f"  Week {week} - Game {game.id}: User {unique_pick.user.username} "
#                                     f"had unique correct pick {unique_pick.picked_team}, "
#                                     f"Expected bonus=1, Found={unique_pick.bonus_points}"
#                                 )
#                             )
#
#         self.stdout.write(self.style.SUCCESS("\nAudit completed. No changes were made."))
#
