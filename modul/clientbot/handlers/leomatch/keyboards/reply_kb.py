from aiogram.types import KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder



def begin_registration():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Давай, начнем!")))
    builder.add(KeyboardButton(text=("Я не хочу никого искать")))
    return builder.as_markup(resize_keyboard=True)


def chooice_sex():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Я парень")))
    builder.add(KeyboardButton(text=("Я девушка")))
    return builder.as_markup(resize_keyboard=True)


def final_registration():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Да")))
    builder.add(KeyboardButton(text=("Изменить анкету")))
    return builder.as_markup(resize_keyboard=True)


def which_search():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Девушку")))
    builder.add(KeyboardButton(text=("Парня")))
    builder.add(KeyboardButton(text=("Мне всё равно")))
    return builder.as_markup(resize_keyboard=True)


def cancel():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Отменить")))
    return builder.as_markup(resize_keyboard=True)


def yes_no():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Да")), KeyboardButton(text=("Нет")))
    return builder.as_markup(resize_keyboard=True)


def get_numbers(count: int, add_exit: bool = False):
    builder = ReplyKeyboardBuilder()
    builder.add(*[KeyboardButton(text=f"{x + 1}") for x in range(count)])
    if add_exit:
        builder.add(KeyboardButton(text=("Выйти")))
    return builder.as_markup(resize_keyboard=True)


def remove():
    return ReplyKeyboardRemove()


def save_current():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Оставить текущее")))
    return builder.as_markup(resize_keyboard=True)
