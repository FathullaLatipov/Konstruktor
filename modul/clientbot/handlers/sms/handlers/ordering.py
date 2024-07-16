from contextlib import suppress
from datetime import datetime, timedelta

from aiogram import Bot, types, flags
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from clientbot.handlers.sms import shortcuts
from clientbot.handlers.sms.data.callback_data import (
    CountryCallbackData,
    OrderCallbackData,
    ProductCallbackData
)
from clientbot.handlers.sms.data.states import CountryState, ProductState
from clientbot.handlers.sms.keyboards import reply_kb
from clientbot.shortcuts import calculate_price, get_user, update_user_balance
from db import models
from loader import client_bot_router, bot_session, main_bot


@client_bot_router.callback_query(text="show_countries")
async def choose_country(query: types.CallbackQuery, state: FSMContext):
    await state.clear()
    markup = await reply_kb.countries_kb(page=1)
    with suppress(TelegramBadRequest):
        await query.message.edit_text(text=_("1. Выберете страну, номер телефона которой будет Вам выдан"),
                                      reply_markup=markup)


@client_bot_router.callback_query(CountryCallbackData.filter())
@flags.rate_limit(key="choose-country")
async def choose_country(query: types.CallbackQuery, callback_data: CountryCallbackData, state: FSMContext):
    if callback_data.action == "paginate":
        await state.clear()
        markup = await reply_kb.countries_kb(page=callback_data.page)
        with suppress(TelegramBadRequest):
            await query.message.edit_text(text=_("1. Выберете страну, номер телефона которой будет Вам выдан"),
                                          reply_markup=markup)
    elif callback_data.action == "page-list":
        markup = await reply_kb.countries_pages_kb(callback_data.page)
        await query.message.edit_text(
            _("📖 Пожалуйста, выберите страницу"),
            reply_markup=markup
        )
    elif callback_data.action == "retrieve" or callback_data.action == "view":
        country_name = shortcuts.get_contry(callback_data.country_code)
        markup = await reply_kb.products_kb(callback_data.country_code)
        try:
            await query.message.edit_text(
                _("🌍 Выбранная страна: {country_name}\n\n"
                  "2. Выберите оператора номера").format(country_name=country_name),
                reply_markup=markup
            )
        except:
            await query.message.answer(
                _("🌍 Выбранная страна: {country_name}\n\n"
                  "2. Выберите оператора номера").format(country_name=country_name),
                reply_markup=markup
            )
    await query.answer()


@client_bot_router.message(state=CountryState.search)
@flags.rate_limit(key="search_country")
async def search_country(message: types.Message, state: FSMContext):
    search_key = message.text
    countries = shortcuts.get_countries(search_key=search_key)
    markup = reply_kb.country_search_result(countries)
    await message.answer(text=_("🔍 Результаты поиска ({len_countries}):").format(len_countries=len(countries)),
                         reply_markup=markup)
    await state.clear()


@client_bot_router.callback_query(ProductCallbackData.filter())
@flags.rate_limit(key="product")
async def products_cd(query: types.CallbackQuery, callback_data: ProductCallbackData, state: FSMContext):
    country = shortcuts.get_contry(callback_data.country_code)
    match callback_data.action:
        case "paginate":
            await state.clear()
            markup = await reply_kb.products_kb(callback_data.country_code, page=callback_data.page)
            text = _("🌍 Выбранная страна: {country}\n"
                     "2. Выберите сервис, от которого вам необходимо принять СМС").format(country=country)
            with suppress(TelegramBadRequest):
                await query.message.edit_text(text, reply_markup=markup)
            await query.answer()
        case "return":
            await state.clear()
            markup = await reply_kb.countries_kb(page=callback_data.page)
            with suppress(TelegramBadRequest):
                await query.message.edit_text(text=_("1. Выберете страну, номер телефона которой будет Вам выдан"),
                                              reply_markup=markup)
        case "page-list":
            markup = await reply_kb.products_pages_kb(callback_data)
            await query.message.edit_text(
                _("📖 Пожалуйста, выберите страницу"),
                reply_markup=markup
            )
            await query.answer()
        case "search":
            text = _("🔍 Введите название сервиса для поиска. Например: telegram")
            markup = reply_kb.back_kb(ProductCallbackData(action="paginate", country_code=callback_data.country_code,
                                                          page=callback_data.page).pack())
            await query.message.edit_text(text, reply_markup=markup)
            await state.set_state(ProductState.search)
            await state.update_data(country_code=callback_data.country_code)
            await query.answer()
        case "retrieve":
            cost = shortcuts.get_price_from_online_sim(callback_data.country_code, callback_data.product)
            country_name = shortcuts.get_contry(callback_data.country_code)
            price, nothing, nothing = await calculate_price(query.from_user.id, cost)
            text = (_("▫️ Выбранный сервис: {product}\n"
                      "▫️ Выбранная страна: {country_name}\n\n"
                      "▫️ Цена: {price}₽").format(product=callback_data.product, country_name=country_name,
                                                  price=price))
            await query.message.edit_text(text,
                                          reply_markup=reply_kb.buy_product_kb(callback_data.country_code,
                                                                               callback_data.product
                                                                               ))
        case "buy":
            cost = shortcuts.get_price_from_online_sim(callback_data.country_code, callback_data.product)
            price, bot_admin_profit, profit = await calculate_price(query.from_user.id, cost)  ###
            user = await get_user(query.from_user.id)
            if user.balance < price:
                await query.answer(_("У вас недостаточно средств для покупки"), show_alert=True)
            else:
                cost = shortcuts.get_price_from_online_sim(callback_data.country_code, callback_data.product)
                user = await shortcuts.get_user(query.from_user.id)
                if user.balance < price:
                    await query.answer(_("У вас недостаточно средств для покупки"), show_alert=True)
                else:
                    try:
                        order = await shortcuts.get_phone(user.uid, callback_data.country_code, callback_data.product)
                    except Exception as e:
                        await query.answer(f'{e}', show_alert=True)
                        return
                    if order == None:
                        await query.answer(_("Нет свободных номеров!"), show_alert=True)
                        await query.message.delete()
                    else:
                        await update_user_balance(user.uid, -price)
                        msg = await query.message.answer(
                            _("Номер успешно заказан!\r\nВаш номер телефона: <code>{phone}</code>").format(
                                phone=order.phone),
                            reply_markup=reply_kb.order_actions(order.order_id))
                        await shortcuts.create_order(
                            order_id=order.order_id, user=user, profit=profit,
                            bot_admin_profit=bot_admin_profit, country_code=callback_data.country_code,
                            phone=order.phone, price=price, product=callback_data.product, msg_id=msg.message_id
                        )
                        bot: models.Bot = await user.bot
                        owner: models.MainBotUser = await bot.owner
                        async with Bot(bot.token, bot_session).context(auto_close=True) as b:
                            await b.send_message(owner.uid,
                                                 _("🥳 Клиент сделал заказ на {price} рублей. Вам начислено: {bot_admin_profit}").format(
                                                     price=price, bot_admin_profit=bot_admin_profit))


@client_bot_router.callback_query(OrderCallbackData.filter())
@flags.rate_limit(key="product")
async def products_cd(query: types.CallbackQuery, callback_data: OrderCallbackData, state: FSMContext):
    order = await shortcuts.get_order(callback_data.order_id)
    user = await shortcuts.get_user(query.from_user.id)
    match callback_data.action:
        case "change":
            order = await shortcuts.get_order(callback_data.order_id)
            now = datetime.now()
            can_ban = datetime.strptime(order.created_at.strftime("%d %m %Y %H:%M:%S"),
                                        "%d %m %Y %H:%M:%S") + timedelta(hours=2, minutes=2)
            if now > can_ban:
                try:
                    shortcuts.close_order_sim(callback_data.order_id)
                except Exception as e:
                    await query.answer(f'{e}', show_alert=True)
                    return
                new_order: shortcuts.OrderNumberResponse = await shortcuts.get_phone(user.id, order.country_code,
                                                                                     order.product)
                if new_order == None:
                    await query.answer(_("Нет свободных номеров! Подождите немного, пока освободятся"), show_alert=True)
                else:
                    await shortcuts.change_order_phone(callback_data.order_id, new_order.order_id, new_order.phone)
                    await query.message.edit_text(
                        _("Номер изменен!\r\nВаш номер телефона: <code>{phone}</code>").format(phone=new_order.phone),
                        reply_markup=reply_kb.order_actions(new_order.order_id))
            else:
                await query.answer(_("Действие можно выполнить только через 2 мин"))
        case "ban":
            order = await shortcuts.get_order(callback_data.order_id)
            now = datetime.now()
            can_ban = datetime.strptime(order.created_at.strftime("%d %m %Y %H:%M:%S"),
                                        "%d %m %Y %H:%M:%S") + timedelta(hours=2, minutes=2)
            if now > can_ban:
                if await shortcuts.cancel_order_and_finish(callback_data.order_id):
                    await shortcuts.add_phone_to_ban(user.uid, order.phone, order.product)
                    await query.message.delete()
                    await query.message.answer(
                        _("Номер добален в черный список.\r\nПокупка отменена. Возвращено: {price} руб").format(
                            price=order.price))
                else:
                    await query.message.answer(_("Действие уже выполнено"))
            else:
                await query.answer(_("Действие можно выполнить только через 2 мин"))


@client_bot_router.message(state=ProductState.search)
@flags.rate_limit(key="search_product")
async def search_product(message: types.Message, state: FSMContext):
    search_key = message.text
    data = await state.get_data()
    country_code = data['country_code']
    products = await shortcuts.get_products(country_code, search_key=search_key)
    markup = reply_kb.product_search_result(products, country_code)
    await message.answer(text=_("🔍 Результаты поиска ({product_len}):").format(product_len=len(products)),
                         reply_markup=markup)
    await state.clear()
