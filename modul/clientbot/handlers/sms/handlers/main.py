from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram import types
from clientbot.handlers.sms.keyboards import reply_kb
from clientbot.handlers.sms.shortcuts import get_order_history, print_order_history
from loader import client_bot_router


@client_bot_router.message(text=__("📲 Купить номер"), flags={'throttling_key': 'buy_number'})
async def buy_number(message: types.Message):
    text = _("1. Выберете страну, номер телефона которой будет Вам выдан")
    markup = await reply_kb.countries_kb()
    await message.answer(text, reply_markup=markup)


@client_bot_router.message(text=__("📫 Все СМС операции"), flags={'throttling_key': 'sms_history'})
async def sms_history(message: types.Message):
    orders, count = await get_order_history(message.from_user.id)
    text = await print_order_history(orders)
    if text is None:
        await message.answer(_("Ничего не найдено"))
    else:
        await message.answer(text, reply_markup=reply_kb.order_history_kb(count))
