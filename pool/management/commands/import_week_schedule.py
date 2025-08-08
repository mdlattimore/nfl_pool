# pool/management/commands/import_week_schedule.py

import json
from django.core.management.base import BaseCommand, CommandError
from django.utils.dateparse import parse_datetime
from pool.models import Team, Game


class Command(BaseCommand):
    help = "Import a week's NFL schedule from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument('week', type=int, help='Week number (e.g., 1)')
        parser.add_argument('file_path', type=str, help='Path to the JSON schedule file for the week')

    def handle(self, *args, **options):
        week = options['week']
        file_path = options['file_path']

        try:
            with open(file_path, 'r') as f:
                games = json.load(f)
        except FileNotFoundError:
            raise CommandError(f"File not found: {file_path}")
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        created = 0
        for game in games:
            try:
                home_name = game['home']['name']
                away_name = game['away']['name']
                game_time_str = game['scheduled']

                home_team = Team.objects.get(name=home_name)
                away_team = Team.objects.get(name=away_name)
                game_time = parse_datetime(game_time_str)

                if not game_time:
                    raise ValueError(f"Invalid datetime: {game_time_str}")

                Game.objects.create(
                    week=week,
                    home_team=home_team,
                    away_team=away_team,
                    game_time=game_time
                )
                created += 1
            except Team.DoesNotExist as e:
                self.stderr.write(self.style.ERROR(f"Missing team: {e}"))
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error importing game: {e}"))

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {created} games for week {week}"))
