from aiogram import types, F
from asgiref.sync import sync_to_async

from modul.clientbot.handlers.leomatch.keyboards import reply_kb
from modul.clientbot.utils.functs import return_main
from modul.clientbot.handlers.leomatch.shortcuts import exists_leo, get_leo
from modul.clientbot.handlers.leomatch.handlers.shorts import manage
from modul.models import LeoMatchModel
from modul.loader import client_bot_router
from aiogram.fsm.context import FSMContext
from modul.clientbot.handlers.leomatch.data.state import LeomatchRegistration
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from modul.models import UserTG


def init_client_dv():
    @client_bot_router.message(F.text == "🫰 Знакомства")
    async def bot_start(message: types.Message, state: FSMContext):
        has_user = await exists_leo(message.from_user.id)
        if not has_user:
            await message.answer(
                ("Добро пожаловать! Я - бот для знакомств. Я помогу тебе найти свою вторую половинку. "),
                reply_markup=reply_kb.begin_registration())
            await state.set_state(LeomatchRegistration.BEGIN)
        else:
            account = await get_leo(message.from_user.id)
            if account.blocked:
                await message.answer(("Ваш аккаунт заблокирован"))
                return
            await manage(message, state)
    @client_bot_router.message(F.text == ("Я не хочу никого искать"), LeomatchRegistration.BEGIN)
    async def bot_start(message: types.Message, state: FSMContext):
        await return_main(message, state)
