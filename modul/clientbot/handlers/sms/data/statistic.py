

from db import models


def get_statistic(bot: models.Bot = None):
    kwargs = {}
    if bot:
        kwargs["user__bot"] = bot
    orders = models.SMSOrder.filter(**kwargs)
    return {
        "Всего заказов": bot.orders.count(),
        "Всего заказов в работе": bot.orders.filter(status=1).count(),
        "Всего заказов завершено": bot.orders.filter(status=6).count(),
        "Всего заказов отменено": bot.orders.filter(status=8).count(),
    }