from django import template

register = template.Library()


@register.filter
def bot_status(bot_enable):
    return "Включен" if bot_enable else "Отключен"
