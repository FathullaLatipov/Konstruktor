from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton
from aiogram.utils.i18n import gettext as _

from clientbot.keyboards.reply_kb import CHATGPT_BUTTONS_TEXT


def get_chatgt_main_kbrd():
    kbrd = ReplyKeyboardBuilder()
    kbrd.row(
        *[KeyboardButton(text=i) for i in CHATGPT_BUTTONS_TEXT],
        KeyboardButton(text=_("🔙 Назад")),
        width=2
    )
    return kbrd.as_markup(resize_keyboard=True)

def cancel_input_prompt():
    kbrd = ReplyKeyboardBuilder()
    kbrd.add(
        KeyboardButton(text=_("Отменить ввод")),
    )
    return kbrd.as_markup(resize_keyboard=True)

def back_btn():
    markup = ReplyKeyboardBuilder()
    return markup.row(KeyboardButton(text='Окончить сеанс'), width=1).as_markup(resize_keyboard=True)