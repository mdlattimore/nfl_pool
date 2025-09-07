class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'pool/dashboard.html'

    # ============================================================
    # Request handling
    # ============================================================

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
            messages.success(request, 'Your picks have been saved.')
        else:
            messages.error(request, "You must make a pick for every game.")
        # Re-render dashboard with messages
        context = self.get_context_data(
            week=week,
            formset=formset,
            games=games
        )
        return self.render_to_response(context)

    # ============================================================
    # Context assembly
    # ============================================================

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # --- Current week info ---
        week_info = get_week_info()
        # Force open/closed state for testing
        # Comment to enforce pick window
        # Uncomment to allow picks during window
        settings = get_pool_settings()
        if not settings.enforce_pick_window:
            week_info['is_pick_open'] = True
            week_info['is_pick_closed'] = False
            print("Pick Window NOT enforced")
        else:
            print("Pick Window enforced")

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
        context['all_weeks_game_summary'] = self.get_all_weeks_game_picks_summary()

        # --- Optional stubs ---
        overall_standings = self.get_overall_standings()
        context['standings'] = overall_standings['standings']
        context['weeks'] = overall_standings['weeks']

        return context

    # ============================================================
    # Standings and summaries
    # ============================================================

    def get_overall_standings(self):
        UNIQUE_BONUS = 2  # keep in sync with your rules
        PERFECT_WEEK_BONUS = 3

        User = get_user_model()
        users = list(User.objects.all())
        user_ids = [u.id for u in users]

        weeks = list(
            Game.objects.values_list('week', flat=True).distinct().order_by(
                'week')
        )

        # Per-user weekly totals will be accumulated here in week order
        per_user_weekly = {u.id: [] for u in users}

        for week in weeks:
            games = list(
                Game.objects.filter(week=week).select_related("winner"))
            if not games:
                # still push 0 for every user to keep column counts aligned
                for uid in user_ids:
                    per_user_weekly[uid].append(0)
                continue

            game_ids = [g.id for g in games]
            games_count = len(games)

            # All picks for this week in one query
            picks_qs = (
                Pick.objects
                .filter(game_id__in=game_ids)
                .select_related("user", "game", "game__winner")
            )
            picks = list(picks_qs)

            # Build a set of (game_id, picked_team_id) that are unique across all users
            uniques = (
                picks_qs.values("game_id", "picked_team_id")
                .annotate(cnt=Count("id"))
                .filter(cnt=1)
            )
            unique_set = {(u["game_id"], u["picked_team_id"]) for u in uniques}

            # Compute weekly totals per user
            week_totals = {uid: 0 for uid in user_ids}
            wins_count = {uid: 0 for uid in user_ids}

            for p in picks:
                correct = (
                        p.picked_team_id == p.game.winner_id and p.game.winner_id is not None)
                base = p.game.points if correct else 0
                unique_bonus = UNIQUE_BONUS if correct and (p.game_id,
                    p.picked_team_id) in unique_set else 0
                week_totals[p.user_id] += base + unique_bonus
                if correct:
                    wins_count[p.user_id] += 1

            # Perfect week bonus
            all_winners_set = all(g.winner_id is not None for g in games)
            if all_winners_set:
                for uid in user_ids:
                    if wins_count[uid] == games_count and games_count > 0:
                        week_totals[uid] += PERFECT_WEEK_BONUS

            # Append this week's total to each user's ledger
            for uid in user_ids:
                per_user_weekly[uid].append(week_totals[uid])

        # Build standings rows
        standings = []
        for u in users:
            weekly_points = per_user_weekly[u.id]
            total_points = sum(weekly_points)
            standings.append({
                "user": u,
                "weekly_points": weekly_points,
                "total_points": total_points,
            })

        # Sort descending by total points
        standings.sort(key=lambda r: r["total_points"], reverse=True)

        # 1224-style ranking
        last_points = None
        last_rank = 0
        for i, row in enumerate(standings, start=1):
            if row["total_points"] != last_points:
                row["rank"] = i
                last_rank = i
                last_points = row["total_points"]
            else:
                row["rank"] = last_rank

        return {
            "weeks": weeks,
            "standings": standings,
        }

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
                    base = pick.game.points if pick.picked_team_id == pick.game.winner_id else 0
                    if base > 0:
                        wins += 1

                    unique_bonus = 2 if (pick.game_id,
                        pick.picked_team_id) in unique_set and base > 0 else 0

                    if pick.bonus_points != unique_bonus:
                        pick.bonus_points = unique_bonus
                        pick.save(update_fields=["bonus_points"])

                    earned_points += base + unique_bonus

                perfect_week_bonus = 3 if wins and wins == len(games) else 0
                earned_points += perfect_week_bonus

                week_summary.append({
                    "user": user,
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

        week_info = get_week_info()
        print((week_info['week'] == all_summaries[0]['week']) and week_info[
            'is_pick_open'])

        if (
                all_summaries
                and week_info['is_pick_open']
                and week_info['week'] == all_summaries[0]['week']
        ):
            return all_summaries[1:]

        return all_summaries

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

    # ============================================================
    # Form helpers
    # ============================================================

    def get_initial_picks(self, games, user):
        picks = Pick.objects.filter(user=user, game__in=games).select_related(
            'picked_team')
        picks_by_game = {p.game_id: p for p in picks}
        return [
            {'picked_team': picks_by_game[
                game.id].picked_team.id} if game.id in picks_by_game else {}
            for game in games
        ]
