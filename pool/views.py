# pool/views.py
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Game, Pick
from .forms import PickFormSet
from django.contrib import messages
from django.db.models import Min, Max

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


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pool/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # This week's games
        current_week = self.get_current_week()
        context['current_week'] = current_week
        context['current_week_games'] = Game.objects.filter(week=current_week)

        context['past_picks'] = (
            Pick.objects.filter(user=self.request.user,
                                game__game_time__lt=timezone.now())
        .select_related('game', 'picked_team', 'game__home_team',
                        'game__away_team', 'game__winner')
        .order_by('-game__game_time')
        )
        return context


    # --- Helpers ---
    def get_current_week(self):
        now = timezone.now()

        # Annotate each week with its earliest and latest game times
        weeks = (
            Game.objects.values('week')
            .annotate(start=Min('game_time'), end=Max('game_time'))
            .order_by('week')
        )

        for w in weeks:
            if w['start'] <= now <= w['end']:
                return w['week']

        # If no match, season hasn't started, return week 1
        return 1

    def get_games(self, week):
        return Game.objects.filter(week=week).order_by('game_time')

    def get_initial_picks(self, games, user):
        """Bulk-fetch initial picks to avoid N+1 queries."""
        picks = Pick.objects.filter(user=user, game__in=games).select_related('picked_team')
        picks_by_game = {p.game_id: p for p in picks}
        return [
            {'picked_team': picks_by_game[game.id].picked_team.id} if game.id in picks_by_game else {}
            for game in games
        ]

    def get_past_picks(self, user, week):
        return Pick.objects.filter(user=user).exclude(game__week=week).select_related('game', 'picked_team')

    def get_standings(self):
        """Stub for standings calculation."""
        return []  # Replace with actual standings query

    def get_picks_summary_by_week(self):
        """Stub for summary table."""
        return []  # Replace with aggregation query

    # --- HTTP methods ---
    def get(self, request, *args, **kwargs):
        week = int(kwargs.get('week', self.get_current_week()))
        games = self.get_games(week)
        formset = PickFormSet(
            games=games,
            initial=self.get_initial_picks(games, request.user)
        )

        context = self.get_context_data(
            week=week,
            formset=formset,
            games=games,
            past_picks=self.get_past_picks(request.user, week),
            standings=self.get_standings(),
            picks_summary=self.get_picks_summary_by_week(),
        )
        return self.render_to_response(context)

    def post(self, request, *args, **kwargs):
        week = int(kwargs.get('week', self.get_current_week()))
        games = self.get_games(week)
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
            messages.success(request, 'Your picks have been saved.')
            return redirect('dashboard')
        else:
            messages.error(request, "You must make a pick for every game.")
        # If not valid, re-render with errors and the rest of dashboard data
        context = self.get_context_data(
            week=week,
            formset=formset,
            games=games,
            past_picks=self.get_past_picks(request.user, week),
            standings=self.get_standings(),
            picks_summary=self.get_picks_summary_by_week(),
        )
        return self.render_to_response(context)