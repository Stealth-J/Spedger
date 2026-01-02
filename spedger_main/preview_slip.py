from .slip_helpers import *
import math


def preview(code, platform = 'sportybet'):
    try:
        url = get_url(code, platform)
        scraping_success, data = scrape_site(url, platform)
        if not scraping_success:
            raise ScrapingError(data)

        outcomes = data.get("data").get("outcomes")
        games_data = []
        games_ids_list = set()

        for sn, outcome in enumerate(outcomes):
            sport_id = outcome.get('sport').get('id')
            sport_name = outcome.get('sport').get('name')
            sport_icon = f'img/sports_icons/{sport_name.lower()}.svg' or None
            home = outcome.get("homeTeamName")
            away = outcome.get("awayTeamName")
            teams = (home, away)
            tournament = outcome.get("sport", {}).get("category", {}).get("tournament", {}).get("name")
            start_time_ms = outcome.get("estimateStartTime")
            start_time = format_time(start_time_ms)
            status = outcome.get("matchStatus", 'none')
            status_class = GAME_STATUS.get(status.lower(), 'unknown')
            market_data = outcome.get("markets")
            market_data = market_data[0] if market_data else {}
            market_desc = market_data.get("desc")
            pick_data = market_data.get("outcomes")
            pick_data = pick_data[0] if pick_data else {}
            pick = pick_data.get("desc")
            pick_id = pick_data.get('id')
            odds = pick_data.get("odds") if not outcome.get('setScore') else '-'
            market_id =  market_data.get('id')
            tourney_id = outcome.get("sport").get("category").get("tournament").get("id")
            game_id = outcome.get('eventId')
            specifier = market_data.get('specifier')
            
            supported = True

            game_data = SimpleNamespace(
                id_ = str(sn),
                home_team = home,
                away_team = away,
                teams = teams,
                league = tournament, 
                start_time = start_time,
                expired = check_game_expiry(start_time),
                status = status,
                market_type = market_desc, 
                pick = pick, 
                pick_id = pick_id,
                odds = odds, 
                status_class = status_class, 
                sport = sport_name,
                sport_id = sport_id,
                sport_icon = sport_icon,
                supported = supported,
                tourney_id = tourney_id,
                market_id = market_id,
                game_id = game_id,
                specifier = specifier,
            )

            games_ids_list.add(game_id)
            games_data.append(game_data)

        print('Finished Successfully')
        valid_games_data = remove_unsupported_selections(games_data, games_ids_list)
        return (True, valid_games_data)

    except Exception as e:
        print(str(e))
        return (False, e)


def get_slip_details(valid_games):
    odds_list = []
    valid_games_raw = []
    games_ids = []
    for game in valid_games:
        valid_games_raw.append(vars(game))
        games_ids.append( game.id_ )
        odds_list.append( float(game.odds) )

    total_odds = round(math.prod(odds_list), 2)
    selections_no = len(valid_games)
    return SimpleNamespace(
        total_odds = total_odds,
        selections_no = selections_no,
        valid_games_raw = valid_games_raw,
        games_ids = games_ids
    )


def save_preview_changes(valid_games, removed_ids):
    removed_ids = removed_ids.split(',')
    valid_games_left = []

    for game in valid_games:
        if game['id_'] in removed_ids:
            continue
        valid_games_left.append(SimpleNamespace(game))

    return valid_games_left