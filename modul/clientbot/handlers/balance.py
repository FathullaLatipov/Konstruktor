# Balance
from contextlib import suppress
from datetime import datetime
from uuid import uuid4

from aiogram import types, Bot, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from clientbot import shortcuts
from clientbot.data.callback_datas import (
    BalanceCallbackData
)
from clientbot.data.states import PromocodeState, RefillAmount
from clientbot.keyboards import inline_kb, reply_kb
from clientbot.keyboards.functs import get_cryptomus_services
from db.models import BillTypeEnum, ClientBotUser, PromocodeDoneModel, PromocodesModel
from clientbot.handlers.chatgpt.keyboards.inline_kbrds import get_kbrd_ai_balance
from utils.aaio.AAIO import AAIO
from loader import client_bot_router, settings, main_bot
from utils.cryptomus.cryptomus import Cryptomus
from utils.cryptomus.models import Currency


@client_bot_router.callback_query(BalanceCallbackData.filter())
@flags.rate_limit(key="balance-cd")
async def balance_cd(query: types.CallbackQuery, state: FSMContext, callback_data: BalanceCallbackData):
    if callback_data.action == "history":
        await query.answer(_("Скоро..."), show_alert=True)
    elif callback_data.action == "refill":
        with suppress(TelegramBadRequest):
            await query.message.edit_reply_markup()
        await show_panel_input_amount(query.message, state)
    elif callback_data.action == "promocode":
        await query.message.delete()
        await query.message.answer(_("Введите промокод"), reply_markup=reply_kb.cancel())
        await state.set_state(PromocodeState.input_code)


@client_bot_router.message(state=PromocodeState.input_code)
async def input_promocode(message: Message, state: FSMContext):
    if message.text == _("Отмена"):
        await message.answer(_("Отменено"), reply_markup=await reply_kb.main_menu(message.from_user.id))
        await state.clear()
        return
    bot = await shortcuts.get_bot()
    promocode = await PromocodesModel.filter(code=message.text, admin=bot.owner).first()
    if not promocode:
        await message.answer(_("Промокод не найден"))
        return
    if promocode.used_count >= promocode.count:
        await message.answer(_("Промокод уже использован максимальное количество раз"))
        return
    done = await PromocodeDoneModel.filter(promocode=promocode, user__uid=message.from_user.id).first()
    if done:
        await message.answer(_("Вы уже использовали этот промокод"))
        return
    client = await shortcuts.get_user(message.from_user.id)
    await PromocodeDoneModel(promocode=promocode, user=client, date=datetime.now().date()).save()
    promocode.used_count += 1
    promocode.last_used_at = datetime.now().date()
    await promocode.save()
    cleint = await shortcuts.get_user(message.from_user.id)
    cleint.balance += promocode.sum
    await cleint.save()
    await message.answer(_("Баланс пополнен на {promocode_sum} рублей").format(promocode_sum=promocode.sum))
    await message.answer(_("Выберите действие"), reply_markup=await reply_kb.main_menu(message.from_user.id))
    text = _(
        "Пользователь {full_name}(@{username}, {user_id}) активировал промокод {promocode_code} на сумму {promocode_sum} рублей").format(
        full_name=message.from_user.full_name, username=message.from_user.username, user_id=message.from_user.id,
        promocode_code=promocode.code, promocode_sum=promocode.sum)
    if bot.parent:
        _bot = Bot(token=bot.token)
        admin_client = await ClientBotUser.filter(uid=bot.owner.uid).first()
        uid = admin_client.uid
    else:
        _bot = main_bot
        uid = bot.owner.uid
    await _bot.send_message(uid, text)


async def show_panel_input_amount(message: Message, state: FSMContext) -> None:
    """Панель для ввода сумы пополнения"""
    text = (_("Вы можете пополнить сумму ниже через кнопку, либо введите желаемую сумму:\n\n"
              "Пример: 100\n"))
    await message.answer(
        text,
        reply_markup=reply_kb.amount_kb()
    )
    await state.set_state(RefillAmount.amount)


@client_bot_router.message(state=RefillAmount.amount)
async def refill_amount(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        await message.answer(_("Сумма должна быть в цифрах"))
        return
    try:
        amount = float(message.text)
    except ValueError:
        await message.answer(_("Баланс пользователя должен быть в цифрах"))
    else:
        text = (
            _("Текущая сумма пополнения: {amount}\n\n"
              "Выберите один из способов пополнения\n").format(amount=amount)
        )
        await message.answer(text, reply_markup=await reply_kb.refill_balance_methods(True))
        await state.set_state(RefillAmount.method)
        await state.update_data(amount=amount, type="balance")


@client_bot_router.message(state=RefillAmount.method)
@flags.rate_limit(key="refill-amount-state")
async def refill_method(message: types.Message, state: FSMContext, bot: Bot):
    method = message.text
    if method == _("Карта UZCARD"):
        await state.clear()
        await message.answer(_("""
🐥 Пополнение с помощью Uzcard 

▫️ Номер карты: <code>8600490446204844</code>


После отправки денег, отправьте чек оплаты, ссылку на бота и свой ID(можно получить нажав на кнопку баланс в боте): @SanjarSupport


Начисление денег происходит вручную в течении 24 часов                                     
                                """), parse_mode="html", reply_markup=await reply_kb.main_menu(message.from_user.id))
        return
    elif method == _("Криптовалюты"):
        await message.answer(_("Выберите криптовалюту"), reply_markup=reply_kb.refill_crypto_balance_methods())
        await state.set_state(RefillAmount.crypto)
        return
    data = await state.get_data()
    amount = data['amount']
    try:
        a = float(amount)
    except:
        await message.answer(_("Платежка отменена: сумма записалась как {amount}").format(amount=amount))
        await state.clear()
        return
    aaio = AAIO(settings.AAIO_ID, settings.AAIO_SECRET_1, settings.AAIO_SECRET_2, settings.AAIO_KEY)
    methods = aaio.get_payment_methods()
    method = methods.get_method(message.text)
    if method:
        data = await state.get_data()
        gt = data.get('gt')
        bot_ = await shortcuts.get_bot()
        if a >= method.min.RUB and a <= method.max.RUB:
            amount = float(data['amount'])
            user = await shortcuts.get_user(message.from_user.id)
            order_id = str(uuid4())
            await bot.send_chat_action(message.from_user.id, "typing")
            balance_type = data.get("type")
            if balance_type == "balance":
                type = BillTypeEnum.PROMOTION
            elif balance_type == "gpt":
                type = BillTypeEnum.AI
            elif balance_type == "anon":
                type = BillTypeEnum.ANON_VIP
            count_stars = 0 if not gt else gt
            await shortcuts.create_bill(user, order_id, amount, type, count_stars)
            url = aaio.payment(amount, order_id)
            await message.answer(
                text=_("🔗 Перейдите по ссылке на кнопке и оплатите ваш тариф.\r\n"),
                reply_markup=inline_kb.payment(
                    url=url, order_id=order_id
                )
            )
            await state.clear()
        else:
            if not gt:
                await message.answer(
                    _("Сумма должна быть больше {method_min_rub} рублей и меньше {method_max_rub} рублей").format(
                        method_min_rub=method.min.RUB, method_max_rub=method.max.RUB))
                await show_panel_input_amount(message, state)
            else:
                await message.answer(
                    _("Минимальная сумма пополнения {method_min_rub} рублей, выберите тариф побольше или же попробуйте оплатить через другой метод").format(
                        method_min_rub=method.min.RUB),
                    reply_markup=await get_kbrd_ai_balance(message.from_user.id, bot_.percent))
        return
    else:
        await message.answer(_("Неверный способ. Выберите из списка ниже"))
        return


@client_bot_router.message(state=RefillAmount.crypto)
@flags.rate_limit(key="refill-amount-state")
async def refill_method(message: types.Message, state: FSMContext, bot: Bot):
    method = message.text
    for service in get_cryptomus_services():
        if method == f"{service.network} {service.currency}":
            min_sum = float(service.limit.min_amount)
            max_sum = float(service.limit.max_amount)
            data = await state.get_data()
            gt = data.get('gt')
            amount = data['amount']
            a = float(amount)
            if a >= min_sum and a <= max_sum:
                user = await shortcuts.get_user(message.from_user.id)
                order_id = str(uuid4())
                bot_obj = await shortcuts.get_bot()
                await bot.send_chat_action(message.from_user.id, "typing")
                count_stars = 0 if not gt else gt
                await shortcuts.create_bill(user, order_id, amount, BillTypeEnum.PROMOTION, 0)
                crypto = Cryptomus(settings.CRYPTOMUS_MERCHANT, settings.CRYPTOMUS_APPKEY)

                courency_result = crypto.currency(service.currency)
                amount_cur = 0
                if len(courency_result.result) == 0:
                    await message.answer(_("Не удалось загрузить валюты. Повторите позже"))
                    await state.clear()
                for curency in courency_result.result:
                    curency: Currency = curency
                    if curency.to == "RUB":
                        amount_cur = float(curency.course)
                        break
                if amount_cur == 0:
                    await message.answer(_("Не удалось загрузить валюты. Повторите позже"))
                    await state.clear()
                else:
                    amount = float(amount) / float(amount_cur)

                result = crypto.add_payment(str(amount), service.currency, order_id, network=service.network,
                                            url_callback="https://dosimple.io/bot/api/cryptomus/payment")
                if isinstance(result, str):
                    courency_result = crypto.currency(service.currency)
                    amount = 0
                    if len(courency_result.result) == 0:
                        await message.answer(_("Не удалось загрузить валюты. Повторите позже"))
                        await state.clear()
                        return
                    for curency in courency_result.result:
                        curency: Currency = curency
                        if curency.to == "RUB":
                            amount = float(curency.course)
                            break
                    await message.answer(
                        _("Сумма должна быть больше {min_sum} рублей и меньше {max_sum} рублей").format(
                            min_sum=min_sum * amount, max_sum=max_sum * amount))
                    await show_panel_input_amount(message, state)
                    return
                else:
                    if isinstance(result, dict):
                        url = result['url']
                    else:
                        url = result.url
                    await message.answer(
                        text=_("🔗 Перейдите по ссылке на кнопке и оплатите ваш тариф.\r\n")
                        , reply_markup=inline_kb.payment(
                            url=url, order_id=order_id
                        )
                    )
                await state.clear()
            else:
                await message.answer(
                    _("Сумма должна быть больше {min_sum} рублей и меньше {max_sum} рублей").format(min_sum=min_sum,
                                                                                                    max_sum=max_sum))
                await show_panel_input_amount(message, state)
            return
    else:
        await message.answer(_("Неверный способ. Выберите из списка ниже"))
        return
