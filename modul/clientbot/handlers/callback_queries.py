import asyncio
import json
from contextlib import suppress

from aiogram import flags, types
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import (TelegramBadRequest, TelegramForbiddenError,
                                TelegramNotFound, TelegramRetryAfter)
from aiogram.utils.i18n import gettext as _

from clientbot import shortcuts, strings
from clientbot.data import states
from clientbot.data.callback_datas import (BroadcastCallbackData, FavouritesCallback, ServiceCallbackData,
                                           ServiceCategoryCallbackData,
                                           ServiceChoseCallbackData,
                                           SocialNetworkCallbackData,
                                           TransferCallbackData)
from clientbot.handlers.main import social_networks
from clientbot.keyboards import inline_kb, reply_kb
from clientbot.utils.exceptions import UserNotFound
from clientbot.utils.order import paginate_orders
from clientbot.utils.smm import get_service
from config import settings
from general.shortcuts import save_user
from general.inline_kbrd import percents
from loader import client_bot_router


@client_bot_router.callback_query(SocialNetworkCallbackData.filter())
@flags.rate_limit(key="services")
async def social_network(query: types.CallbackQuery, callback_data: SocialNetworkCallbackData):
    if callback_data.action == "obtain":
        try:
            await query.message.edit_text(strings.CHOOSE_SOCIAL,
                                          reply_markup=await inline_kb.service_category(callback_data.id))
        except:
            await query.message.answer(strings.CHOOSE_SOCIAL,
                                       reply_markup=await inline_kb.service_category(callback_data.id))
    elif callback_data.action == "favourites":
        btns = await inline_kb.get_favourites_btns(query.from_user.id)
        favourties = await shortcuts.get_favourites(query.from_user.id)
        await query.message.edit_text(_("Список избранного") if len(favourties) > 0 else _("Пусто"), reply_markup=btns)
    elif callback_data.action == "back":
        with suppress(TelegramBadRequest):
            await query.message.delete()
        await query.message.answer(strings.MAIN_MENU.format(query.from_user.full_name),
                                   reply_markup=await reply_kb.main_menu(query.message.from_user.id))


@client_bot_router.callback_query(ServiceCategoryCallbackData.filter())
@flags.rate_limit(key="services")
async def service_category(query: types.CallbackQuery, callback_data: ServiceCategoryCallbackData):
    if callback_data.action == "obtain":
        await query.message.edit_text(strings.CHOOSE_SOCIAL,
                                      reply_markup=await inline_kb.services(callback_data.smm_idx, callback_data.id))
    elif callback_data.action == "back":
        await query.message.edit_reply_markup(await inline_kb.social_networks())


@client_bot_router.callback_query(ServiceCallbackData.filter())
@flags.rate_limit(key="services", rate=2)
async def services(query: types.CallbackQuery, callback_data: ServiceCallbackData):
    if callback_data.action == "obtain":
        service = await get_service(callback_data.id)
        if not service:
            await query.answer(_("Услуга не доступна"), show_alert=True)
            return
        if int(service.min) == 1 and int(service.max) == 1:
            service_price = float(service.rate)
        else:
            service_price = shortcuts.calculate_service_price(service)
        price, _, _ = await shortcuts.calculate_price(query.from_user.id, service_price)
        await query.message.edit_text(
            strings.SERVICE_DETAILS.format(
                service_id=service.service,
                service=service.name,
                quantity="" if int(service.min) == 1 and int(service.max) == 1 else " за 1000",
                price=f"{price:.2f}",
                min=int(service.min),
                max=int(service.max),
                description=service.description,
                compilation_time=service.time
            ),
            reply_markup=inline_kb.service_chose(
                callback_data.smm_idx, callback_data.category_idx, callback_data.id)
        )
    elif callback_data.action == "back":
        markup = await inline_kb.service_category(callback_data.smm_idx)
        await query.message.edit_reply_markup(markup)


@client_bot_router.callback_query(FavouritesCallback.filter())
@flags.rate_limit(key="services")
async def service_chose(query: types.CallbackQuery, state: FSMContext, callback_data: FavouritesCallback):
    if callback_data.action == "view":
        service = await get_service(callback_data.service)
        if int(service.min) == 1 and int(service.max) == 1:
            service_price = float(service.rate)
        else:
            service_price = shortcuts.calculate_service_price(service)
        price, _, _ = await shortcuts.calculate_price(query.from_user.id, service_price)
        await query.message.edit_text(
            strings.SERVICE_DETAILS.format(
                service_id=service.service,
                service=service.name,
                quantity="" if int(service.min) == 1 and int(service.max) == 1 else " за 1000",
                price=f"{price:.2f}",
                min=int(service.min),
                max=int(service.max),
                description=service.description,
                compilation_time=service.time
            ),
            reply_markup=inline_kb.favourite_service_chose(callback_data.smm, callback_data.category,
                                                           callback_data.service)
        )
    elif callback_data.action == "delete":
        await query.answer(_("Удалено из избранного"), show_alert=True)
        await shortcuts.delete_from_favourites(query.from_user.id, callback_data.service)
        btns = await inline_kb.get_favourites_btns(query.from_user.id)
        favourties = await shortcuts.get_favourites(query.from_user.id)
        await query.message.edit_text(_("Список избранного") if len(favourties) > 0 else _("Пусто"), reply_markup=btns)
    elif callback_data.action == "back":
        await social_network(query, SocialNetworkCallbackData(
            action="favourites", id=0
        ))
    elif callback_data.action == "exit":
        await query.message.delete()
        await social_networks(query.message)


@client_bot_router.callback_query(ServiceChoseCallbackData.filter())
@flags.rate_limit(key="services")
async def service_chose(query: types.CallbackQuery, state: FSMContext, callback_data: ServiceChoseCallbackData):
    service = await get_service(callback_data.service)
    if service:
        if callback_data.action == "back":
            await query.message.edit_text(strings.CHOOSE_SOCIAL,
                                          reply_markup=await inline_kb.services(callback_data.smm_idx,
                                                                                callback_data.category_idx))
        elif callback_data.action == "add_to_favourites":
            res = await shortcuts.add_to_favourites(query.from_user.id, callback_data.service, callback_data.smm_idx,
                                                    callback_data.category_idx)
            await query.answer(_("Услуга добавлена в избранные") if res else _("Услуга уже была добавлена ранее"),
                               show_alert=True)
        else:
            with suppress(TelegramBadRequest):
                await query.message.edit_reply_markup()
                await query.message.answer(
                    _("💬 Вы заказываете «{service_name}»\n\n"
                      "Для оформления заказа укажите ссылку.").format(service_name=service.name),
                    reply_markup=reply_kb.cancel()
                )
                await state.set_state(states.Order.link)
                await state.update_data(_service=callback_data.service)
                await state.update_data(_category_idx=callback_data.category_idx)
                await state.update_data(_smm_idx=callback_data.smm_idx)
                await query.answer()
    else:
        await query.answer(_("Услуга не доступна"), show_alert=True)


# Transfer to balance
@client_bot_router.callback_query(TransferCallbackData.filter())
@flags.rate_limit(key="transfer_money")
async def transfer_money(query: types.CallbackQuery, state: FSMContext):
    if await shortcuts.referral_balance(query.from_user.id) <= 0:
        await query.answer(_("⛔️ У вас на балансе недостаточно средств"), show_alert=True)
    else:
        await query.answer()
        try:
            await query.message.delete()
        except TelegramBadRequest:
            pass
        await query.message.answer(_("💸 Введите сумму перевода денег на ваш основной счёт"),
                                   reply_markup=reply_kb.cancel())
        await state.set_state(states.Transfer.amount)


# Order pagination
@client_bot_router.callback_query(Text(text_startswith="child-change-percent"))
@flags.rate_limit(key="order_paginate")
async def order_paginate(query: types.CallbackQuery):
    bot = await shortcuts.get_current_bot()
    await query.message.edit_text(_("Выберите новую процентную ставку"),
                                  reply_markup=percents('edit-bot-percent', 'back-child-admin', bot.id))


@client_bot_router.callback_query(Text(text_startswith="delete"))
@flags.rate_limit(key="order_paginate")
async def order_paginate(query: types.CallbackQuery):
    await query.message.delete()


@client_bot_router.callback_query(Text(text_startswith="order-pagination"))
@flags.rate_limit(key="order_paginate")
async def order_paginate(query: types.CallbackQuery):
    page = int(query.data.split(":")[1])
    try:
        text, reply_markup = await paginate_orders(query.from_user.id, page)
    except UserNotFound:
        await save_user(query.from_user)
        text, reply_markup = await paginate_orders(query.from_user.id, page)
    await query.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)


@client_bot_router.callback_query(BroadcastCallbackData.filter(), state=states.Broadcast.confirmation)
@flags.rate_limit(key="broadcast_confirmation")
async def broadcast_confirmation(query: types.CallbackQuery, callback_data: BroadcastCallbackData,
                                 state: FSMContext):
    if callback_data.confirm:
        await query.message.edit_text(strings.WAIT)
        users = await shortcuts.get_all_users()
        data = await state.get_data()
        message = types.Message(**json.loads(data.get('message')))
        await state.clear()
        succeed, failed = 0, 0
        for user in users:
            if user.uid in settings.ADMIN_LIST:
                continue
            try:
                await message.send_copy(user.uid)
                succeed += 1
                await asyncio.sleep(settings.SLEEP_TIME)
            except TelegramRetryAfter as e:
                await asyncio.sleep(e.retry_after)
            except (TelegramBadRequest, TelegramForbiddenError, TelegramNotFound):
                failed += 1
        await query.message.answer(strings.BROADCAST_RESULT.format(succeed, failed))
    else:
        await query.message.edit_text(strings.CANCELLED)

    await state.clear()


@client_bot_router.callback_query(BroadcastCallbackData.filter())
@flags.rate_limit(key="cancel_broadcasting")
async def cancel_broadcasting(query: types.CallbackQuery):
    await query.answer(_("Это действие недопустимо."))
    try:
        await query.message.delete()
    except TelegramBadRequest:
        await query.message.edit_reply_markup()


@client_bot_router.callback_query(text="faq-information")
@flags.rate_limit(key="faq-information")
async def cancel_broadcasting(query: types.CallbackQuery):
    await query.message.answer(_("""▶️Время выполнения заказа
Время выполнения заказа зависит от поставщика. Обычно выполнение начинается сразу. Максимальный срок выполнения заказа - 7 дней. Если по истечении данного срока заказ не был выполнен, клиенту следует написать в службу поддержки.
▶️Ошибочно указана ссылка или тип услуги
Если клиент ошибочно указал ссылку, или услугу на неё - отменить заказ уже невозможно. Если ссылка была указана не существующая, или не действующая в данной социальной сети - то заказ будет в течении 7-ми дней отменён. Администрация не может отменить заказ, поскольку заказы после оформления автоматически передаются поставщикам.
▶️Списали подписчиков
Если происходят единичные списания - то это нормально, поскольку это естественные отписки. Массово - подписчики сами по себе не отписываются. Если произошло массовое списание - значит алгоритмы в соц. сети, где вы продвигаете аккаунт - заподозрили подозрительную активность. Любую накрутку Вы производите на свой страх и риск, и администрация данного сервиса, и никто другой кроме Вас - за это ответственности не несёт.
▶️Поступление средств на счёт
После проведения оплаты, как правило, средства сразу поступают на счёт. Если перед оплатой была выбрана какая- либо услуга - средства сразу уйдут на её выполнение. Список заказов - Вы можете увидеть в разделе «Социальные сети». Если Вы уверены что оплата прошла, а баланс не был пополнен (или заказ не был создан) - напишите в службу поддержки.
▶️Возврат средств
Средства внесённые клиентом на баланс - не подлежат возврату."""))
