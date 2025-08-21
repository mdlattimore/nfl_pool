# pool/views.py
# Lines 84-88 control enforcement of pick window
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView

from pool.forms import PickFormSet
from pool.models import Game, Pick
from pool.utils import get_week_info


class PickView(LoginRequiredMixin, View):
    template_name = 'pool/make_picks.html'

    def get_games(self, week):
        return Game.objects.filter(week=week).order_by('game_time')

    def get_initial_data(self, games, user):
        """Pre-fill picks if the user has already made them — single query version."""
        # Fetch all picks for these games in one query
        picks = Pick.objects.filter(user=user, game__in=games).select_related(
            'picked_team')

        # Map game_id -> picked_team.id for quick lookup
        picks_by_game_id = {pick.game_id: pick.picked_team_id for pick in picks}

        # Build initial list in the same order as games
        return [
            {'picked_team': picks_by_game_id.get(game.id)} or {}
            for game in games
        ]

    def get(self, request, week):
        games = self.get_games(week)
        formset = PickFormSet(games=games, initial=self.get_initial_data(games,
                                                                         request.user))
        return render(request, self.template_name,
                      {'formset': formset, 'week': week, 'games': games})

    def post(self, request, week):
        games = self.get_games(week)
        formset = PickFormSet(request.POST, games=games)

        if formset.is_valid():
            for form, game in zip(formset.forms, games):
                picked_team = form.cleaned_data.get('picked_team')
                if picked_team:
                    # Prevent picking after start time
                    if timezone.now() < game.game_time:
                        Pick.objects.update_or_create(
                            user=request.user,
                            game=game,
                            defaults={'picked_team': picked_team}
                        )
            messages.success(request, 'Your picks have been saved.')
            return redirect('make_picks', week=week)
        else:
            messages.error(request, "You must make a pick for every game.")

            return render(request, self.template_name,
                          {'formset': formset, 'week': week, 'games': games})


User = get_user_model()


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pool/dashboard.html'

    # ------------------------
    # Context helpers
    # ------------------------
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Current week info ---
        week_info = get_week_info()

        # Force open/closed state for testing
        # Comment to enforce pick window
        # Uncomment to allow picks during window
        # week_info['is_pick_open'] = True
        # week_info['is_pick_closed'] = False

        if week_info:
            context['current_week'] = week_info['week']
            context['pick_open'] = week_info['pick_open']
            context['pick_close'] = week_info['pick_close']
            context['is_pick_open'] = week_info['is_pick_open']
            context['is_pick_closed'] = week_info['is_pick_closed']
        else:
            context['current_week'] = 1
            context['pick_open'] = None
            context['pick_close'] = None
            context['is_pick_open'] = True
            context['is_pick_closed'] = False

        # --- This Week's Games ---
        context['current_week_games'] = Game.objects.filter(
            week=context['current_week']
        ).order_by('game_time')

        # --- Past Picks ---
        past_picks = (
            Pick.objects.filter(user=self.request.user,
                                game__game_time__lt=timezone.now())
            .select_related('game', 'picked_team', 'game__home_team',
                            'game__away_team', 'game__winner')
            .order_by('game__week', 'game__game_time')
        )
        context['past_picks'] = past_picks
        context['total_points'] = sum(p.total_points for p in past_picks)


        # --- Weekly Picks (All Users) ---
        week_info = get_week_info()

        # week = int(kwargs.get('week', week_info['week'] if week_info else 1))
        # context['week_game_summary'] = self.get_week_game_picks_summary(week)

        context[
            'all_weeks_game_summary'] = self.get_all_weeks_game_picks_summary()

        # --- Optional stubs ---
        overall_standings = self.get_overall_standings()
        context['standings'] = overall_standings['standings']
        context['weeks'] = overall_standings['weeks']

        return context

    def get_weekly_picks(self, week):
        """
        Returns all picks for the given week with user/game info.
        """
        return (
            Pick.objects.filter(game__week=week)
            .select_related('user', 'picked_team', 'game', 'game__home_team',
                            'game__away_team', 'game__winner')
            .order_by('user__username', 'game__game_time')
        )

    # def get_overall_standings(self):
    #     User = get_user_model()
    #     users = User.objects.all()
    #     weeks = Game.objects.values_list('week', flat=True).distinct().order_by(
    #         'week')
    #     standings = []
    #
    #     for user in users:
    #         weekly_points = []
    #         total_points = 0
    #         for week in weeks:
    #             picks = Pick.objects.filter(user=user, game__week=week)
    #             week_points = sum(p.points_earned for p in picks)
    #             weekly_points.append(week_points)
    #             total_points += week_points
    #         standings.append({
    #             'user': user,
    #             'weekly_points': weekly_points,
    #             'total_points': total_points
    #         })
    #
    #     # Sort descending by total points
    #     standings.sort(key=lambda r: r['total_points'], reverse=True)
    #
    #     # Assign rank
    #     for i, row in enumerate(standings, start=1):
    #         row['rank'] = i
    #
    #     return {
    #         'weeks': list(weeks),
    #         'standings': standings
    #     }
    def get_overall_standings(self):
        User = get_user_model()
        users = User.objects.all()
        weeks = Game.objects.values_list('week', flat=True).distinct().order_by(
            'week')
        standings = []

        for user in users:
            weekly_points = []
            total_points = 0
            for week in weeks:
                picks = Pick.objects.filter(user=user, game__week=week)
                week_points = sum(p.total_points for p in picks)
                weekly_points.append(week_points)
                total_points += week_points
            standings.append({
                'user': user,
                'weekly_points': weekly_points,
                'total_points': total_points
            })

        # Sort descending by total points
        standings.sort(key=lambda r: r['total_points'], reverse=True)

        # Assign competition rank (1224 style)
        last_points = None
        last_rank = 0
        for i, row in enumerate(standings, start=1):
            if row['total_points'] != last_points:
                row['rank'] = i
                last_rank = i
                last_points = row['total_points']
            else:
                row['rank'] = last_rank

        return {
            'weeks': list(weeks),
            'standings': standings
        }

    # ------------------------
    # GET / POST handling for pick form
    # ------------------------
    def get(self, request, *args, **kwargs):
        week_info = get_week_info()
        week = int(kwargs.get('week', week_info['week'] if week_info else 1))
        games = Game.objects.filter(week=week).order_by('game_time')
        formset = PickFormSet(
            games=games,
            initial=self.get_initial_picks(games, request.user)
        )

        context = self.get_context_data(
            week=week,
            formset=formset,
            games=games
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        week = int(kwargs.get('week', get_week_info()['week']))
        games = Game.objects.filter(week=week).order_by('game_time')
        formset = PickFormSet(request.POST, games=games)

        if formset.is_valid():
            for form, game in zip(formset.forms, games):
                picked_team = form.cleaned_data.get('picked_team')
                if picked_team and timezone.now() < game.game_time:
                    Pick.objects.update_or_create(
                        user=request.user,
                        game=game,
                        defaults={'picked_team': picked_team}
                    )
        # Re-render dashboard with messages
        context = self.get_context_data(
            week=week,
            formset=formset,
            games=games
        )
        return self.render_to_response(context)

    # ------------------------
    # Helpers for pick form initialization
    # ------------------------
    def get_initial_picks(self, games, user):
        picks = Pick.objects.filter(user=user, game__in=games).select_related(
            'picked_team')
        picks_by_game = {p.game_id: p for p in picks}
        return [
            {'picked_team': picks_by_game[
                game.id].picked_team.id} if game.id in picks_by_game else {}
            for game in games
        ]

    def get_all_weeks_game_picks_summary(self):
        users = User.objects.all()

        # Grab all distinct weeks, descending
        weeks = Game.objects.values_list("week", flat=True).distinct().order_by(
            "-week")

        all_summaries = []

        for week in weeks:
            games = Game.objects.filter(week=week).select_related(
                "home_team", "away_team", "winner"
            ).order_by("game_time")

            # Only include this week if there is at least one pick
            if not Pick.objects.filter(game__in=games).exists():
                continue

            week_summary = []

            for user in users:
                picks = Pick.objects.filter(
                    user=user, game__in=games
                ).select_related("picked_team")

                picks_by_game = {pick.game_id: pick for pick in picks}

                row = {
                    "user": user,
                    "picks": [picks_by_game.get(game.id) for game in games],
                    "points_earned": sum([p.total_points for p in picks]),
                    "week": week,
                }
                week_summary.append(row)

            # Sort descending by points
            week_summary.sort(key=lambda r: r["points_earned"], reverse=True)

            # Assign ranks (ties handled properly: equal points → same rank)
            current_rank = 0
            last_points = None
            for idx, row in enumerate(week_summary, start=1):
                if row["points_earned"] != last_points:
                    current_rank = idx
                    last_points = row["points_earned"]
                row["rank"] = current_rank

            all_summaries.append(
                {
                    "week": week,
                    "games": games,
                    "summary": week_summary,
                }
            )

        return all_summaries
