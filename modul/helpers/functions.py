from config import settings
from aiogram import Bot
from clientbot import shortcuts
from db import models
from loader import bot_session


async def send_message(bot_token: str, uid: str, message: str, reply_markup=None):
    try:
        async with Bot(token=bot_token, session=bot_session).context(auto_close=False) as bot:
            await bot.send_message(uid, message, reply_markup=reply_markup)
        return True
    except:
        return False


def get_user_percentage(uid: int, referrals: int):
    if uid in settings.SPONSORS:
        referrals_gte = settings.SPONSORS[uid]['referrals']
        percent = settings.SPONSORS[uid]['percent']
        if referrals >= referrals_gte:
            return percent
    elif referrals >= 500:
        return 7
    return 5
