from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, ReplyKeyboardMarkup
from asgiref.sync import sync_to_async

from modul.clientbot import strings
from modul.clientbot.shortcuts import get_current_bot, have_one_module
from modul.models import Bot
from aiogram import Bot as CBot
from modul.config import settings_conf

MUSIC_MENU_BUTTONS_TEXT = [
    ("🎙Лучшая музыка"),
    ("🎧Новые песни"),
    ("🔥Чарт Музыка"),
    ("🔍Поиск")
]

CHATGPT_BUTTONS_TEXT = [
    ("☁ Чат с GPT-4"),
    ("☁ Чат с GPT-3.5"),
    ("🎨 Генератор фото [DALL-E]"),
    ("🗣️Голосовой помощник"),
    ("🗨️ Текст в аудио"),
    ("🔉 Аудио в текст"),
    ("🎥 Транскрипция ютуб"),
    ("🔍 Гугл поиск"),
    ("🔋 Баланс"),
    ("ℹ️ Помощь"),
]

HOROSCOPE_BUTTONS_TEXT = [
    ("🔮 Гороскоп на каждый день"),
    ("🔮 Гороскоп на завтра"),
    ("🔮 Гороскоп на месяц"),
    ("🏵 Восточный гороскоп"),
    ("🎩 Профиль"),
]

ANON_MENU_BUTTONS_TEXT = [
    ("☕ Искать собеседника"),
    ("🍪 Профиль"),
    "⭐ VIP",
]


def cancel():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text=("Отмена")))
    return builder.as_markup(resize_keyboard=True)


def cancel_or_skip():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=("Отмена")),
        KeyboardButton(text=("Пропустить")),
        width=1
    )
    return builder.as_markup(resize_keyboard=True)


def yes_no():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=("Да")),
        KeyboardButton(text=("Нет")),
        width=2
    )
    return builder.as_markup(resize_keyboard=True)


def have_one_module(bot: CBot, module_name: str):
    modules = [
        "enable_promotion",
        "enable_music",
        "enable_download",
        "enable_leo",
        "enable_chatgpt",
        "enable_horoscope",
        "enable_anon",
        "enable_sms",
    ]
    if getattr(bot, f"enable_{module_name}"):
        return [getattr(bot, x) for x in modules].count(True) == 1
    return False


async def turn_bot_data(attr: str, bot: CBot):
    bot = await get_current_bot()
    setattr(bot, attr, not getattr(bot, attr))
    await bot.save()


@sync_to_async
def get_bot_owner(bot):
    return bot.owner

@sync_to_async
def owner_bots_filter(owner):
    return owner.bots.filter(owner=owner, unauthorized=False).count()


async def gen_buttons(current_bot: Bot, uid: int):
    btns = []
    owner = await get_bot_owner(current_bot)
    if current_bot.enable_promotion:
        btns.append(("⭐️ Социальные сети"))
        btns.append(("📋 Мои заказы"))
        btns.append(("💰 Баланс"))
        btns.append(("👤 Реферальная система"))
        btns.append(("🌍 Поменять язык"))
    if current_bot.enable_music:
        if have_one_module(current_bot, "music"):
            [btns.append(i) for i in MUSIC_MENU_BUTTONS_TEXT]
        else:
            btns.append(("🎧 Музыка"))
    if current_bot.enable_download:
        if not have_one_module(current_bot, "download"):
            btns.append(("🎥 Скачать видео"))
    if current_bot.enable_chatgpt:
        if have_one_module(current_bot, "chatgpt"):
            [btns.append(i) for i in CHATGPT_BUTTONS_TEXT]
        else:
            btns.append(("🌐 ИИ"))
    if current_bot.enable_leo:
        btns.append(("🫰 Знакомства"))
    if current_bot.enable_horoscope:
        if have_one_module(current_bot, "horoscope"):
            [btns.append(i) for i in HOROSCOPE_BUTTONS_TEXT]
        else:
            btns.append(("♈️ Гороскоп"))
    if current_bot.enable_promotion:
        btns.append(("ℹ️ Информация"))
    if current_bot.enable_anon:
        if have_one_module(current_bot, "anon"):
            [btns.append(i) for i in ANON_MENU_BUTTONS_TEXT]
        else:
            btns.append(("🥂 Анонимный чат"))
    if current_bot.enable_child_bot and owner.uid != uid:
        btns.append(("🤖 Создать своего бота"))
    if current_bot.parent is not None and owner.uid == uid:
        btns.append(("📬 Мой кабинет"))

    bots_count = await owner_bots_filter(owner)
    if bots_count > 1:
        btns.append(("✨ Список наших ботов"))
    return btns


async def gen_buttons_anon(current_bot: Bot, uid: int):
    btns = []
    owner = await current_bot.owner
    if current_bot.enable_anon:
        if have_one_module(current_bot, "anon"):
            [btns.append(i) for i in ANON_MENU_BUTTONS_TEXT]
        else:
            btns.append(("🥂 Анонимный чат"))
    if current_bot.enable_child_bot and owner.uid != uid:
        btns.append(("🤖 Создать своего бота"))
    if await current_bot.parent != None and owner.uid == uid:
        btns.append(("📬 Мой кабинет"))

    bots_count = await owner.bots.filter(owner=owner, unauthorized=False).count()
    if bots_count > 1:
        btns.append(("✨ Список наших ботов"))
    return btns


async def main_menu(uid: int, bot: CBot):
    builder = ReplyKeyboardBuilder()
    current_bot = await get_current_bot(bot)
    btns = await gen_buttons(current_bot, uid)
    builder.row(*[KeyboardButton(text=i) for i in btns], width=2)
    return builder.as_markup(resize_keyboard=True)


def confirm():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=("Да, продолжить")),
        KeyboardButton(text=("Отмена")),
        width=1
    )
    return builder.as_markup(resize_keyboard=True)


def amount_kb():
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=strings.CANCEL), width=1)
    builder.row(
        KeyboardButton(text="50"),
        KeyboardButton(text="100"),
        KeyboardButton(text="250"),
        KeyboardButton(text="500"),
        KeyboardButton(text="1000"),
        KeyboardButton(text="5000"),
        width=3
    )
    return builder.as_markup(resize_keyboard=True)


def withdraw_confirmation():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=("Перевести")),
        KeyboardButton(text=strings.CANCEL),
        width=1
    )
    return builder.as_markup(resize_keyboard=True)


async def download_main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=("Назад")),
        width=1
    )
    return builder.as_markup(resize_keyboard=True)


async def ai_main_menu():
    keyboard = ReplyKeyboardBuilder()
    keyboard.row(
        KeyboardButton(text=("Назад",)),
        width=1,
    )
    return keyboard.as_markup(resize_keyboard=True)
