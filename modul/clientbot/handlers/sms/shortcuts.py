from datetime import datetime
from aiogram import Bot
from clientbot.shortcuts import get_user
from config import settings
from db import models
from loader import bot_session, main_bot
from mainbot.shortcuts import update_user_balance as admin_change_balance
from dataclasses import dataclass
from clientbot.shortcuts import update_user_balance as client_change_balance
from onlinesimru import NumbersService
from aiogram.utils.i18n import gettext as _


@dataclass
class OrderNumberResponse:
    order_id: int
    phone: str


async def create_order(user: models.ClientBotUser, order_id: int, profit: float, bot_admin_profit: float,
                       country_code: str, product: str,
                       phone: str, price: str, msg_id: int):
    order = await models.SMSOrder.create(
        order_id=order_id, user=user, profit=profit,
        bot_admin_profit=bot_admin_profit, country_code=country_code, product=product, phone=phone, price=price,
        msg_id=msg_id
    )
    return order


def get_countries(page: int = 1, country_code: str = None, search_key: str = None):
    limit = 15
    offset = limit * (page - 1)
    numbers = NumbersService(settings.SIM_ONLINE, lang='ru')
    tariffs = numbers.tariffs()['countries']
    countries = [{
        'id': value['code'],
        'name': value['name'],
    } for key, value in tariffs.items()]
    return countries[offset:limit * page], len(countries)


def get_contry(country_code: int):
    numbers = NumbersService(settings.SIM_ONLINE, lang='ru')
    return numbers.tariffs()['countries'][f'_{country_code}']['name']


def get_price_from_online_sim(country: str, service: str) -> float:
    numbers = NumbersService(settings.SIM_ONLINE)
    tariffs = numbers.tariffsOne(country)
    for key, value in tariffs['services'].items():
        if value['slug'] == service:
            return float(value['price']) * settings.DOLLAR_CURRENCY
    raise ValueError("Service not found")


async def get_order(order_id: int):
    return await models.SMSOrder.get_or_none(order_id=order_id)


async def get_products(country: str, page: int = 1, product: str = None, search_key: str = None):
    limit = 15
    offset = limit * (page - 1)
    numbers = NumbersService(settings.SIM_ONLINE)
    tzid = numbers.tariffsOne(country)
    products: dict = tzid["services"]
    products = [{key: value} for key, value in products.items()]
    # if product:
    #     for product_ in products:
    #         key = list(product_.keys())[0]
    #         if product == key:
    #             return product_[key]
    # elif search_key:
    #     keys = []
    #     for product_ in products:
    #         keys.append(list(product_.keys())[0])
    #     return process.extractBests(search_key, keys, scorer=fuzz.WRatio, score_cutoff=70)
    return products[offset:limit * page], len(products)


def get_product(products: list, service: str) -> dict:
    """"""
    for product_dict in products:
        product_dict: dict = product_dict
        for key, value in product_dict.items():
            if key == service:
                return value
    return {}


async def change_order_phone(order_id: int, new_order_id: int, new_phone: str):
    order = await get_order(order_id)
    order.order_id = new_order_id
    order.phone = new_phone
    await order.save()


async def get_phone(user_id: int, country: str, product: str, ):
    numbers = NumbersService(settings.SIM_ONLINE)
    limit = 0
    while True:
        if limit == 15:
            break
        try:
            response = numbers.get(product, country, number=True)
        except Exception as e:
            await main_bot.send_message(settings.ADMIN, _("Ошибка при получении номера: {e}").format(e=e))
            raise Exception(f"Ошибка при получении номера, попробуйте позже {e}")
        order_id = response['tzid']
        phone = response['number']
        if not await has_phone_in_block(user_id, phone, order_id):
            return OrderNumberResponse(order_id, phone)
        else:
            try:
                close_order_sim(order_id)
            except:
                pass
        limit += 1
    return None


def close_order_sim(order_id: int):
    try:
        numbers = NumbersService(settings.SIM_ONLINE)
        numbers.close(order_id)
    except Exception as e:
        raise Exception('Отменить можно только после 2 минут ожидания')


async def finish_order(order_id: int):
    order = await get_order(order_id)
    if order.receive_status != "received":
        order.receive_status = "received"
        await order.save()
        user: models.ClientBotUser = await order.user
        bot: models.Bot = await user.bot
        owner: models.MainBotUser = await bot.owner
        async with Bot(bot.token, session=bot_session).context(auto_close=False) as b:
            b: Bot = b
            await client_change_balance(owner, order.profit)
        try:
            close_order_sim(order_id)
        except:
            pass


async def cancel_order_and_finish(order_id: int):
    order = await get_order(order_id)
    if order.receive_status not in ['received', 'canceled']:
        close_order_sim(order_id)
        user: models.ClientBotUser = await order.user
        await client_change_balance(user.uid, order.price, "charge", order.product)
        order.receive_status = "canceled"
        await order.save()
        return True
    return False


async def add_phone_to_ban(user_uid: int, phone: str, service: str):
    user = await get_user(user_uid)
    await models.SMSBanModel.create(
        user=user,
        service=service,
        phone=phone
    )


async def has_phone_in_block(user_uid: int, phone: str, service: str):
    user = await get_user(user_uid)
    ban = await models.SMSBanModel.filter(user=user, phone=phone, service=service)
    return len(ban) > 0


async def get_order_history(uid: int, page: int = 1):
    offset = settings.HISTORY_LIMIT * (page - 1)
    user = await get_user(uid)
    queryset = models.SMSOrder.filter(user=user, receive_status="received")
    return await queryset.limit(settings.HISTORY_LIMIT).offset(offset).order_by("-id"), await queryset.count()


async def print_order_history(orders: list["models.SMSOrder"]):
    text = []
    for order in orders:
        text.append(
            _("🧾 Заказ №: {order_id}\n"
              "💴 Цена: {price:.2f}₽\n"
              "📱 Сервис: <code>{product}</code>\n"
              "📱 Номер: <code>{phone}</code>\n"
              "📊 Код: {receive_code}\n").format(order_id=order.order_id, price=order.price, product=order.product,
                                                phone=order.price, code=order.receive_code)
        )
    return "\n".join(text) if text else None


async def delete_order(order_id: int):
    order = await get_order(order_id)
    if order:
        await order.delete()
