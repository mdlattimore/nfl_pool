import json
from pprint import pprint



with open("nfl_2025_schedule_tight.json", "r") as file:
    data = json.load(file)


game_data = []
# set data index to week# - 1
for game in data[0]['games']:
    game_data.append(game)

with open('nfl_2025_week_1.json', 'w') as file:
    json.dump(game_data, file)


