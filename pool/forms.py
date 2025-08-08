from django import forms
from .models import Pick, Game, Team
from django.forms import BaseFormSet, formset_factory

class PickForm(forms.ModelForm):
    picked_team = forms.ModelChoiceField(
        queryset=Team.objects.none(),  # Will be overridden in __init__
        widget=forms.RadioSelect,
        empty_label=None,
        required=True
    )

    def __init__(self, *args, **kwargs):
        game = kwargs.pop('game', None)
        super().__init__(*args, **kwargs)

        if game:
            self.fields['picked_team'].queryset = Team.objects.filter(
                id__in=[game.home_team.id, game.away_team.id]
            )
            # Optional: customize the label (e.g., show just the team alias or full name)
            self.fields['picked_team'].label_from_instance = lambda obj: obj.name

    class Meta:
        model = Pick
        fields = ['picked_team']


class BasePickFormSet(BaseFormSet):
    def __init__(self, *args, games=None, **kwargs):
        self.games = games or []
        super().__init__(*args, **kwargs)

        for i, form in enumerate(self.forms):
            if i < len(self.games):
                game = self.games[i]
                form.game = game  # Assign it directly for clarity

                # Manually set the limited queryset
                form.fields['picked_team'].queryset = Team.objects.filter(
                    id__in=[game.home_team_id, game.away_team_id]
                )
                form.fields['picked_team'].label_from_instance = lambda obj: obj.name

PickFormSet = formset_factory(PickForm, formset=BasePickFormSet, extra=0)
