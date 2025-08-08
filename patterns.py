import json

with open('nfl_2025_schedule.json', 'r') as file:
    s = json.load(file)


for game in s['weeks'][0]['games']:
    print(f"{game['away']['name']} at {game['home']['name']}")

all_games = []
for week in s['weeks']:
    for game in week['games']:
        all_games.append(f"{game['away']['name']} at {game['home']['name']}")

print(all_games)
print(len(all_games))


 for week in s['weeks']:
...     print(f"Week {week['title']}\n")
...
...     for game in week['games']:
...
...         print(f"{game['away']['alias']} at {game['home']['alias']}")
...
...     print()
...
...     print()