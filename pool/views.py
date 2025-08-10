# pool/views.py
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Game, Pick
from .forms import PickFormSet

class PickView(LoginRequiredMixin, View):
    template_name = 'pool/make_picks.html'

    def get_games(self, week):
        return Game.objects.filter(week=week).order_by('game_time')

    def get_initial_data(self, games, user):
        """Pre-fill picks if the user has already made them."""
        initial = []
        for game in games:
            try:
                pick = Pick.objects.get(user=user, game=game)
                initial.append({'picked_team': pick.picked_team.id})
            except Pick.DoesNotExist:
                initial.append({})
        return initial

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
            return redirect('make_picks', week=week)

        return render(request, self.template_name, {'formset': formset, 'week': week, 'games': games})
