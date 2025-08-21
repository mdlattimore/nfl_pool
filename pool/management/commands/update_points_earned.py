from django.core.management.base import BaseCommand
from pool.models import Game, Pick

UNIQUE_CORRECT_BONUS = 1

class Command(BaseCommand):
    help = "Update points_earned and apply unique correct pick bonuses."

    def handle(self, *args, **options):
        total_updated = 0
        total_bonus_awarded = 0

        games_with_winner = Game.objects.exclude(winner__isnull=True)

        for game in games_with_winner:
            picks = list(Pick.objects.filter(game=game))

            # Identify correct picks
            correct_picks = [p for p in picks if p.picked_team_id == game.winner_id]

            # Update points_earned for all picks
            for pick in picks:
                pick.points_earned = game.points if pick.picked_team_id == game.winner_id else 0
                total_updated += 1
                pick.save()

            # Apply bonus if exactly one correct pick exists
            if len(correct_picks) == 1:
                unique_pick = correct_picks[0]
                if unique_pick.bonus_points < UNIQUE_CORRECT_BONUS:
                    unique_pick.bonus_points = UNIQUE_CORRECT_BONUS
                    unique_pick.save()
                    total_bonus_awarded += 1
                    self.stdout.write(
                        f"Applied UNIQUE_CORRECT_BONUS to Pick(id={unique_pick.id}, user={unique_pick.user.username})"
                    )

        self.stdout.write(self.style.SUCCESS(
            f"Finished updating {total_updated} picks and awarded {total_bonus_awarded} unique correct bonuses."
        ))

# pool/management/commands/audit_picks.py

