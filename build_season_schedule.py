import json
from pprint import pprint



with open("schedules/nfl_2025_schedule_tight.json", "r") as file:
    data = json.load(file)


game_data = []
# set data index to week# - 1
for idx, week in enumerate(data, start=1):
    for game in week['games']:
        game['week'] = idx
        game_data.append(game)

with open('schedules/nfl_2025_schedule_processed.json', 'w') as file:
    json.dump(game_data, file)


