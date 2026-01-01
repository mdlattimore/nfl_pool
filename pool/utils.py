from datetime import datetime, time, timedelta, timezone as dt_timezone
import pytz
from django.utils import timezone
from django.db.models import Min, Max
from .models import Game, PoolSettings

def get_week_info():
    now = timezone.now()

    eastern = pytz.timezone('US/Eastern')
    now_eastern = now.astimezone(eastern)

    # Find most recent Tuesday 2 AM Eastern
    days_since_tuesday = (now_eastern.weekday() - 1) % 7  # Tuesday = 1
    last_tuesday_date = (now_eastern - timedelta(days=days_since_tuesday)).date()
    week_start_naive = datetime.combine(last_tuesday_date, time(2, 0))
    week_start = eastern.localize(week_start_naive).astimezone(dt_timezone.utc)

    week_end = week_start + timedelta(days=7)

    # Pick window -- correct value: timedelta(days=2)
    pick_open = week_start
    pick_close = eastern.localize(
        # Close pick window at 8pm Eastern on Thursday -- Normal
        # datetime.combine(last_tuesday_date + timedelta(days=2), time(13, 0))

        # close pick window at 4pm on Saturday (Week 18)
        datetime.combine(last_tuesday_date + timedelta(days=4), time(16, 0))

    ).astimezone(dt_timezone.utc)

    current_game_week = (
        Game.objects
        .filter(game_time__gte=week_start, game_time__lt=week_end)
        .values_list('week', flat=True)
        .first()
    )

    if current_game_week is None:
        current_game_week = 1

    return {
        'week': current_game_week,
        'week_start': week_start,
        'week_end': week_end,
        'pick_open': pick_open,
        'pick_close': pick_close,
        'is_pick_open': pick_open <= now < pick_close,
        'is_pick_closed': now >= pick_close,
    }

def get_pool_settings():
    return PoolSettings.objects.first() or PoolSettings(enforce_pick_window=True)