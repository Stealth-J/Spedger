from random import randint

def duel_winner(duelists):
    highest_percent = 0
    highest_odds = 0
    current_winner = None

    for duelist in duelists:
        if duelist.slip:
            if duelist.slip.win_percentage > highest_percent:
                highest_percent = duelist.slip.win_percentage
                current_winner = duelist
                highest_odds = duelist.slip.total_odds
            elif duelist.slip.win_percentage == highest_percent:
                if duelist.slip.total_odds > highest_odds:
                    highest_odds = duelist.slip.total_odds
                    current_winner = duelist
                elif duelist.slip.total_odds == highest_odds:
                    current_winner = 'Draw'
        else:
            continue

    return current_winner


def background_img_func():
    background_rand_num = randint(1, 10)
    return f'background{background_rand_num}'


def avatar_img_func():
    avatar_rand_num = randint(1, 20)
    return f'avatar{avatar_rand_num}'


def return_slips_events(slips, accurate = False):
    slips_events = []
    accurate_events = []
    for slip in slips:
        for evt in slip.slip_events.filter(event_settled = True):
            slips_events.append(evt)
    if accurate:
        accurate_events = [ evt for evt in slips_events if evt.event_settled and evt.event_won ]
    
    return slips_events, accurate_events


def get_duel_record(duels_obj, user_obj, recipient_user = None):
    duels_obj = duels_obj.filter(settled = True)
    if recipient_user:
        duels_obj = duels_obj.filter(duellists__user = recipient_user)
        
    duels_won = duels_obj.filter(winning_user = user_obj).count()
    duels_drawn = duels_obj.filter(winning_user = None).count()
    duels_lost = duels_obj.count() - duels_won - duels_drawn
    return f'({duels_won}-{duels_drawn}-{duels_lost})'