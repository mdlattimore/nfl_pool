import os
import django
from itertools import groupby

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_project.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
from pool.models import Team


teams = list(Team.objects.all())

# Sort by conference/division, then by winning percentage, then by name
teams.sort(key=lambda t: (t.conference, t.division, -t.winning_percentage, t.name))

grouped = {
    division: list(group)
    for division, group in groupby(teams, key=lambda t: t.division_full)
}

for div, group in grouped.items():
    print(div)
    for team in group:
        record = f"{team.wins}-{team.losses}-{team.ties}"
        print(team.name, record)


# def get_records():
#     records = []
#     for team in Team.objects.all():
#         team_record = {}
#         name = team.name
#         wins = team.wins
#         losses = team.losses
#         ties = team.ties
#         conference = team.conference
#         division = team.division
#         record = f"{wins}-{losses}-{ties}"
#         winning_percentage = calculate_winning_percentage(record)
#         team_record['team'] = team
#         team_record['record'] = record
#         team_record['conference'] = conference
#         team_record['division'] = division
#         team_record['winning_percentage'] = winning_percentage
#         records.append(team_record)
#     return records
#
#
# def rank_teams():
#     records = get_records()
#     results = []
#     for entry in records:
#         team_record = {}
#         team_record['team'] = entry['team']
#         team_record['record'] = entry['record']
#         team_record['conference'] = entry['conference']
#         team_record['division'] = entry['division']
#         team_record['winning_percentage'] = entry['winning_percentage']
#         results.append(team_record)
#     results_sorted = sorted(results, key=lambda r: r['winning_percentage'], reverse=True)
#     return results_sorted
#
#
#
#
# ranked_records = rank_teams()
# for team in ranked_records:
#     print(f"{team['team']} ({team['conference']} "
#           f"{team['division']}): {team['record']}")