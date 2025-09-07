from django.core.management.base import BaseCommand
from django.db.models import Count

from pool.models import *

User = get_user_model()
from openai import OpenAI
import os

key = os.getenv('OPENAI_API_KEY')


def get_all_weeks_summary():
    users = User.objects.all()

    # Grab all distinct weeks, descending
    weeks = Game.objects.values_list("week", flat=True).distinct().order_by(
        "-week")

    all_summaries = []

    for week in weeks:
        games = Game.objects.filter(week=week).select_related(
            "home_team", "away_team", "winner"
        ).order_by("game_time")

        if not Pick.objects.filter(game__in=games).exists():
            continue

        week_summary = []

        # --- Precompute uniqueness ---
        unique_map = (
            Pick.objects.filter(game__in=games)
            .values("game_id", "picked_team_id")
            .annotate(count=Count("id"))
            .filter(count=1)
        )
        unique_set = {(u["game_id"], u["picked_team_id"]) for u in
            unique_map}

        for user in users:
            picks = Pick.objects.filter(user=user,
                                        game__in=games).select_related(
                "picked_team", "game", "game__winner"
            )
            picks_by_game = {pick.game_id: pick for pick in picks}

            # --- Recompute points per pick ---
            earned_points = 0
            wins = 0

            for pick in picks:
                # Base points
                base = pick.game.points if pick.picked_team_id == pick.game.winner_id else 0
                if base > 0:
                    wins += 1

                # Unique bonus (only if pick is correct and unique)
                unique_bonus = 2 if (pick.game_id,
                    pick.picked_team_id) in unique_set and base > 0 else 0

                # Update Pick.bonus_points if it differs
                if pick.bonus_points != unique_bonus:
                    pick.bonus_points = unique_bonus
                    pick.save(update_fields=["bonus_points"])

                earned_points += base + unique_bonus

            # Perfect week bonus
            perfect_week_bonus = 3 if wins and wins == len(games) else 0
            earned_points += perfect_week_bonus

            week_summary.append({
                "user": user.fname,
                "picks": [picks_by_game.get(game.id) for game in games],
                "points_earned": earned_points,
                "week": week,
                "perfect_week": bool(perfect_week_bonus),
            })

        # Sort & rank
        week_summary.sort(key=lambda r: r["points_earned"], reverse=True)

        current_rank = 0
        last_points = None
        for idx, row in enumerate(week_summary, start=1):
            if row["points_earned"] != last_points:
                current_rank = idx
                last_points = row["points_earned"]
            row["rank"] = current_rank

        all_summaries.append({
            "week": week,
            "games": games,
            "summary": week_summary,
        })

    return all_summaries


def serialize_weeks_summary(raw_summary):
    serialized = []

    for week_entry in raw_summary:
        week = week_entry["week"]

        # Build a lookup of game_id → winner for this week
        game_winners = {
            game.id: str(game.winner) if game.winner else None
            for game in week_entry["games"]
        }

        # Serialize games
        games = [
            {
                "id": game.id,
                "week": game.week,
                "home_team": str(game.home_team),
                "away_team": str(game.away_team),
                "winner": str(game.winner) if game.winner else None,
            }
            for game in week_entry["games"]
        ]

        # Serialize user summaries
        summaries = []
        for user_summary in week_entry["summary"]:
            user = user_summary["user"]

            picks = []
            for pick in user_summary["picks"]:
                if pick is None:
                    continue  # skip missing picks
                winner = game_winners.get(pick.game.id)
                is_correct = (winner is not None and str(pick.picked_team) ==
                              winner)
                picks.append({
                    "id": pick.id,
                    "game": str(pick.game),
                    "team": str(pick.picked_team),
                    "winner": winner,
                    "is_correct": is_correct,
                })

            summaries.append({
                "user": user,
                "picks": picks,
                "points_earned": user_summary["points_earned"],
                "week": user_summary["week"],
                "perfect_week": user_summary["perfect_week"],
                "rank": user_summary["rank"],
            })

        serialized.append({
            "week": week,
            "games": games,
            "summary": summaries,
        })

    return serialized


def build_full_results_package(weeks_summary):
    """
    Build the full results package, including per-week summaries
    and cumulative standings.

    Accepts either:
    - raw QuerySet-style objects from get_all_weeks_game_picks_summary
    - already serialized data from serialize_weeks_summary
    """
    # Detect if already serialized (list of dicts with "games" key)
    already_serialized = (
            isinstance(weeks_summary, list) and
            all(isinstance(week, dict) and "games" in week for week in
                    weeks_summary)
    )

    if not already_serialized:
        # If raw objects, serialize first
        weeks_summary = serialize_weeks_summary(weeks_summary)

    # Build cumulative standings
    cumulative = {}
    for week in weeks_summary:
        for user_summary in week['summary']:
            user_email = user_summary['user']
            points = user_summary['points_earned']
            cumulative.setdefault(user_email, 0)
            cumulative[user_email] += points

    # Build final package
    package = {
        "weeks": weeks_summary,
        "cumulative_standings": [
            {"user": user, "points": pts} for user, pts in
            sorted(cumulative.items(), key=lambda x: -x[1])
        ]
    }

    return package


def trim_full_results_for_llm(full_results):
    """
    Aggressively trims the full results package for LLM input.
    Keeps only essential info for generating a summary email:
    - Week info (week number)
    - Games: home team, away team, winner
    - Summary: user, points earned, rank, perfect_week, picks (game string, team picked, winner, is_correct)
    - Cumulative standings: user, points
    """
    trimmed = {
        "weeks": [],
        "cumulative_standings": full_results.get("cumulative_standings", []),
    }

    for week in full_results.get("weeks", []):
        trimmed_week = {
            "week": week.get("week"),
            "games": [
                {
                    "home_team": game["home_team"],
                    "away_team": game["away_team"],
                    "winner": game["winner"],
                }
                for game in week.get("games", [])
            ],
            "summary": [
                {
                    "user": s["user"],
                    "points_earned": s["points_earned"],
                    "rank": s["rank"],
                    "perfect_week": s.get("perfect_week", False),
                    "picks": [
                        {
                            "game": pick["game"],
                            "team": pick["team"],
                            "winner": pick["winner"],
                            "is_correct": pick["is_correct"],
                        }
                        for pick in s.get("picks", [])
                    ],
                }
                for s in week.get("summary", [])
            ],
        }
        trimmed["weeks"].append(trimmed_week)

    return trimmed


class Command(BaseCommand):
    help = "Quickly generate a past week's games, picks, and winners for testing."

    def handle(self, *args, **options):
        client = OpenAI(api_key=key)
        raw_summaries = get_all_weeks_summary()
        serialized = serialize_weeks_summary(raw_summaries)
        full_results_package = build_full_results_package(serialized)
        trimmed_full_results_package = trim_full_results_for_llm(
            full_results_package)

        # avoid list index error if we are less than 3 weeks into season
        if len(trimmed_full_results_package["weeks"]) >= 3:
            last_three_weeks = {
                'weeks': trimmed_full_results_package["weeks"][0:2],
                'cumulative_standings': trimmed_full_results_package[
                    'cumulative_standings'],
            }
        else:
            last_three_weeks = {
                'weeks': trimmed_full_results_package["weeks"],
                'cumulative_standings': trimmed_full_results_package[
                    'cumulative_standings'],
            }
        prompt_data = trim_full_results_for_llm(last_three_weeks)
        note_obj = WeeklyNote.objects.filter(week=prompt_data["weeks"][0][
            "week"])
        notes = note_obj.values_list('notes', flat=True)

        prompt = f"""
        You are the commissioner of a family/friends NFL pool. Each week, players pick winners of every game and earn points. Results are recorded in JSON ("Results"). 

        Write an email summarizing the most recent week using that week's results, 
        past results, and overall standings. Use a conversational tone. Don't use
        the phrase 'NFL Pool' but rather use natural language (like 
        ‘this week’s games,’ or ‘the pool’) instead of repeating it. Highlight good 
        performances and trends. Only use information from "Results" or "Notes"; 
        do not invent anything (no underdogs, close games, or speculation). 
        Focus on the top players; use first names only. Sign as 'Mark'. Format 
        in Markdown, applying styles as appropriate for emphasis or note.

        Tone: Light, witty, humorous
        Length: Maximum three short paragraphs

        Results:
        {prompt_data}

        Notes:
        {notes}
        """

        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=.5
        )

        email = Email(
            data=prompt_data,
            text=response.output_text
        )
        email.save()
        self.stdout.write(self.style.SUCCESS(
            response.output_text
        ))
        print(response.output_text)
