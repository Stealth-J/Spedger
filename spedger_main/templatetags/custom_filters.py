from django import template
from ..countries import COUNTRY_CODES
from ..slip_helpers import TIME_STRING_FORMAT
import math

register = template.Library()


@register.filter
def country_flag(country_name):
    country_code = COUNTRY_CODES.get(country_name.lower())
    return f'imgs/flags/{country_code}.png'


@register.filter
def return_none(val):
    if val == '':
        return 'None'
    return val


@register.filter
def return_0_if_none(val):
    if val == None:
        return 0
    return val


@register.filter
def return_dots_if_none(data):
    if data:
        return data
    else:
        return '...'


@register.filter
def format_timesince(date):
    dates = date.split(', ')
    num, unit = dates[0].split()
    new_date = f'{num}{unit[0]}'
    return new_date


@register.filter
def format_date(date):
    return date.strftime(TIME_STRING_FORMAT)


@register.filter
def compact_num(num):
    if int(num) > 99:
        return '99+'
    
    return num


@register.filter
def order_slip(qs):
    return qs.order_by('-entry_date')


@register.filter
def filter_chat_odds(odds):
    odds = float(odds)
    if odds >= 1000000:
        return '1M+'
    elif odds > 10000:
        odds = round(math.floor(odds), -3)
        return f'{str(odds).removesuffix('000')}k+'
    elif odds > 1000:
        odds = math.floor(odds)
        return round(odds, -3)
    else:
        if odds == 0:
            return 0
        return round(odds, 1)


@register.filter
def format_chat_date(date):
    new_date = format_timesince(date)
    if new_date == '0m':
        new_date = 'Just Now'
    else :
        new_date = f'{new_date} ago.'

    return new_date