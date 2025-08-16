# pool/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from .models import Game, Pick
#
# # --- Game signal: update all related picks when winner changes ---
# @receiver(post_save, sender=Game)
# def update_picks_on_game_change(sender, instance, **kwargs):
#     """
#     Update all picks for this game whenever the Game is saved.
#     Points are set according to Game.points and correctness.
#     """
#     picks = Pick.objects.filter(game=instance)
#     for pick in picks:
#         if instance.winner:
#             pick.is_correct = pick.picked_team == instance.winner
#             pick.points_earned = instance.points if pick.is_correct else 0
#         else:
#             # No winner yet
#             pick.is_correct = None
#             pick.points_earned = 0
#         pick.save(update_fields=["is_correct", "points_earned"])
#
#
# # --- Pick signal: update pick correctness/points when pick is saved ---
# @receiver(post_save, sender=Pick)
# def update_pick_on_save(sender, instance, **kwargs):
#     """
#     Update a pick's correctness and points when the Pick itself is created or changed.
#     """
#     game = instance.game
#     if game.winner:
#         instance.is_correct = instance.picked_team == game.winner
#         instance.points_earned = game.points if instance.is_correct else 0
#     else:
#         instance.is_correct = None
#         instance.points_earned = 0
#
#     # Avoid infinite recursion by using update_fields
#     instance.save(update_fields=["is_correct", "points_earned"])

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Game, Pick

# Update all picks when a game's winner or points changes
@receiver(post_save, sender=Game)
def update_picks_on_game_change(sender, instance, **kwargs):
    picks = Pick.objects.filter(game=instance)
    for pick in picks:
        if instance.winner:
            pick.is_correct = pick.picked_team == instance.winner
            pick.points_earned = instance.points if pick.is_correct else 0
        else:
            pick.is_correct = None
            pick.points_earned = 0
        pick.save(update_fields=["is_correct", "points_earned"])


# Update a pick immediately after creation or change
@receiver(post_save, sender=Pick)
def update_pick_on_save(sender, instance, **kwargs):
    game = instance.game
    if game.winner:
        instance.is_correct = instance.picked_team == game.winner
        instance.points_earned = game.points if instance.is_correct else 0
    else:
        instance.is_correct = None
        instance.points_earned = 0
    instance.save(update_fields=["is_correct", "points_earned"])
