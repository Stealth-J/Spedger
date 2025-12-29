from django import template
from ..countries import COUNTRY_CODES

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