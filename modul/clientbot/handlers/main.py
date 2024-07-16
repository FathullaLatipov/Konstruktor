from contextlib import suppress
from datetime import datetime, timedelta
import math
from aiogram import Bot, html, types, flags
from aiogram.filters import CommandObject, CommandStart
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest, TelegramNotFound
from aiogram.types import Message
from aiogram.types import BotCommand
from modul.clientbot import shortcuts, strings
from modul.clientbot.data.callback_datas import MainMenuCallbackData
from modul.clientbot.keyboards import inline_kb, reply_kb
from modul.clientbot.utils.exceptions import UserNotFound
# from modul.clientbot.utils.order import paginate_orders
from modul import models
from modul.clientbot.data.states import Download
# from modul.clientbot.handlers.anon.handlers.main import cabinet_text

from modul.loader import client_bot_router, bot_session
from aiogram.fsm.context import FSMContext
import sys
import traceback

from django.db import transaction
from asgiref.sync import sync_to_async
from aiogram import Bot

from modul.models import UserTG


@sync_to_async
@transaction.atomic
async def save_user(u, bot: Bot, inviter=None):
    bot = await sync_to_async(models.Bot.objects.select_related("owner").filter(token=bot.token).first)()
    user = await sync_to_async(models.UserTG.objects.filter(uid=u.id).first)()
    current_ai_limit = 12
    if not user:
        user = await sync_to_async(models.UserTG.objects.create)(
            uid=u.id,
            username=u.username,
            first_name=u.first_name,
            last_name=u.last_name,
        )
    else:
        current_ai_limit = 0

    client_user = await sync_to_async(models.ClientBotUser.objects.filter(uid=u.id, bot=bot).first)()
    if client_user:
        return client_user

    client_user = await sync_to_async(models.ClientBotUser.objects.create)(
        uid=u.id,
        user=user,
        bot=bot,
        inviter=inviter,
        current_ai_limit=current_ai_limit
    )
    return client_user


async def start(message: types.Message, state: FSMContext, bot: Bot):
    bot_db = await shortcuts.get_bot(bot)
    uid = message.from_user.id
    text = ("Добро пожаловать, {hello}").format(hello=html.quote(message.from_user.full_name))
    kwargs = {}
    if shortcuts.have_one_module(bot_db, "download"):
        text = ("🤖 Привет, {full_name}! Я бот-загрузчик.\r\n\r\n" \
                "Я могу скачать фото/видео/аудио/файлы/архивы с *Youtube, Instagram, TikTok, Facebook, SoundCloud, Vimeo, Вконтакте, Twitter и 1000+ аудио/видео/файловых хостингов*. Просто пришли мне URL на публикацию с медиа или прямую ссылку на файл.").format(
            full_name=message.from_user.full_name)
        await state.set_state(Download.download)
        kwargs['parse_mode'] = "Markdown"
    # elif shortcuts.have_one_module(bot_db, "anon"):
    #     # text = cabinet_text()
    #     kwargs['reply_markup'] = await reply_kb.main_menu(uid)
    else:
        kwargs['reply_markup'] = await reply_kb.main_menu(uid, bot)
    await message.answer(text, **kwargs)


@sync_to_async
def get_user(uid: int, username: str, first_name: str = None, last_name: str = None):
    user = UserTG.objects.get_or_create(uid=uid, username=username, first_name=first_name, last_name=last_name)
    return user


def init_client_bot_handlers():
    @client_bot_router.message(CommandStart())
    @flags.rate_limit(key="on_start")
    async def on_start(message: Message, command: CommandObject, state: FSMContext, bot: Bot):
        info = await get_user(uid=message.from_user.id, username=message.from_user.username,
                              first_name=message.from_user.first_name if message.from_user.first_name else None,
                              last_name=message.from_user.last_name if message.from_user.last_name else None)
        await state.clear()
        commands = await bot.get_my_commands()
        bot_commands = [
            BotCommand(command="/start", description="Меню"),
        ]
        if commands != bot_commands:
            await bot.set_my_commands(bot_commands)
        referral = command.args
        uid = message.from_user.id
        user = await shortcuts.get_user(uid, bot)

        if not user:
            if referral and referral.isdigit():
                inviter = await shortcuts.get_user(int(referral))
                if inviter:
                    await shortcuts.increase_referral(inviter)
                    with suppress(TelegramForbiddenError):
                        user_link = html.link('реферал', f'tg://user?id={uid}')
                        await bot.send_message(
                            chat_id=referral,
                            text=('new_referral').format(
                                user_link=user_link,
                            )
                        )
            else:
                inviter = None
            await save_user(u=message.from_user, inviter=inviter, bot=bot)
        await start(message, state, bot)


# @client_bot_router.message(text=__("🌍 Поменять язык"))
# async def change_language(message: types.Message):
#     user = await shortcuts.get_base_user(message.from_user.id)
#     user.language_code = 'ru' if user.language_code == 'en' else 'en'
#     await user.save()
#     await message.answer(
#         _("Вы поменяли язык на {lang}").format(lang=("Русский" if user.language_code == 'ru' else "English")))


# @client_bot_router.message(text=__("💰 Баланс"))
# @flags.rate_limit(key="balance")
# async def balance_menu(message: Message):
#     user = await shortcuts.get_user(message.from_user.id)
#     await message.answer(_("💲 Ваш баланс: {balance}₽\n🏷 Ваш id: <code>{user_id}</code>").format(balance=user.balance,
#                                                                                                 user_id=message.from_user.id),
#                          reply_markup=inline_kb.balance_menu())


# @client_bot_router.message(text=__("✨ Список наших ботов"))
# @flags.rate_limit(key="our-bots")
# async def balance_menu(message: Message):
#     bot_db = await shortcuts.get_bot()
#     owner = await bot_db.owner
#     bots = await models.Bot.filter(owner=owner, unauthorized=False)
#     text = _("✨ Список наших ботов:\n")
#     for bot in bots:
#         try:
#             b = Bot(bot.token, bot_session)
#             info = await b.get_me()
#             text += f"🤖 @{bot.username} - {info.full_name}\n"
#         except Exception as e:
#             pass
#     await message.answer(text)


# @client_bot_router.message(text=__("📋 Мои заказы"))
# @flags.rate_limit(key="user_orders")
# async def user_orders(message: Message):
#     await Bot.get_current().send_chat_action(message.from_user.id, "typing")
#     try:
#         text, reply_markup = await paginate_orders(message.from_user.id)
#     except UserNotFound:
#         await save_user(message.from_user)
#         text, reply_markup = await paginate_orders(message.from_user.id)
#     if text:
#         await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
#     else:
#         await message.answer(_("⛔️ У вас еще нет заказов"))

#
# @client_bot_router.message(text=__("👤 Реферальная система"))
# @flags.rate_limit(key="partners")
# async def partners(message: Message):
#     username = (await Bot.get_current().get_me()).username
#     uid = message.from_user.id
#     await message.answer(
#         text=strings.PARTNERS_INFO.format(
#             await shortcuts.referral_count(uid),
#             await shortcuts.referral_balance(uid),
#             username,
#             uid
#         ),
#         reply_markup=inline_kb.transfer_keyboard()
#     )


# @client_bot_router.message(text=__("⭐️ Социальные сети"))
# @flags.rate_limit(key='social_networks')
# async def social_networks(message: Message):
#     await message.answer(
#         text=strings.CHOOSE_SOCIAL,
#         reply_markup=await inline_kb.social_networks()
#     )


# @client_bot_router.message(text=__("👮‍♂️ Связаться с администратором"))
# @client_bot_router.message(text=__("ℹ️ Информация"))
# @flags.rate_limit(key="information")
# async def information_menu(message: types.Message, bot: Bot):
#     bot_obj = await shortcuts.get_bot()
#     owner: models.MainBotUser = bot_obj.owner
#     try:
#         await message.answer(strings.INFO.format(username=f"@{bot_obj.username}"), reply_markup=inline_kb.info_menu(
#             support=bot_obj.support or owner.uid,
#             channel_link=bot_obj.news_channel
#         ))
#     except TelegramBadRequest as e:
#         if "BUTTON_USER_INVALID" in e.message:
#             await bot.send_message(owner.uid, _("⚠️ Измените ид поддержки бота. Текущий недействителен."))
#         try:
#             await message.answer(strings.INFO.format(username=f"@{bot_obj.username}"), reply_markup=inline_kb.info_menu(
#                 support=owner.uid,
#                 channel_link=bot_obj.news_channel
#             ))
#         except TelegramBadRequest:
#             await bot.send_message(owner.uid, _("Неправильный хост URL. Пожалуйста, измените ссылку на канал"))
#             await message.answer(strings.INFO.format(username=f"@{bot_obj.username}"), reply_markup=inline_kb.info_menu(
#                 support=owner.uid,
#             ))


@client_bot_router.callback_query(MainMenuCallbackData.filter())
@flags.rate_limit(key="back-to-main-menu", rate=2)
async def main_menu(query: types.CallbackQuery, callback_data: MainMenuCallbackData):
    if callback_data.action is None:
        try:
            await query.message.delete()
        except (TelegramBadRequest, TelegramNotFound):
            await query.message.edit_reply_markup()
        finally:
            await query.message.answer(strings.MAIN_MENU.format(query.from_user.first_name),
                                       reply_markup=await reply_kb.main_menu(query.message.from_user.id))
