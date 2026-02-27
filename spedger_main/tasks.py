from celery import shared_task
from .models import *
from .async_helpers import *
from asgiref.sync import async_to_sync, sync_to_async
from django.utils import timezone as dj_tz
from datetime import datetime


def link_json_to_obj_and_update(data, code_tuple):
    _, slip_obj = code_tuple
    slip_events = list( slip_obj.slip_events.filter(event_settled = False) )
    outcomes_dict_ids = {}
    outcomes_dict_teams = {}

    for each in data.get('outcomes'):
        try:
            if each.get('matchStatus') == 'Ended':
                eventId = each.get('eventId')
                home = each.get('homeTeamName')
                away = each.get('awayTeamName')
                teams = f'{home} - {away}'
                market = each.get('markets')[0].get('desc')
                pick = each.get('markets')[0].get('outcomes')[0].get('desc')
                comp = each.get('sport').get('category').get('tournament').get('name')

                outcomes_dict_ids[eventId, market, pick, comp] = each
                outcomes_dict_teams[teams, market, pick, comp] = each
        
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
                isWinning = event_outcome.get('markets')[0].get('outcomes')[0].get('isWinning')
                if isWinning:
                    each.event_won = bool(int(isWinning))
                updated_events.append(each)

        except Exception as e:
            print(f'Error - {str(e)}')
        
    return updated_events


@shared_task
def update_live_games():
    active_slips = list( Slip.objects.prefetch_related('slip_events').filter(settled = False))
    codes_tuple = [ (slip_obj.slip_code, slip_obj) for slip_obj in active_slips ]
    results = async_to_sync(scrape_slips_info)(codes_tuple)
    updated_events_total = []

    for result, code_tuple in zip(results, codes_tuple):
        if result[0]:
            try:
                data = result[1].get('data')
                updated_events = link_json_to_obj_and_update(data, code_tuple)
                updated_events_total.extend(updated_events)

            except Exception as e:
                print(f'Error - {str(e)}')

    SlipEvent.objects.bulk_update(updated_events_total, ['event_settled', 'event_won'])


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
                print(each.winner)
                each.winning_user = each.winner.user

            updated_duels.append(each)

    Duel.objects.bulk_update(updated_duels, ['settled', 'settled_date', 'winning_user'])
