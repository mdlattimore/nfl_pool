# pool/views.py
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Game, Pick
from .forms import PickFormSet
from django.contrib import messages
from django.db.models import Min, Max, Sum
from .utils import get_week_info

class PickView(LoginRequiredMixin, View):
    template_name = 'pool/make_picks.html'

    def get_games(self, week):
        return Game.objects.filter(week=week).order_by('game_time')

    # def get_initial_data(self, games, user):
    #     """Pre-fill picks if the user has already made them."""
    #     initial = []
    #     for game in games:
    #         try:
    #             pick = Pick.objects.get(user=user, game=game)
    #             initial.append({'picked_team': pick.picked_team.id})
    #         except Pick.DoesNotExist:
    #             initial.append({})
    #     return initial

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
        formset = PickFormSet(games=games, initial=self.get_initial_data(games, request.user))
        return render(request, self.template_name, {'formset': formset, 'week': week, 'games': games})

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

            return render(request, self.template_name, {'formset': formset, 'week': week, 'games': games})


# class DashboardView(LoginRequiredMixin, TemplateView):
#     template_name = 'pool/dashboard.html'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#
#         week_info = get_week_info()
#
#         # Force open/closed state for testing
#         week_info['is_pick_open'] = True
#         week_info['is_pick_closed'] = False
#
#         context.update(week_info)
#
#         # This week's games (visible all week until next Tuesday 2 AM)
#         context['current_week_games'] = Game.objects.filter(week=week_info['week'])
#
#         # Past picks (all games before start of current week)
#         past_picks = (
#             Pick.objects
#             .filter(
#                 user=self.request.user,
#                 game__game_time__lt=week_info['week_start']
#             )
#             .select_related('game', 'picked_team', 'game__home_team', 'game__away_team', 'game__winner')
#             .order_by('game__week', 'game__game_time')
#         )
#         context['past_picks'] = past_picks
#         context['total_points'] = past_picks.aggregate(total=Sum('points_earned'))['total'] or 0
#
#         return context
#
#     def get_games(self, week):
#         return Game.objects.filter(week=week).order_by('game_time')
#
#     def get_initial_picks(self, games, user):
#         """Bulk-fetch initial picks to avoid N+1 queries."""
#         picks = Pick.objects.filter(user=user, game__in=games).select_related('picked_team')
#         picks_by_game = {p.game_id: p for p in picks}
#         return [
#             {'picked_team': picks_by_game[game.id].picked_team.id} if game.id in picks_by_game else {}
#             for game in games
#         ]
#
#     def get(self, request, *args, **kwargs):
#         week_info = get_week_info()
#         games = self.get_games(week_info['week'])
#         formset = PickFormSet(
#             games=games,
#             initial=self.get_initial_picks(games, request.user)
#         )
#
#         context = self.get_context_data(
#             formset=formset,
#             games=games,
#         )
#         return self.render_to_response(context)
#
#     def post(self, request, *args, **kwargs):
#         week_info = get_week_info()
#         games = self.get_games(week_info['week'])
#         formset = PickFormSet(request.POST, games=games)
#
#         if formset.is_valid():
#             for form, game in zip(formset.forms, games):
#                 picked_team = form.cleaned_data.get('picked_team')
#                 if picked_team and timezone.now() < game.game_time:
#                     Pick.objects.update_or_create(
#                         user=request.user,
#                         game=game,
#                         defaults={'picked_team': picked_team}
#                     )
#             messages.success(request, 'Your picks have been saved.')
#             return redirect('dashboard')
#         else:
#             messages.error(request, "You must make a pick for every game.")
#
#         context = self.get_context_data(
#             formset=formset,
#             games=games,
#         )
#         return self.render_to_response(context)

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.utils import timezone
from pool.models import Game, Pick
from pool.forms import PickFormSet
from pool.utils import get_week_info
from django.contrib.auth import get_user_model

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
            Pick.objects.filter(user=self.request.user, game__game_time__lt=timezone.now())
            .select_related('game', 'picked_team', 'game__home_team',
                            'game__away_team', 'game__winner')
            .order_by('game__week', 'game__game_time')
        )
        context['past_picks'] = past_picks
        context['total_points'] = past_picks.aggregate(Sum('points_earned'))['points_earned__sum'] or 0

        # --- Weekly Picks (All Users) ---
        week_info = get_week_info()
        week = int(kwargs.get('week', week_info['week'] if week_info else 1))
        context['week_game_summary'] = self.get_week_game_picks_summary(week)

        # --- Optional stubs ---
        context['standings'] = self.get_standings()

        return context

    def get_weekly_picks(self, week):
        """
        Returns all picks for the given week with user/game info.
        """
        return (
            Pick.objects.filter(game__week=week)
            .select_related('user', 'picked_team', 'game', 'game__home_team', 'game__away_team', 'game__winner')
            .order_by('user__username', 'game__game_time')
        )

    def get_standings(self):
        """Stub: replace with your pool standings calculation."""
        return []

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
        picks = Pick.objects.filter(user=user, game__in=games).select_related('picked_team')
        picks_by_game = {p.game_id: p for p in picks}
        return [
            {'picked_team': picks_by_game[game.id].picked_team.id} if game.id in picks_by_game else {}
            for game in games
        ]

    def get_week_game_picks_summary(self, week):
        users = User.objects.all()
        games = Game.objects.filter(week=week).select_related(
            'home_team', 'away_team', 'winner'
        ).order_by('game_time')

        summary = []

        for user in users:
            picks = Pick.objects.filter(user=user,
                                        game__in=games).select_related(
                'picked_team')
            picks_by_game = {pick.game_id: pick for pick in picks}

            row = {
                'user': user,
                'picks': [picks_by_game.get(game.id) for game in games]
            }
            summary.append(row)

        return {'games': games, 'summary': summary}
