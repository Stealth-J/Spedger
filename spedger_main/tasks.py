from celery import shared_task
from .models import *
from .async_helpers import *
from asgiref.sync import async_to_sync, sync_to_async
from django.utils import timezone as dj_tz
from datetime import datetime
from .helpers import rank_users_leaderboards, send_mail_with_template
from time import perf_counter


def link_json_to_obj_and_update(data, code_tuple):
    _, slip_obj = code_tuple
    slip_events = list( slip_obj.slip_events.filter(event_settled = False) )
    outcomes_dict_ids = {}
    outcomes_dict_teams = {}
    accepted_status = ['Ended', 'Cancelled']

    for each in data.get('outcomes'):
        try:
            if each.get('matchStatus') in accepted_status:
                eventId = each.get('eventId')
                home = each.get('homeTeamName')
                away = each.get('awayTeamName')
                teams = f'{home} - {away}'
                market = each.get('markets')[0].get('desc')
                pick = each.get('markets')[0].get('outcomes')[0].get('desc')
                comp = each.get('sport').get('category').get('tournament').get('name')

                outcomes_dict_ids[eventId, market, pick, comp] = each
                outcomes_dict_teams[teams, market, pick, comp] = each
            else:
                CustomError.objects.create(
                    error_class = 'Unknown Match Status',
                    error_txt = f'Game between {each.get('homeTeamName')} and {each.get('awayTeamName')}. Event id - {each.get('eventId')}'
                )

        except Exception as e:
            print(f'Parsing data for JSON changed - {str(e)}')

    updated_events = []
    for each in slip_events:
        try:
            teams = ' - '.join(each.participants)
            if each.event_id:
                event_tuple = (each.event_id, each.market, each.pick, each.competition)
                event_outcome = outcomes_dict_ids.get(event_tuple, '')
            else:
                event_tuple = (teams, each.market, each.pick, each.competition)
                event_outcome = outcomes_dict_teams.get(event_tuple, '')

            if event_outcome != '':
                each.event_settled = True
                if event_outcome.get('matchStatus') == 'Cancelled':
                    each.event_cancelled = True
                else:
                    isWinning = event_outcome.get('markets')[0].get('outcomes')[0].get('isWinning')
                    if isWinning:
                        each.event_won = bool(int(isWinning))
                updated_events.append(each)

        except Exception as e:
            print(f'Error - {str(e)}')
        
    return updated_events


@shared_task
def update_live_games():
    t = perf_counter()

    active_slips = list( Slip.objects.prefetch_related('slip_events').filter(settled = False))
    codes_tuple = [ (slip_obj.slip_code, slip_obj) for slip_obj in active_slips ]
    results = async_to_sync(scrape_slips_info)(codes_tuple)
    updated_events_total = []

    print(f'Scraping took {perf_counter()-t:.2f}s')

    for result, code_tuple in zip(results, codes_tuple):
        if result[0]:
            try:
                data = result[1].get('data')
                updated_events = link_json_to_obj_and_update(data, code_tuple)
                updated_events_total.extend(updated_events)

            except Exception as e:
                print(f'Error - {str(e)}')

    SlipEvent.objects.bulk_update(updated_events_total, ['event_settled', 'event_won', 'event_cancelled', 'event_postponed'])


@shared_task
def update_settled_slips():
    unsettled_slips = list(Slip.objects.prefetch_related('slip_events').filter(settled = False) )
    updated_slips = []

    for slip in unsettled_slips:
        total_events = slip.slip_events.count()
        settled_events = slip.slip_events.filter(event_settled = True).count()
        events_won = slip.slip_events.filter(event_won = True).count()

        if total_events == settled_events:
            slip.settled = True
        if total_events == events_won:
            slip.slip_won = True
            send_perfect_slips_mails.delay(slip)

        updated_slips.append(slip)
    Slip.objects.bulk_update(updated_slips, ['settled', 'slip_won'])


@shared_task
def update_ongoing_duels():
    ongoing_duels = Duel.objects.prefetch_related('duellists').filter(settled = False, duel_status = 'accepted')
    updated_duels = []

    for each in ongoing_duels:
        duellists_slip_status = list( each.duellists.values_list('slip__settled', flat = True) )
        duel_settled = all(duellists_slip_status)
        if duel_settled:
            each.settled = True
            each.settled_date = dj_tz.make_aware(datetime.now())
            if each.winner and each.winner != 'Draw':
                each.winning_user = each.winner.user
                recipient = each.duellists.exclude(user = each.winner.user).first()
                send_duels_congratulatory_mails.delay(each.winner.id, recipient.id, duel_won = True)

            updated_duels.append(each)

    Duel.objects.bulk_update(updated_duels, ['settled', 'settled_date', 'winning_user'])


@shared_task
def update_players_ranks():
    all_games = WeeklyGame.objects.prefetch_related('game_participants').order_by('id')
    previous_game = all_games.exclude(current_game = True).last()
    players_list = []

    game_players = rank_users_leaderboards(previous_game.game_participants.all())
    for each in game_players:
        each.ranking = each.rank
        players_list.append(each)

    WeeklyGameParticipant.objects.bulk_update(players_list, ['ranking'])
    send_congratulatory_mails.delay()


@shared_task 
def send_congratulatory_mails():
    all_games = WeeklyGame.objects.prefetch_related('game_participants').order_by('id')
    previous_game = all_games.exclude(current_game = True).last()

    for player in previous_game.game_participants.all():
        if player.ranking <= 5:
            message = 'Congratulations on your top 5 finish.'
            if player.ranking == 1:
                message = 'Congratulations - you finished 1st place this week'
            
            context = {
                'username': player.user.username,
                'message': message,
                'ranking': player.ranking,
                'start_date': previous_game.start_date.strftime("%d %b, %Y"),
                'end_date': previous_game.end_date.strftime("%d %b, %Y"),
            }

            send_mail_with_template('Weekly Result', 'emails/weekly_result.html', context, player.user.email)


@shared_task
def send_duels_congratulatory_mails(user_obj_id, recipient_id, duel_won = False):
    user_obj = DuellistInfo.objects.filter(id = user_obj_id)
    recipient = DuellistInfo.objects.filter(id = recipient_id)
    score = 'none'

    if duel_won:
        title = 'Duel Won'
        message = f'Congratulations. You beat {recipient.user.username} in your recent duel'
        score = f'{user_obj.slip.win_percentage} - {recipient.slip.win_percentage}'

    else:
        title = 'Duel Received'
        message = f'You have received a duel request from {recipient.user.username}'

    context = {
        'title': title,
        'username': recipient.user.username,
        'message': message, 
        'score': score
    }
    send_mail_with_template('Duels', 'emails/duel_notifs.html', context, user_obj.user.email)


@shared_task
def send_perfect_slips_mails(slip):
    context = {
        'username': slip.user.username,
        'slip_code': slip.slip_code, 
    }

    send_mail_with_template('Perfect Slip', 'emails/perfect_slip_notifs.html', context, slip.user.email)