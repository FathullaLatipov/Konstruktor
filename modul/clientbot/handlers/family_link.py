from aiogram import Bot, html, flags
from aiogram.exceptions import TelegramBadRequest, TelegramUnauthorizedError
from aiogram.utils.token import TokenValidationError
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from tortoise.exceptions import IntegrityError
from clientbot import shortcuts
from clientbot.keyboards.reply_kb import cancel, main_menu, confirm
from general.shortcuts import save_user
from general.views import get_cabinet_text
from mainbot.data.states import ChildPayout
from loader import client_bot_router
from aiogram.dispatcher.fsm.context import FSMContext
from config import settings
from loader import bot_session
from aiogram.types import Message, CallbackQuery
from mainbot import shortcuts as main_shortcuts
from general import bot_manage, payouts
from general.inline_kbrd import my_cabinet, percents


# @client_bot_router.message(text=_('create_bot'))
@client_bot_router.message(text=__("🤖 Создать своего бота"))
@flags.rate_limit(key="partners")
async def partners(message: Message):
    user = await main_shortcuts.get_user(message.from_user.id)
    if not user:
        await save_user(message.from_user)
    await bot_manage.select_module(message, "child")
        
        
# @client_bot_router.message(text=_('my_cabinet'))
@client_bot_router.message(text=__("📬 Мой кабинет"))
@flags.rate_limit(key="user_cabinet")
async def user_cabinet(message: Message):
    text = await get_cabinet_text(message.from_user.id)
    await message.answer(text, reply_markup=my_cabinet())

@client_bot_router.callback_query(text="payout")
@flags.rate_limit(key="payout")
async def payout(query: CallbackQuery, state: FSMContext):
    await payouts.payout(query.message)
    await state.set_state(ChildPayout.method)


@client_bot_router.message(state=ChildPayout.method)
@flags.rate_limit(key="choose-fowpay-method")
async def choose_method(message: Message, state: FSMContext):
    try:
        text, method_name, method_code, payment_min = await payouts.choose_method(message.text, message.from_user.id)
        await state.set_state(ChildPayout.amount)
        await state.update_data(method=method_name, method_code=method_code, comm=payment_min)
        await message.answer(text, reply_markup=cancel())
    except Exception as e:
        await message.answer(str(e))

@client_bot_router.message(state=ChildPayout.amount)
@flags.rate_limit(key="payout-amount")
async def withdraw_amount(message: Message, state: FSMContext):
    try:
        data = await state.get_data()
        comm, name = data['comm'], data["method"]
        text, amount = await payouts.withdraw_amount(message.text, message.from_user.id, name, comm)
        await state.update_data(amount=amount)
        await message.answer(text, )
        await state.set_state(ChildPayout.wallet)
    except Exception as e:
        await message.answer(str(e))


@client_bot_router.message(state=ChildPayout.wallet)
@flags.rate_limit(key="payout-wallet")
async def withdraw(message: Message, state: FSMContext):
    wallet = message.text.replace(" ", "")
    data = await state.get_data()
    amount = data['amount']
    method = data['method']
    await state.update_data(wallet=wallet)
    await message.answer(payouts.WITHDRAW.format(
        amount=amount,
        wallet=wallet,
        method_name=method
    ), reply_markup=confirm())
    await state.set_state(ChildPayout.confirmation)


@client_bot_router.message(state=ChildPayout.confirmation)
@flags.rate_limit(key="withdraw_confirmation")
async def withdraw_confirmation(message: Message, state: FSMContext):
    if message.text in ["Перевести", "Да, продолжить"]:
        data = await state.get_data()
        amount = data.get('amount')
        wallet = data.get('wallet')
        method_code = data.get('method_code')            
        text = await payouts.withdraw_confirmation(amount, wallet, method_code, message.from_user.id)
        await message.answer(text, reply_markup=await main_menu(message.from_user.id))
    else:
        await state.clear()
        await message.answer(_("Отменено"), reply_markup=await main_menu(message.from_user.id))