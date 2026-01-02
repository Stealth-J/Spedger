import copy
import requests

BOOKING_URLS = {
    'sportybet': 'https://www.sportybet.com/api/ng/orders/share'
}
BOOKING_HEADERS = {
    'sportybet': {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "Origin": "https://www.sportybet.com",
        "Referer": "https://www.sportybet.com/",
    }
}
sporty_payload_raw = {
    "selections": []
}
PAYLOAD_RAW = {
    'sportybet': sporty_payload_raw,
}


def prepare_payload(valid_games):
    payload = copy.deepcopy(PAYLOAD_RAW["sportybet"])
    for game in valid_games:
        # market_id, specifier, pick_id = game['booking_data']
        game_id = game.game_id
        market_id = game.market_id
        specifier = game.specifier
        pick_id = game.pick_id
        payload["selections"].append(
            { "eventId": game_id, "marketId": market_id, "specifier": specifier, "outcomeId": pick_id }
        )

    return payload

def book(valid_games):
    try:
        payload = prepare_payload(valid_games)

        response = requests.post(BOOKING_URLS['sportybet'], json = payload, headers = BOOKING_HEADERS["sportybet"], timeout = 25)
        response.raise_for_status()
        data = response.json()
        if data.get("bizCode") != 10000:
            return (False, data.get("message", "Unknown error"))
        
        booking_code = data['data']['shareCode']
    
    except Exception as e:
        return (False, e)
    
    return (True, booking_code)