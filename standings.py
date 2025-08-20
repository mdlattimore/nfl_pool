from django.contrib.auth import get_user_model
from pool.models import Game, Pick


def get_overall_standings():
    User = get_user_model()
    users = User.objects.all()
    weeks = Game.objects.values_list('week', flat=True).distinct().order_by('week')
    standings = []

    for user in users:
        weekly_points = []
        total_points = 0
        for week in weeks:
            picks = Pick.objects.filter(user=user, game__week=week)
            week_points = sum(p.points_earned for p in picks)
            weekly_points.append(week_points)
            total_points += week_points
        standings.append({
            'user': user,
            'weekly_points': weekly_points,
            'total_points': total_points
        })

    # Sort descending by total points
    standings.sort(key=lambda r: r['total_points'], reverse=True)

    # Assign rank
    for i, row in enumerate(standings, start=1):
        row['rank'] = i

    return {
        'weeks': list(weeks),
        'standings': standings
    }
