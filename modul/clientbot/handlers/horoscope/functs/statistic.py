from datetime import datetime, timedelta
from db.models import HoroscopeAnalitics
from dataclasses import dataclass
from aiogram.utils.i18n import gettext as _


@dataclass
class HoroscopeAnaliticsData:
    today: int
    week: int
    month: int
    all: int


async def add_statistic(bot_username: str):
    now = datetime.now()
    instance = await HoroscopeAnalitics.filter(bot_username=bot_username, created_at__gte=now.date()).first()
    if instance:
        instance.count += 1
        instance.updated_at = now
        await instance.save()
    else:
        await HoroscopeAnalitics.create(bot_username=bot_username, count=1)


async def get_horoscope_data(bot_username: str = None):
    kwargs = {}
    now = datetime.now()
    if bot_username:
        kwargs["bot_username"] = bot_username
    today_count = sum([x.count for x in await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date())] or [0])
    week_count = sum([x.count for x in
                      await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date() - timedelta(days=7))] or [0])
    month_count = sum([x.count for x in
                       await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date() - timedelta(days=30))] or [
                          0])
    all_count = sum([x.count for x in await HoroscopeAnalitics.filter(**kwargs)] or [0])
    return HoroscopeAnaliticsData(today_count, week_count, month_count, all_count)


async def get_statistic(bot_username: str = None):
    kwargs = {}
    now = datetime.now()
    if bot_username:
        kwargs["bot_username"] = bot_username
    today_count = sum([x.count for x in await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date())] or [0])
    week_count = sum([x.count for x in
                      await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date() - timedelta(days=7))] or [0])
    month_count = sum([x.count for x in
                       await HoroscopeAnalitics.filter(**kwargs, created_at__gte=now.date() - timedelta(days=30))] or [
                          0])
    all_count = sum([x.count for x in await HoroscopeAnalitics.filter(**kwargs)] or [0])
    return _("📈 Модуль: Гороскоп (использование)\n"
             "Сегодня: {today_count}\n"
             "Неделя: {week_count}\n"
             "Месяц: {month_count}\n"
             "Всего: {all_count}\n\n").format(today_count=today_count, week_count=week_count, month_count=month_count,
                                              all_count=all_count)
