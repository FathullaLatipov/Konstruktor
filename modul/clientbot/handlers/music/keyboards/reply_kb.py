from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from modul.clientbot.keyboards.reply_kb import MUSIC_MENU_BUTTONS_TEXT


async def music_main_menu():
    kbrd = ReplyKeyboardBuilder()
    kbrd.row(
        *[KeyboardButton(text=i) for i in MUSIC_MENU_BUTTONS_TEXT],
        KeyboardButton(text=_("🔙 Назад")),
        width=1
    )
    return kbrd.as_markup(resize_keyboard=True)
