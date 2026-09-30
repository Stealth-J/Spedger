from django.core.mail import EmailMessage
from django.conf import settings
from .models import Duel, FriendRequest, Profile, Slip, SlipEvent
from datetime import datetime
from django.db.models import F, Window, Count, Sum, Case, When, Q, ExpressionWrapper, FloatField, Max, Value, CharField
from django.db.models.functions import DenseRank, Round, ExtractWeekDay, ExtractMonth, TruncDate, NullIf
import statistics
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils import timezone as dj_tz
from collections import defaultdict
from types import SimpleNamespace
import random


WEEK_DAYS_DICT = {
    '1': 'Sun',
    '2': 'Mon',
    '3': 'Tue',
    '4': 'Wed',
    '5': 'Thur',
    '6': 'Fri',
    '7': 'Sat',
}
MONTHS_DICT = {
    '1': 'Jan',
    '2': 'Feb',
    '3': 'Mar',
    '4': 'Apr',
    '5': 'May',
    '6': 'Jun',
    '7': 'Jul',
    '8': 'Aug',
    '9': 'Sep',
    '10': 'Oct',
    '11': 'Nov',
    '12': 'Dec',
}

def randomize(prob):
    return random.random() < prob


def send_mail(subject, body, email):
    email = EmailMessage(subject, body, to = [email])
    email.send()

def send_mail_with_template(subject, template_name, context, email):
    body = render_to_string(template_name, context)
    email = EmailMessage(subject, body, to = [email])
    email.content_subtype = "html"
    email.send()


def total_notifications(request):
    total_duels = Duel.objects.prefetch_related('duellists').filter(duellists__user = request.user, duel_status = 'open', duellists__recipient = 'True').count()
    total_requests = FriendRequest.objects.prefetch_related('recipient').filter(recipient = request.user, status = 'open').count()

    return total_requests, total_duels


def paginate(request, qs, page_num = 1):
    paginator = Paginator(qs, settings.PAGE_SIZE)
    current_qs = paginator.get_page(page_num)
    return current_qs


def rank_group_members(qs):
    annotated_qs = qs.annotate(
        pure_odds_temp = Sum(
            Case(When(
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True), then = F('user__slips__total_odds')
            ))
        ),
        winning_slips_temp = Count(
            Case(When(
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True), then = 1
            ))
        ),
        total_slips = Count('user__slips'),
        pure_percentage_temp = Case(
            When(total_slips = 0, then = Value(0.0)),
            default = ExpressionWrapper(
                ( F('winning_slips_temp') * 100.0) / F('total_slips'),
                output_field = FloatField()
            ),
            output_field = FloatField(),
        )
    )

    ranked_qs = annotated_qs.annotate(
        rank = Window(
            expression = DenseRank(), 
            order_by = [ F('pure_odds_temp').desc(nulls_last = True), F('pure_percentage_temp').desc(nulls_last = True) ],
        )
    )
    
    return ranked_qs


def rank_users_leaderboards(wkly_qs = None, wkly = True):
    if wkly:
        wkly_qs = wkly_qs.exclude(user__user_profile__private_acct = True)

        annotated_qs = wkly_qs.annotate(
            total_events = Count('slip__slip_events'),
            events_won = Count(
                Case(When(
                    Q(slip__slip_events__event_won = True), then = F('slip__slip_events')
                ))
            ),
            accuracy = ExpressionWrapper(
                ( F('events_won') * 100.0 ) / F('total_events'), output_field = FloatField()
            ),
            highest_selection = Max('slip__slip_events__event_odd'),
            games_won = Count(
                Case(When(
                    Q(slip__slip_events__event_won = True) & Q(slip__slip_events__event_settled = True), then = 1
                ))
            ),
            games_lost = Count(
                Case(When(
                    Q(slip__slip_events__event_won = False) & Q(slip__slip_events__event_settled = True), then = 1
                ))
            )
        )
        ranked_qs = annotated_qs.annotate(rank = Window(
            expression = DenseRank(),
            order_by = [ F('accuracy').desc(nulls_last = True), F('slip__total_odds').desc(nulls_last = True), F('highest_selection').desc(nulls_last = True) ]
        ))
    else:
        all_profiles = Profile.objects.exclude(private_acct = True)
        ranked_qs = rank_group_members(all_profiles)

    return ranked_qs


def source_insights_stats(request):
    total_slips = Slip.objects.prefetch_related("slip_events", "user")
    total_users = Profile.objects.prefetch_related('user__slips', 'user__slips__slip_events').exclude(user__slips = None)
    current_month = datetime.now().month
    cm_slips = total_slips.filter(entry_date__month = current_month)
    user_slips = request.user.slips
    user_slips_won = user_slips.filter(settled = True, slip_won = True)
    user_slips_events = SlipEvent.objects.filter(slip__user = request.user)

    highest_pure_odds = total_slips.filter(settled = True, slip_won = True).order_by('-total_odds').first()
    highest_pure_odds_cm = cm_slips.filter(settled = True, slip_won = True).order_by('-total_odds').first()   # cm means current month

    the_best = total_users.annotate(
        total_pure_odds = Sum(
            Case(When(
                Q(user__slips__settled = True) & Q(user__slips__slip_won = True), then = F('user__slips__total_odds')
            ))
        ),
    ).order_by('-total_pure_odds').exclude(total_pure_odds = 0)
    most_accurate = total_users.annotate(
        total_events = Count(
            Case(When(
                Q(user__slips__slip_events__event_settled = True), then = F('user__slips__slip_events')
            ))
        ),
        events_won = Count(
            Case(When(
                Q(user__slips__slip_events__event_won = True), then = F('user__slips__slip_events')
            ))
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('events_won') * 100.0 ) / F('total_events'), output_field = FloatField()
        ),
    ).order_by('-calc_accuracy')
    most_accurate_pure = total_users.annotate(
        total_slips = Count(
            Case(When(
                Q(user__slips__settled = True), then = F('user__slips')
            ))
        ),
        slips_won = Count(
            Case(When(
                Q(user__slips__slip_won = True) & Q(user__slips__settled = True), then = F('user__slips')
            ))
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('slips_won') * 100.0 ) / F('total_slips'), output_field = FloatField()
        ),
    ).order_by('-calc_accuracy').first()
    accuracy_qs_cm = total_users.filter(user__slips__entry_date__month = current_month).annotate(
        total_pure_odds = Sum(
            'user__slips__total_odds',
            filter = Q(
                user__slips__settled = True,
                user__slips__slip_won = True,
                user__slips__entry_date__month = current_month,
            )
        ),
        total_events = Count(
            'user__slips__slip_events',
            filter = Q(
                user__slips__entry_date__month = current_month,
                user__slips__slip_events__event_settled = True,
            )
        ),
        events_won = Count(
            'user__slips__slip_events',
            filter = Q(
                user__slips__entry_date__month = current_month,
                user__slips__slip_events__event_won = True,
            )
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ),
    )

    # Period
    days = list(user_slips.annotate(
        day = TruncDate('entry_date')    # truncdate converts date to simpler format
    ).values_list('day', flat = True).distinct().order_by('day'))
    current_streak = 0
    longest_streak = 0
    for i, day_ in enumerate(days):
        if i == 0 or (day_ - days[i - 1]).days != 1:
            current_streak = 1
        else:
            current_streak += 1

        longest_streak = max(longest_streak, current_streak)

    if user_slips_won:
        most_memorable = user_slips_won.order_by('-total_odds').first()
    else:
        most_memorable = user_slips.annotate(
            total_events = Count('slip_events'),
            events_won = Count(
                Case(When(
                    Q(slip_events__event_won = True), then = F('slip_events')
                ))
            ),
            calc_accuracy = ExpressionWrapper(
                ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
            ),
        ).order_by('-calc_accuracy').first()

    week_days_qs = user_slips.annotate(
        day = ExtractWeekDay('entry_date')
    ).values('day').annotate(
        wins = Count( 
            'id', filter = Q(slip_won = True, settled = True),
            distinct = True
        ),
        slips_no = Count('id', distinct = True),

        total_events = Count('slip_events' ),
        events_won = Count( Case(When(
            Q(slip_events__event_won = True), then = F('slip_events')
        ))),
        calc_accuracy = Round(ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        )),
    ).exclude(slips_no = 0).order_by('day')
    months_qs = user_slips.annotate(
        month = ExtractMonth('entry_date')
    ).values('month').annotate(
        wins = Count( 
            'id', filter = Q(slip_won = True, settled = True),
            distinct = True
        ),
        slips_no = Count('id', distinct = True),

        total_events = Count('slip_events'),
        events_won = Count( Case(When(
            Q(slip_events__event_won = True), then = F('slip_events')
        ))),
        calc_accuracy = Round(ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        )),
    ).exclude(slips_no = 0).order_by('month')  
    
    day_bet_most = WEEK_DAYS_DICT.get(f"{week_days_qs.order_by('-slips_no').first()['day']}")
    day_bet_most_value = week_days_qs.order_by('-slips_no').first()['slips_no']
    day_win_most = WEEK_DAYS_DICT.get(f"{week_days_qs.order_by('-wins').first()['day']}")
    day_win_most_value = week_days_qs.order_by('-wins').first()['wins']
    day_lose_most = WEEK_DAYS_DICT.get(f"{week_days_qs.order_by('calc_accuracy').first()['day']}")
    day_lose_most_value = week_days_qs.order_by('calc_accuracy').first()['calc_accuracy']
    month_bet_most = MONTHS_DICT.get(f"{months_qs.order_by('-slips_no').first()['month']}")
    month_bet_most_value = months_qs.order_by('-slips_no').first()['slips_no']
    best_month = MONTHS_DICT.get(f"{months_qs.order_by('-calc_accuracy').first()['month']}")
    best_month_value = months_qs.order_by('-calc_accuracy').first()['calc_accuracy']
    worst_month = MONTHS_DICT.get(f"{months_qs.order_by('calc_accuracy').first()['month']}")
    worst_month_value = months_qs.order_by('calc_accuracy').first()['calc_accuracy']

    # Teams and Players
    home_teams_qs = user_slips_events.values('participants__0').annotate(
        total_events = Count('id'),
        events_won = Count('id', filter = Q(event_won = True)),
    )
    away_teams_qs = user_slips_events.values('participants__1').annotate(
        total_events = Count('id'),
        events_won = Count('id', filter = Q(event_won = True)),
    )
    team_stats = defaultdict(lambda: {'total_events': 0, 'events_won': 0})  
    teams_list = []
    for item in home_teams_qs:
        team = item['participants__0']
        team_stats[team]['total_events'] += item['total_events']
        team_stats[team]['events_won'] += item['events_won']
    for item in away_teams_qs:
        team = item['participants__1']
        team_stats[team]['total_events'] += item['total_events']
        team_stats[team]['events_won'] += item['events_won']

    for team, stats in team_stats.items():
        total = stats['total_events']
        wins = stats['events_won']
        accuracy = round((wins / total) * 100)
        teams_list.append( SimpleNamespace(
            team = team,
            total_events = total,
            events_won = wins,
            calc_accuracy = accuracy,
        ))

    teams_list.sort(key = lambda x: x.total_events, reverse = True)
    total_teams_predicted = len(set(list(user_slips_events.values_list('participants__0', flat = True).distinct()) + list(user_slips_events.values_list('participants__1', flat = True).distinct())))

    players_slip_events = user_slips_events.filter(market_group = 'player')
    players_qs = players_slip_events.values('player_involved').annotate(
        total_events = Count('id', filter = Q(event_settled = True)),
        events_won = Count(
            'id', filter = Q(event_won = True)
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ),
    )[:10]
    if players_slip_events.count() > 0:
        players_selection_accuracy = round( (players_slip_events.filter(event_won = True, event_settled = True).count() / players_slip_events.count()) * 100 )
    else:
        players_selection_accuracy = 0

    # Sports and Competitions
    sports_qs = user_slips_events.values('sport').annotate(
        total_events = Count('id', filter = Q(event_settled = True)),
        events_won = Count(
            'id', filter = Q(event_won = True)
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ),
    ).order_by('total_events').exclude(total_events = 0)[:7]
    competitions_qs = user_slips_events.values('competition').annotate(
        total_events = Count('id', filter = Q(event_settled = True)),
        events_won = Count(
            'id', filter = Q(event_won = True)
        ),
        calc_accuracy = ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ),
    ).order_by('total_events').exclude(total_events = 0)[:7]

    # Markets
    markets_qs = user_slips_events.exclude(market_group = 'player').annotate(
        market_class = Case(
            When(market__icontains = 'Over/Under', then = Value("Over/Under")),
            When(market__icontains = 'Corners', then = Value("Corners")),
            When(market__icontains = 'Draw No Bet', then = Value("DNB")),
            default = F('market'),
            output_field = CharField()
        )
    ).values('market_class').annotate(
        total_events = Count('id', filter = Q(event_settled = True)),
        events_won = Count(
            'id', filter = Q(event_won = True)
        ),
        calc_accuracy = Round(ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ))
    ).exclude(total_events = 0)
    markets_charts_qs = markets_qs.order_by('total_events').exclude(total_events = 0)[:5]

    # Extra
    odds_qs = user_slips_events.filter(event_settled = True).annotate(
        odds_range = Case(
            When(event_odd__lt = 1.2, then = Value('<1.2')),
            When(event_odd__lt = 1.5, then = Value('1.2–1.5')),
            When(event_odd__lt = 2.0, then = Value('1.5–2.0')),
            When(event_odd__lt = 3.0, then = Value('2.0–3.0')),
            When(event_odd__lt = 5.0, then = Value('3.0–5.0')),
            default = Value('>5.0'),
            output_field = CharField(),
        ),
        odds_range_id = Case(
            When(event_odd__lt = 1.2, then = Value('1')),
            When(event_odd__lt = 1.5, then = Value('2')),
            When(event_odd__lt = 2.0, then = Value('3')),
            When(event_odd__lt = 3.0, then = Value('4')),
            When(event_odd__lt = 5.0, then = Value('5')),
            default = Value('6'),
            output_field = CharField(),
        ),
    ).values('odds_range').annotate(
        total_events = Count('id'),
        events_won = Count(
            'id', filter = Q(event_won = True)
        ),
        calc_accuracy = Round(ExpressionWrapper(
            ( F('events_won') * 100.0 ) / NullIf(F('total_events'), 0), output_field = FloatField()
        ))        
    ).exclude(total_events = 0).order_by('odds_range_id')

    avg_lengths_list = list(
        user_slips.annotate(selections_no = Count('slip_events'))
        .values_list('selections_no', flat = True)
    )
    wins_lengths_list = list(
        user_slips_won.annotate(selections_no = Count('slip_events'))
        .values_list('selections_no', flat = True)
    )
    
    avg_length = statistics.median(avg_lengths_list)
    optimal_length = statistics.median(wins_lengths_list)
    time_since_win = (dj_tz.make_aware(datetime.now()) - user_slips_won.order_by('-id').first().entry_date).days
    
    insights_data = SimpleNamespace(
        the_best = the_best.first(),
        most_accurate = most_accurate.first(),
        current_month = current_month,
        current_month_txt = MONTHS_DICT[f'{current_month}'],
        most_accurate_pure = most_accurate_pure,
        accuracy_qs_cm = accuracy_qs_cm.order_by('-calc_accuracy').exclude(total_events = 0)[:5],
        top_scorers_qs_cm = accuracy_qs_cm.order_by('-total_pure_odds').exclude(total_events = 0)[:5],
        top_scorers_qs = the_best[:5],
        accuracy_qs = most_accurate[:5],
        largest_win = highest_pure_odds,
        largest_win_cm = highest_pure_odds_cm,
        longest_streak = longest_streak,
        most_memorable = most_memorable,
        active_days = len(days),
        week_days_chart_data = week_days_qs,
        week_days_list = [ WEEK_DAYS_DICT.get(f"{day}") for day in list(week_days_qs.values_list('day', flat = True)) ],
        week_days_slips_list = list(week_days_qs.values_list('slips_no', flat = True)),
        week_days_accuracy_list = list(week_days_qs.values_list('calc_accuracy', flat = True)),
        week_days_wins_list = list(week_days_qs.values_list('wins', flat = True)),
        months_chart_data = months_qs,   # the logic incase it's not complete
        months_list = [ MONTHS_DICT.get(f"{month}") for month in list(months_qs.values_list('month', flat = True)) ],
        months_slips_list = list(months_qs.values_list('slips_no', flat = True)),
        months_accuracy_list = list(months_qs.values_list('calc_accuracy', flat = True)),
        months_wins_list = list(months_qs.values_list('wins', flat = True)),
        day_bet_most = day_bet_most,
        day_bet_most_value = day_bet_most_value,
        day_win_most = day_win_most,
        day_win_most_value = day_win_most_value,
        day_lose_most = day_lose_most,
        day_lose_most_value = day_lose_most_value,
        month_bet_most = month_bet_most,
        month_bet_most_value = month_bet_most_value,
        best_month = best_month,
        best_month_value = best_month_value,
        worst_month = worst_month,
        worst_month_value = worst_month_value,
        teams_chart_data = teams_list[:7],
        teams_names_list = [ team.team for team in teams_list[:7]],
        teams_selections_no_list = [ team.total_events for team in teams_list[:7]],
        total_teams_predicted = total_teams_predicted,
        players_chart_data = players_qs,
        players_selection_accuracy = players_selection_accuracy,
        sports_chart_data = sports_qs,
        sports_list = list(sports_qs.values_list('sport', flat = True)),
        sports_selections_list = list(sports_qs.values_list('total_events', flat = True)),
        competitions_chart_data = competitions_qs,
        competitions_list = list(competitions_qs.values_list('competition', flat = True)),
        competitions_selections_list = list(competitions_qs.values_list('total_events', flat = True)),
        competitions_predicted = user_slips_events.values('competition').distinct().count(),
        markets_chart_data = markets_qs[:7],
        markets_list = list(markets_charts_qs.values_list('market_class', flat = True)),
        markets_selections_list = list(markets_charts_qs.values_list('total_events', flat = True)),
        markets_accuracy_list = list(markets_charts_qs.values_list('calc_accuracy', flat = True)),
        fav_market = markets_qs.order_by('-total_events').first(),
        best_market = markets_qs.order_by('-calc_accuracy').first(),
        worst_market = markets_qs.order_by('calc_accuracy').first(),
        odds_list = list(odds_qs.values_list('odds_range', flat = True)),
        odds_accuracy_list = list(odds_qs.values_list('calc_accuracy', flat = True)),
        odds_selections_list = list(odds_qs.values_list('total_events', flat = True)),
        avg_length = avg_length,
        optimal_length = optimal_length,
        days_since_win = time_since_win,
        slips_won = bool(user_slips_won),
    )
    return insights_data