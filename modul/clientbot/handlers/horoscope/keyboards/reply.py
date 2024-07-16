from aiogram.utils.keyboard import ReplyKeyboardBuilder
from clientbot.keyboards.reply_kb import HOROSCOPE_BUTTONS_TEXT
from aiogram.utils.i18n import gettext as _

from clientbot.shortcuts import get_bot, have_one_module


def zodiac_signs_builder() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    signs = [
        _("♈ Овен"), _("♉ Телец"), _("♊ Близнецы"), _("♋ Рак"),
        _("♌ Лев"), _("♍ Дева"), _("♎ Весы"), _("♏ Скорпион"),
        _("♐ Стрелец"), _("♑ Козерог"), _("♒ Водолей"), _("♓ Рыбы")
    ]

    [builder.button(text=sign) for sign in signs]
    builder.button(text=_("Вернуться"))

    builder.adjust(4)
    return builder.as_markup(resize_keyboard=True)


async def main_horoscope_menu() -> ReplyKeyboardBuilder:
    builder = ReplyKeyboardBuilder()
    [builder.button(text=sign) for sign in HOROSCOPE_BUTTONS_TEXT]
    bot = await get_bot()
    if not have_one_module(bot, 'horoscope'):
        builder.button(text=_("Отмена"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)
