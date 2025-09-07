# # pool/management/commands/recalculate_pick_points.py
#
# from django.core.management.base import BaseCommand
# from pool.models import Pick
#
# class Command(BaseCommand):
#     help = "Recalculate points_earned and is_correct for all picks."
#
#     def handle(self, *args, **options):
#         picks = Pick.objects.select_related('game', 'picked_team', 'game__winner').all()
#         updated_count = 0
#
#         for pick in picks:
#             game = pick.game
#             if game.winner:
#                 pick.is_correct = pick.picked_team == game.winner
#                 pick.points_earned = game.points if pick.is_correct else 0
#                 pick.save(update_fields=['is_correct', 'points_earned'])
#                 updated_count += 1
#
#         self.stdout.write(self.style.SUCCESS(
#             f"Recalculated points for {updated_count} picks."
#         ))
# pool/management/commands/recalculate_pick_points.py

from django.core.management.base import BaseCommand

from pool.models import Pick


class Command(BaseCommand):
    help = "Recalculate points and correctness for all picks based on current game winners and points."

    def handle(self, *args, **options):
        updated = 0
        picks = Pick.objects.select_related('game', 'picked_team')
        for pick in picks:
            game = pick.game
            if game.winner:
                pick.is_correct = pick.picked_team == game.winner
                pick.points_earned = game.points if pick.is_correct else 0
                pick.save(update_fields=['is_correct', 'points_earned'])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} picks."))
