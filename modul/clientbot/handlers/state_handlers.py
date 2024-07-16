from aiogram import types
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _

from clientbot.data.schemas import Service
from clientbot.data.states import Order, Transfer, Broadcast
from clientbot import shortcuts, strings
from clientbot.handlers.chatgpt.handlers.main import main_cabinet
from clientbot.handlers.main import start
from clientbot.keyboards import reply_kb, inline_kb
from clientbot.utils.exceptions import InvalidQuantity
from clientbot.utils.order import perform_order
from clientbot.utils.smm import get_service
from loader import client_bot_router


async def confirmation(message: types.Message, state: FSMContext, service: Service):
    data = await state.get_data()
    if 'quantity' in data or "_quantity" in data:
        quantity = data.get('_quantity', None)
        if quantity is None:
            quantity = data.get('quantity')
        service_price = shortcuts.calculate_service_price(service, quantity)
    else:
        service_price = float(service.rate)
    user_balance = await shortcuts.user_balance(message.from_user.id)
    price, profit, bot_percent = await shortcuts.calculate_price(message.from_user.id, service_price)
    if user_balance < price:
        await message.answer(_("⛔️ У вас недостаточно средств, цена услуги: {price}₽").format(price=price),
                             reply_markup=inline_kb.add_balance())
        await start(message, state)
        await state.clear()
        return
    service_steps = strings.SERVICE_STEPS[service.type]
    additional = '\n'.join(
        map(lambda item: f"{service_steps[item]['ru']}: {data.get(item, '')}", list(service_steps.keys())))
    if additional:
        additional += "\n"
    text = strings.NEW_ORDER_INFO.format(link=data.get('link'), price=price, additional=additional)
    await message.answer(text, reply_markup=reply_kb.confirm(), disable_web_page_preview=True)
    await state.set_state(Order.confirm)


async def next_state(message: types.Message, state: FSMContext, service: Service):
    data = await state.get_data()
    service_steps = strings.SERVICE_STEPS[service.type]
    previous_step_idx = data.get('_current_step', None)
    if previous_step_idx is not None:
        try:
            previous_step_key = tuple(service_steps.keys())[previous_step_idx]
            previous_step = service_steps[previous_step_key]
            if message.text != strings.SKIP:
                if previous_step_key == "quantity":
                    try:
                        value = int(message.text)
                        if not int(service.min) <= value <= int(service.max):
                            raise InvalidQuantity
                    except ValueError:
                        raise InvalidQuantity
                elif previous_step.get("type", "") == "line":
                    v = message.text.splitlines()
                    if service.type == strings.ServiceType.CUSTOM_COMMENTS:
                        if not int(service.min) <= len(v) <= int(service.max):
                            raise InvalidQuantity
                    value = "\n".join(v)
                    await state.update_data(_quantity=len(v))
                elif previous_step_key in ["min", "max"]:
                    try:
                        value = int(message.text)
                        if (previous_step_key == "min" and value < int(service.min)) or (
                                previous_step_key == "max" and value > int(service.max)):
                            raise InvalidQuantity
                        else:
                            await state.update_data(_quantity=value)
                    except ValueError:
                        raise InvalidQuantity
                elif service.type == strings.ServiceType.DEFAULT and previous_step_key == "interval":
                    try:
                        value = int(message.text)
                        if value < 1:
                            raise ValueError
                    except ValueError:
                        await message.answer(_("Интервал введен неправильно. Оно должно быть больше 0"))
                        return
                else:
                    value = message.text
                await state.update_data({previous_step_key: value})
            else:
                if not previous_step['optional']:
                    await message.answer(_("Вы не можете пропустить этот шаг"))
                    return
        except InvalidQuantity:
            await message.answer(strings.QUANTITY_ERROR.format(min=int(service.min), max=int(service.max)),
                                 reply_markup=reply_kb.cancel())
            return
    if previous_step_idx is None:
        idx = 0
    else:
        if previous_step_idx + 1 < len(service_steps.keys()):
            idx = previous_step_idx + 1
        else:
            idx = -1
    if idx == -1:
        await confirmation(message, state, service)
    else:
        next_step_key = tuple(service_steps.keys())[idx]
        next_step = service_steps[next_step_key]
        if next_step_key == "quantity":
            text = next_step['description'].format(min=int(service.min), max=int(service.max))
        else:
            text = next_step['description']
        markup = reply_kb.cancel_or_skip() if next_step['optional'] else reply_kb.cancel()
        await message.answer(text, reply_markup=markup)
        await state.update_data(_current_step=idx)


@client_bot_router.message(Order(), content_types=types.ContentType.TEXT)
async def order_service(message: types.Message, state: FSMContext):
    data = await state.get_data()
    state_ = await state.get_state()
    service = await get_service(data.get("_service"))
    service_steps = strings.SERVICE_STEPS[service.type]
    if state_ == Order.link.state:
        await state.update_data(link=message.text)
        if service_steps:
            await state.set_state(Order.current_step)
            await next_state(message, state, service)
        else:
            await confirmation(message, state, service)
    elif state_ == Order.current_step.state:
        await next_state(message, state, service)
    elif state_ == Order.confirm.state:
        try:
            if message.text == _("Да, продолжить"):
                await perform_order(message, state, service)
            else:
                await message.answer(_("Отменено"), reply_markup=await reply_kb.main_menu(message.from_user.id))
        finally:
            await state.clear()


# Broadcasting
@client_bot_router.message(state=Broadcast.message)
async def broadcast(message: types.Message, state: FSMContext):
    await message.answer(_("Сообщение готово к отправке."), reply_markup=await reply_kb.main_menu(message.from_user.id))
    await state.update_data(message=message.json(exclude_none=True))
    await state.set_state(Broadcast.confirmation)
    await message.answer(_("Начинать?"), reply_markup=inline_kb.broadcast_confirmation())


# Transfer
@client_bot_router.message(state=Transfer.amount)
async def transfer(message: types.Message, state: FSMContext):
    amount = message.text
    uid = message.from_user.id
    if not amount.isdigit() and float(amount) < 50:
        await message.answer(_("⛔️ Минимальная сумма снятия 50 рублей"))
        return
    amount = float(amount)
    if await shortcuts.referral_balance(uid) < amount:
        await message.answer(_("⛔️ Недостаточно средств для снятия такой суммы денег"))
        return
    await shortcuts.transfer_money(uid, amount)
    await message.answer(_("🥳 Успешно переведена сумма в размере <b><u>{amount} ₽</u></b> на ваш основной счет!").format(amount=amount),
                         reply_markup=await reply_kb.main_menu(message.from_user.id))
    await state.clear()
