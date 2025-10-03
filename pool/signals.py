from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from .models import Game, Pick, Team


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


@receiver(pre_save, sender=Game)
def track_old_result(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Game.objects.get(pk=instance.pk)
            instance._old_winner = old.winner
            instance._old_tie = old.is_tie
        except Game.DoesNotExist:
            instance._old_winner = None
            instance._old_tie = False
    else:
        instance._old_winner = None
        instance._old_tie = False



@receiver(post_save, sender=Game)
def update_team_records(sender, instance, created, **kwargs):
    old_winner = getattr(instance, "_old_winner", None)
    old_tie = getattr(instance, "_old_tie", False)

    new_winner = instance.winner
    new_tie = instance.is_tie

    # No change --> no update
    if old_winner == new_winner and old_tie and new_tie:
        return

    home, away = instance.home_team, instance.away_team

    # --- Undo old result ---
    if old_tie:
        home.ties -= 1
        away.ties -= 1
        home.save(update_fields=["ties"])
        away.save(update_fields=["ties"])
    elif old_winner:
        old_loser = away if old_winner == home else home
        old_winner.wins -= 1
        old_loser.losses -= 1
        old_winner.save(update_fields=["wins"])
        old_loser.save(update_fields=["losses"])

    # --- Apply new result ---
    if new_tie:
        home.ties += 1
        away.ties += 1
        home.save(update_fields=["ties"])
        away.save(update_fields=["ties"])
    elif new_winner:
        new_loser = away if new_winner == home else home
        new_winner.wins += 1
        new_loser.losses += 1
        new_winner.save(update_fields=["wins"])
        new_loser.save(update_fields=["losses"])