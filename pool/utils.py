from datetime import timedelta
from django.utils import timezone
from django.db.models import Min, Max
import pytz
from .models import Game


def get_week_info():
    """
    Returns a dictionary with:
        - week: current week number
        - pick_open: datetime pick window opens
        - pick_close: datetime pick window closes
        - is_pick_open: bool
        - is_pick_closed: bool
    If no games are found, returns None.
    """

    eastern = pytz.timezone("US/Eastern")
    now = timezone.now().astimezone(eastern)

    # Get earliest and latest games for each week
    weeks = (
        Game.objects.values('week')
        .annotate(start=Min('game_time'), end=Max('game_time'))
        .order_by('week')
    )

    for w in weeks:
        week_start = w['start'].astimezone(eastern)

        # Adjust week start to Tuesday 2:00 AM ET
        week_start = week_start - timedelta(days=week_start.weekday())  # Monday
        week_start += timedelta(days=1)  # Tuesday
        week_start = week_start.replace(hour=2, minute=0, second=0, microsecond=0)

        pick_close = week_start + timedelta(days=2, hours=17)  # Thursday 7 PM ET
        week_end = week_start + timedelta(days=6, hours=23, minutes=59)

        if week_start <= now <= week_end:
            return {
                'week': w['week'],
                'pick_open': week_start,
                'pick_close': pick_close,
                'is_pick_open': week_start <= now <= pick_close,
                'is_pick_closed': now > pick_close
            }

    return None
