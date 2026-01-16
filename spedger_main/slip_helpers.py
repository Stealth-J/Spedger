from datetime import datetime, timezone
from django.utils import timezone as django_timezone
import requests
from requests.exceptions import Timeout, ConnectionError
from urllib.parse import urlparse
from types import SimpleNamespace
from .models import Slip, SlipEvent, DiaryEntry


TIME_STRING_FORMAT = "%d %b %y, %H:%M"
SITES_URLS = {
    'sportybet': "https://www.sportybet.com/api/ng/orders/share/{}?_t={}",
}
GAME_STATUS = {
    'not start': 'pending',
    'ended': 'finished',
    'abandoned': 'finished',
    'none': 'pending',
    'h1': 'live',
    'h2': 'live',
    'ht': 'live',
    'q1': 'live',
    'q2': 'live',
    'q3': 'live',
    'q4': 'live',
    'live': 'live',
    'aet': 'finished',
    'ap': 'finished',
    'suspended': 'finished',
}
SLIP_DOMAINS = {
    "sportybet": ["sportybet.com", "sportybet.ng", "www.sportybet.com", "www.sportybet.ng"],
}
PREVIEW_HEADERS = {
    'sportybet': {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 
        'User-Agent': 'Mozilla/5.0', 
        'Origin': 'https://www.sportybet.com'
    },   
}
SUPPORTED_SPORTS = ['Football', 'Baseball', 'Tennis', 'American Football', 'Basketball']


class ScrapingError(Exception):
    pass


def format_time(time_data, ms = True):
    ms_time = time_data
    if ms:
        ms_time = datetime.fromtimestamp(time_data / 1000, tz = timezone.utc)
    
    time = ms_time.strftime(TIME_STRING_FORMAT)
    return time

def get_timestamp(platform):
    if platform == 'sportybet':
        dt = datetime.now()
    else:
        return
    
    timestamp = int(dt.timestamp() * 1000)
    return timestamp

def get_url(slip_code, platform):
    try:
        url_raw = SITES_URLS.get(platform, None)
        timestamp = get_timestamp(platform)
        url = url_raw.format(slip_code, timestamp)
        return url
    
    except Exception as e:
        return

def check_game_expiry(string):
    dt = datetime.strptime(string, TIME_STRING_FORMAT)
    dt = dt.replace(tzinfo = timezone.utc)
    dt_now = datetime.now().replace(tzinfo = timezone.utc)
    return int(dt.timestamp() * 1000) < int(dt_now.timestamp() * 1000)


def validate_url(url, platform):
    expected_domains = SLIP_DOMAINS.get(platform)
    if not expected_domains:
        return f"Unknown platform '{platform}' "

    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return f'URL is not valid. {url}'
    
    except Exception:
        return 'Malformed URL'
    
    domain = parsed.netloc.lower()
    if domain not in expected_domains:
        return f"Not a valid {platform} slip "

    return ''

def scrape_site(url, platform):
    headers = PREVIEW_HEADERS.get(platform)
    if not headers:
        return (False, f"Unknown platform '{platform}'")
    
    error_txt = validate_url(url, platform)
    if error_txt != '':
        return (False, error_txt)
    
    try:
        response = requests.get(url, headers = headers)
        print("Fetch time:", response.elapsed.total_seconds())
        response.raise_for_status()
        data = response.json()
        scrape_msg = data.get('message')

        if scrape_msg != 'Success':
            return (False, scrape_msg)
        return (True, data)

    except Timeout:
        return (False, 'Request timed out')
    except ConnectionError as e:
        print(e)
        return (False, 'There was a connection error')
    except Exception as e:
        return (False, f'Failed to fetch slip data: {str(e)}')


def remove_unsupported_selections(games_data):
    valid_games_data = []
    valid_ids_list = []

    for game in games_data:
        if game.game_id not in valid_ids_list:
            if game.sport in SUPPORTED_SPORTS:
                if game.status.lower() != 'not start':
                    continue
                if game.expired:
                    continue
                if not game.home_team or not game.away_team:
                    continue

                valid_ids_list.append(game.game_id)
                valid_games_data.append(game)
    return valid_games_data


def create_slip_obj(request, valid_games, slip_info, code, wkly = False, log_in_diary = False):
    try:
        slip_events = []
        profile_obj = request.user.user_profile

        slip_obj = Slip.objects.create(
            user = request.user,
            slip_code = code,
            total_odds = slip_info.total_odds,
            weekly = wkly
        )
        if profile_obj.log_all_slips or log_in_diary == True:
            entry_obj = DiaryEntry.objects.create(slip = slip_obj, user = request.user)

        for game in valid_games:
            teams = [game.home_team, game.away_team]
            naive_date = datetime.strptime(game.start_time, TIME_STRING_FORMAT)

            slip_event_obj = SlipEvent(
                slip = slip_obj,
                participants = teams,
                pick = game.pick,
                market = game.market_type,
                sport = game.sport,
                competition = game.league,
                event_odd = game.odds,
                event_date = django_timezone.make_aware(naive_date)
            )
            slip_events.append(slip_event_obj)

        SlipEvent.objects.bulk_create(slip_events, batch_size = 20)

    except Exception as e:
        raise Exception('Error while creating slip object')
    
    if log_in_diary == True:
        return entry_obj
    return slip_obj