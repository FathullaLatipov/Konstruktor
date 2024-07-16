import asyncio
from datetime import datetime, timedelta
import json
import re
from contextlib import suppress
from io import BytesIO

from aiogram import types, F, Bot, html
from aiogram.dispatcher.fsm.context import FSMContext
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNotFound,
    TelegramRetryAfter
)
from aiogram.utils.i18n import gettext as _

from tortoise.exceptions import IntegrityError

from clientbot import strings, shortcuts
from clientbot.data.callback_datas import (
    AdminPanelCallbackData,
    BroadcastCallbackData,
    MandatorySubscription,
    Promocodes,
    Switch,
)
from clientbot.data.states import (
    BroadcastState,
    ChangePhoto,
    ChangeChannelLink,
    ChangeAdmin,
    ChangeSupport,
    Post,
    AddSubscriptionChat,
    PromocodeState
)
from clientbot.filters.IsAdmin import IsAdminFilter
from clientbot.handlers.horoscope.functs.statistic import get_horoscope_data, get_statistic
from clientbot.keyboards import inline_kb, reply_kb
from config import settings, scheduler
from clientbot.handlers.leomatch.shortcuts import get_analitics
from db import models
from db.models import GPTTypeEnum, MainBotUser, PromocodesModel
from clientbot.handlers.anon.handlers.statistic import get_anon_analitics, get_anon_data
from general.inline_kbrd import percents
from loader import client_bot_router
from mainbot.shortcuts import add_broadcast, collect_and_run_broadcast
from utils.analitics import AnaliticData, AnaliticInfoData, gen_data, make_analitic, make_analitic_graph
from utils.functions import get_call_method, check_url
from tortoise.functions import Sum
import pytz

from utils.img_analitic.main import ImageAnaliticsDateRange, ImageAnaliticsSimpleData


@client_bot_router.message(IsAdminFilter(), commands="admin")
async def enter_admin_panel(message: types.Message):
    await message.answer(_("Панель администратора"), reply_markup=await inline_kb.admin_buttons())


@client_bot_router.callback_query(Switch.filter())
async def switch_create_bot(query: types.CallbackQuery, callback_data: Switch, state: FSMContext):
    if callback_data.action == "switch-leo":
        await shortcuts.turn_bot_data("enable_leo")
    elif callback_data.action == "switch-chatgpt":
        await shortcuts.turn_bot_data("enable_chatgpt")
    elif callback_data.action == "switch-download":
        await shortcuts.turn_bot_data("enable_download")
    elif callback_data.action == "switch-music":
        await shortcuts.turn_bot_data("enable_music")
    elif callback_data.action == "switch-create":
        await shortcuts.turn_bot_data("enable_child_bot")
    elif callback_data.action == "switch-promotion":
        await shortcuts.turn_bot_data("enable_promotion")
    elif callback_data.action == "switch-horoscope":
        await shortcuts.turn_bot_data("enable_horoscope")
    elif callback_data.action == "switch-anon":
        await shortcuts.turn_bot_data("enable_anon")
    elif callback_data.action == "switch-sms":
        await shortcuts.turn_bot_data("enable_sms")
    await query.message.edit_text(_("Панель администратора"), reply_markup=await inline_kb.admin_buttons())


@client_bot_router.callback_query(Promocodes.filter())
async def switch_create_bot(query: types.CallbackQuery, callback_data: Promocodes, state: FSMContext):
    if callback_data.action == "select":
        promocode = await PromocodesModel.filter(id=callback_data.promocode_id).first()
        last_activate = promocode.last_used_at.strftime('%d.%m.%Y') if promocode.last_used_at else _("Не активирован")
        await query.message.edit_text(_("Управление промокодом\n"
                                        "Код: <code>{promocode_code}</code>\n"
                                        "Сумма: {promocode_sum}\n"
                                        "Рассчитан на: {promocode_count}\n"
                                        "Активировали: {promocode_used_count}\n"
                                        "Создан: {time}\n"
                                        "Последнее использование: {last_activate}").format(
            promocode_code=promocode.code,
            promocode_sum=promocode.sum,
            promocode_count=promocode.count,
            promocode_used_count=promocode.used_count,
            time=promocode.created_at.strftime('%d.%m.%Y'),
            last_activate=last_activate),
            parse_mode="HTML",
            reply_markup=inline_kb.promocode_manage(callback_data.promocode_id))
    elif callback_data.action == "refill":
        await state.update_data(promocode_id=callback_data.promocode_id)
        await query.message.delete()
        await query.message.answer(_("Введите кол-во добавления активации"), reply_markup=reply_kb.cancel())
        await state.set_state(PromocodeState.refill)
    elif callback_data.action == "add":
        await query.message.delete()
        await query.message.answer(
            _("Отправьте сумму промокода.\nСумма указываете за единицу промокода. (например 50).\nВ последующем сообщении вы укажите количество активации (Например 5) следовательно, с Вашего баланса спишется 5 * 50 = 250 рублей."),
            reply_markup=reply_kb.cancel())
        await state.set_state(PromocodeState.set_sum)
    elif callback_data.action == "delete":
        promocode = await PromocodesModel.filter(id=callback_data.promocode_id).first()
        await query.message.edit_text(_("Вы уверены, что хотите удалить промокод?\n"
                                        "Промокод расчитан на {promocode_count} человек на сумму {promocode_sum}\n"
                                        "Было активированно {promocode_used_count} раз, посему вернется: {final_amount} руб.").format(
            promocode_count=promocode.count, promocode_sum=promocode.sum, promocode_used_count=promocode.used_count,
            final_amount=(promocode.count - promocode.used_count) * promocode.sum),
            reply_markup=inline_kb.promocode_sure_delete(callback_data.promocode_id))
    elif callback_data.action == "delete-confirm":
        promocode = await PromocodesModel.filter(id=callback_data.promocode_id).first()
        admin = await shortcuts.get_main_bot_user(query.from_user.id)
        admin.balance += (promocode.count - promocode.used_count) * promocode.sum
        await admin.save()
        await promocode.delete()
        uid = query.from_user.id
        await query.message.edit_text(_("Панель управление промокодами"),
                                      reply_markup=await inline_kb.promocode_menu(uid))
    elif callback_data.action == "back":
        await query.message.edit_text(_("Панель администратора"), reply_markup=await inline_kb.admin_buttons())


@client_bot_router.message(state=PromocodeState.refill)
async def set_sum(message: types.Message, state: FSMContext):
    if message.text == _("Отмена"):
        await message.delete()
        uid = message.from_user.id
        await message.answer(_("Панель управление промокодами"), reply_markup=await inline_kb.promocode_menu(uid))
        return
    try:
        sum = int(message.text)
    except:
        await message.answer(_("Неверное количество"))
        return
    await state.update_data(count=sum, type='refill')
    data = await state.get_data()
    promocode_id = data.get("promocode_id")
    promocode = await PromocodesModel.filter(id=promocode_id).first()
    if not promocode:
        await message.answer(_("Промокод не найден"))
        return
    total_sum = sum * promocode.sum
    admin = await shortcuts.get_main_bot_user(message.from_user.id)
    if admin.balance < total_sum:
        await message.answer(_("Недостаточно средств, текущий баланс: {admin_balance}, требуется {total_sum}").format(
            admin_balance=admin.balance, total_sum=total_sum))
        return
    await message.answer(_("Это будет стоить {total_sum} р, Вы согласны?").format(total_sum=total_sum), reply_markup=reply_kb.yes_no())
    await state.set_state(PromocodeState.confirm_add)


@client_bot_router.message(state=PromocodeState.confirm_add)
async def set_sum(message: types.Message, state: FSMContext):
    if message.text == _("Да"):
        data = await state.get_data()
        type = data.get("type")
        if type == 'add':
            sum = data.get("sum")
            count = data.get("count")
            code = data.get("code")
        elif type == 'refill':
            promocode_id = data.get("promocode_id")
            promocode = await PromocodesModel.filter(id=promocode_id).first()
            if not promocode:
                await message.answer(_("Промокод не найден"))
                return
            sum = promocode.sum
            count = data.get('count')
            code = promocode.code
        total_sum = sum * count
        admin = await shortcuts.get_main_bot_user(message.from_user.id)
        if admin.balance < total_sum:
            await message.answer(_("Недостаточно средств, текущий баланс: {admin_balance}, требуется {total_sum}").format(admin_balance=admin.balance, total_sum=total_sum))
            return
        admin.balance -= total_sum
        await admin.save()
        if type == 'add':
            await PromocodesModel.create(code=code, sum=sum, count=count, admin=admin, created_at=datetime.now().date())
            await message.answer(_("Промокод успешно создан"), reply_markup=types.ReplyKeyboardRemove())
        else:
            promocode.count += count
            await promocode.save()
            await message.answer(_("Промокод успешно пополнен"), reply_markup=types.ReplyKeyboardRemove())
    await state.clear()
    uid = message.from_user.id
    await message.answer(_("Панель управление промокодами"), reply_markup=await inline_kb.promocode_menu(uid))


@client_bot_router.message(state=PromocodeState.set_sum)
async def set_sum(message: types.Message, state: FSMContext):
    if message.text == _("Отмена"):
        await message.delete()
        uid = message.from_user.id
        await message.answer(_("Панель управление промокодами"), reply_markup=await inline_kb.promocode_menu(uid))
        return
    try:
        sum = float(message.text)
    except:
        await message.answer(_("Неверная сумма"))
        return
    await state.update_data(sum=sum)
    await message.answer(_("Отправьте количество активаций"), reply_markup=reply_kb.cancel())
    await state.set_state(PromocodeState.set_count)


@client_bot_router.message(state=PromocodeState.set_count)
async def set_count(message: types.Message, state: FSMContext):
    if message.text == _("Отмена"):
        await message.delete()
        uid = message.from_user.id
        await message.answer(_("Панель управление промокодами"), reply_markup=await inline_kb.promocode_menu(uid))
        return
    try:
        count = int(message.text)
    except:
        await message.answer(_("Неверное количество"))
        return
    data = await state.get_data()
    sum = data.get("sum")
    total_sum = sum * count
    admin = await shortcuts.get_main_bot_user(message.from_user.id)
    if admin.balance < total_sum:
        await message.answer(_("Недостаточно средств, текущий баланс: {admin_balance}").format(admin_balance=admin.balance))
        return
    await state.update_data(count=count)
    await message.answer(_("Отправьте код промокода"), reply_markup=reply_kb.cancel())
    await state.set_state(PromocodeState.set_code)


@client_bot_router.message(state=PromocodeState.set_code)
async def set_code(message: types.Message, state: FSMContext):
    if message.text == _("Отмена"):
        await message.delete()
        uid = message.from_user.id
        await message.answer(_("Панель управление промокодами"), reply_markup=await inline_kb.promocode_menu(uid))
        return
    code = message.text
    await state.update_data(code=code, type='add')
    data = await state.get_data()
    sum = data.get("sum")
    count = data.get("count")
    admin = await shortcuts.get_main_bot_user(message.from_user.id)
    total_sum = sum * count
    if admin.balance < total_sum:
        await message.answer(_("Недостаточно средств, текущий баланс: {admin_balance} р., требуется {total_sum} р.").format(admin_balance=admin.balance, total_sum=total_sum))
        return
    await message.answer(_("Это будет стоить {total_sum} р, Вы согласны?").format(total_sum=total_sum), reply_markup=reply_kb.yes_no())
    await state.set_state(PromocodeState.confirm_add)


@client_bot_router.callback_query(IsAdminFilter(), AdminPanelCallbackData.filter())
async def admin_panel(query: types.CallbackQuery, callback_data: AdminPanelCallbackData, state: FSMContext):
    bot = await shortcuts.get_bot()
    await query.answer()
    if callback_data.action == "request_history":
        owner: MainBotUser = bot.owner
        if owner.last_export_history and (owner.last_export_history + timedelta(days=1) > datetime.now(pytz.UTC)):
            await query.message.answer(
                _("Вы уже делали запрос, ожидайте результата. (Повторый запрос можно сделать завтра)"))
            return
        scheduler.add_job(shortcuts.task_admin_export_history, args=(query.from_user.id, bot.username),
                          id=f"admin-export-history-{query.from_user.id}", replace_existing=False, max_instances=1)
        await query.message.answer(_("Ваш запрос принят, ожидайте результата. (Повторый запрос можно сделать завтра)"))
    elif callback_data.action == "statistics":
        await query.message.edit_text(_("Начала генерации аналитики"))
        now = datetime.now()
        this_week = now - timedelta(days=6)
        this_month = now - timedelta(days=30)
        data = await state.get_data()
        bot = data['bot']
        bot_info = await bot.get_me()
        bot_db = await models.Bot.filter(username=bot_info.username).first()
        new_clients = await models.ClientBotUser.filter(created_at__gte=this_week,
                                                        bot__username=bot_info.username).order_by('created_at')
        update_clients = await models.ClientBotUser.filter(updated_at__gte=this_week,
                                                           bot__username=bot_info.username).order_by('updated_at')
        data = gen_data(new_clients, 'created_at', lambda x: x.strftime("%d.%m.%Y"))
        data_update = gen_data(update_clients, 'updated_at', lambda x: x.strftime("%d.%m.%Y"))

        bytes = make_analitic_graph(bot_info.username, [
            AnaliticData(
                'Регистрация пользователей',
                [f'{x}' for x in data.keys()],
                data.values()
            ),
            AnaliticData(
                'Активность пользователей',
                [f'{x}' for x in data_update.keys()],
                data_update.values()
            ),
        ])
        await query.message.answer_photo(types.BufferedInputFile(bytes, filename="image.png"))
        order_create = await models.Order.filter(created_at__gte=this_week,
                                                 user__bot__username=bot_info.username).order_by('created_at')
        order_create_data = gen_data(order_create, 'created_at', lambda x: x.strftime("%d.%m.%Y"))
        order_finish = await models.Order.filter(updated_at__gte=this_week, user__bot__username=bot_info.username,
                                                 status='Completed').order_by('updated_at')
        order_finish_data = gen_data(order_finish, 'updated_at', lambda x: x.strftime("%d.%m.%Y"))
        if bot_db.enable_promotion:
            bytes = make_analitic_graph(bot_info.username, [
                AnaliticData(
                    'Заказы',
                    [f'{x}' for x in order_create_data.keys()],
                    order_create_data.values()
                ),
                AnaliticData(
                    'Заказы (Выполнено)',
                    [f'{x}' for x in order_finish_data.keys()],
                    order_finish_data.values()
                ),
            ])
            await query.message.answer_photo(types.BufferedInputFile(bytes, filename="image.png"))
        users = await shortcuts.get_all_users_count()  #
        main_bot_users = await shortcuts.users_count()
        new_users = await shortcuts.get_new_users_count()
        ordered_today = await shortcuts.ordered_today()
        earned_today = await shortcuts.earned_today()
        earned = await shortcuts.earned()
        statistic = await get_analitics(bot_info.username)
        records = models.GPTRecordModel.filter(bot__username=bot_info.username)
        horoscope_data = await get_horoscope_data(bot_info.username)
        records_payments = models.BillHistory.filter(user__bot__username=bot_db.username, type=models.BillTypeEnum.AI,
                                                     status=models.BillStatus.PAID)
        a = (await records_payments.filter(created_at__gte=now.date()).annotate(sum=Sum('amount')).values('sum'))
        a = a[0]['sum'] if a else 0
        b = (await records_payments.filter(created_at__gte=this_week.date()).annotate(sum=Sum('amount')).values('sum'))
        b = b[0]['sum'] if b else 0
        c = (await records_payments.filter(created_at__gte=this_month.date()).annotate(sum=Sum('amount')).values('sum'))
        c = c[0]['sum'] if c else 0
        d = (await records_payments.filter().annotate(sum=Sum('amount')).values('sum'))
        d = d[0]['sum'] if d else 0
        musics = models.DownloadAnalyticsModel.filter(domain='music', bot_username=bot_info.username)
        anon = await get_anon_data(bot_db)
        media = models.DownloadAnalyticsModel.filter(bot_username=bot_info.username).exclude(domain='music')
        today = await media.filter(date__gte=now.date()).order_by('-count')
        media_one = []
        for i, x in enumerate(today[:4]):
            media_one.append(ImageAnaliticsSimpleData(f'{i + 1}. {x.domain} ', x.count))
        media_two = []
        for i, x in enumerate(today[4:8]):
            media_two.append(ImageAnaliticsSimpleData(f'{i + 1}. {x.domain} ', x.count))
        media_three = []
        for i, x in enumerate(today[8:12]):
            media_three.append(ImageAnaliticsSimpleData(f'{i + 1}. {x.domain} ', x.count))
        now_date = datetime.now()

        paster = []
        now = 0
        if bot_db.enable_leo:
            paster.append(
                AnaliticInfoData(
                    'Знакомста',
                    [
                        ImageAnaliticsSimpleData("👥 Всего: ", statistic.count_users),
                        ImageAnaliticsSimpleData("🤵‍♂️ Мужчин: ", statistic.count_man),
                        ImageAnaliticsSimpleData("🧍‍♀️ Женщин: ", statistic.count_female),
                    ]
                )
            )
        if bot_db.enable_chatgpt:
            paster.append(
                AnaliticInfoData(
                    'ChatGPT',
                    [
                        ImageAnaliticsDateRange(
                            await records.filter(created_at__gte=now_date.date()).filter(
                                type=models.GPTTypeEnum.REQUEST).count(),
                            await records.filter(created_at__gte=this_week.date()).filter(
                                type=models.GPTTypeEnum.REQUEST).count(),
                            await records.filter(created_at__gte=this_month.date()).filter(
                                type=models.GPTTypeEnum.REQUEST).count(),
                            await records.filter().filter(type=models.GPTTypeEnum.REQUEST).count(),
                        ),
                    ]
                )
            )
            paster.append(
                AnaliticInfoData(
                    'Ген. картинок',
                    [
                        ImageAnaliticsDateRange(
                            await records.filter(created_at__gte=now_date.date()).filter(
                                type=models.GPTTypeEnum.PICTURE).count(),
                            await records.filter(created_at__gte=this_week.date()).filter(
                                type=models.GPTTypeEnum.PICTURE).count(),
                            await records.filter(created_at__gte=this_month.date()).filter(
                                type=models.GPTTypeEnum.PICTURE).count(),
                            await records.filter().filter(type=models.GPTTypeEnum.PICTURE).count(),
                        ),
                    ]
                )
            )
            paster.append(
                AnaliticInfoData(
                    'Баланс (ИИ)',
                    [
                        ImageAnaliticsDateRange(
                            a,
                            b,
                            c,
                            d
                        ),
                    ]
                )
            )
        if bot_db.enable_horoscope:
            paster.append(
                AnaliticInfoData(
                    'Гороскоп',
                    [
                        ImageAnaliticsDateRange(
                            horoscope_data.today,
                            horoscope_data.week,
                            horoscope_data.month,
                            horoscope_data.all,
                        ),
                    ]
                )
            )
        if bot_db.enable_music:
            paster.append(
                AnaliticInfoData(
                    'Музыка',
                    [
                        ImageAnaliticsDateRange(
                            await musics.filter(date__gte=now_date.date()).count(),
                            await musics.filter(date__gte=this_week.date()).count(),
                            await musics.filter(date__gte=this_month.date()).count(),
                            await musics.filter().count(),
                        ),
                    ]
                )
            )
        if bot_db.enable_anon:
            paster.append(
                AnaliticInfoData(
                    'Анонимный чат',
                    [
                        ImageAnaliticsSimpleData("Все пользователи: ", anon.all_users),
                        ImageAnaliticsSimpleData("Мужчин: ", anon.mans_count),
                        ImageAnaliticsSimpleData("Женщин: ", anon.womans_count),
                    ]
                )
            )
            paster.append(
                AnaliticInfoData(
                    'Анонимный чат 2',
                    [
                        ImageAnaliticsSimpleData("Сейчас общаются: ", anon.now_chat),
                        ImageAnaliticsSimpleData("Мужчин: ", anon.now_mans),
                        ImageAnaliticsSimpleData("Женщин: ", anon.now_womans),
                    ]
                )
            )
            paster.append(
                AnaliticInfoData(
                    'Покупка VIP',
                    [
                        ImageAnaliticsDateRange(
                            anon.vip_today,
                            anon.vip_week,
                            anon.vip_month,
                            anon.vip_all,
                        ),
                    ]
                )
            )
        sms = models.SMSOrder.filter(user__bot__username=bot_info.username)
        if bot_db.enable_sms:
            paster.append(
                AnaliticInfoData(
                    'СМС активация',
                    [
                        ImageAnaliticsDateRange(
                            await sms.filter(created_at__gte=now_date.date(), receive_status='received').count(),
                            await sms.filter(created_at__gte=this_week.date(), receive_status='received').count(),
                            await sms.filter(created_at__gte=this_month.date(), receive_status='received').count(),
                            await sms.filter(receive_status='received').count(),
                        ),
                    ]
                )
            )
        if bot_db.enable_download:
            if len(media_one) > 0:
                paster.append(
                    AnaliticInfoData(
                        'Скачка медиа',
                        media_one
                    )
                )
            if len(media_two) > 0:
                paster.append(
                    AnaliticInfoData(
                        'Скачка медиа 2',
                        media_two
                    )
                )
            if len(media_three) > 0:
                paster.append(
                    AnaliticInfoData(
                        'Скачка медиа 3',
                        media_three
                    )
                )
            if await media.filter().count() > 0:
                paster.append(
                    AnaliticInfoData(
                        'Скачка медиа общее', [
                            ImageAnaliticsDateRange(
                                await media.filter(date__gte=now_date.date()).count(),
                                await media.filter(date__gte=this_week.date()).count(),
                                await media.filter(date__gte=this_month.date()).count(),
                                await media.filter().count(),
                            ),
                        ]
                    )
                )
        clients = models.ClientBotUser.filter(bot__username=bot_info.username)
        paster.append(
            AnaliticInfoData(
                'Новые клиенты',
                [
                    ImageAnaliticsDateRange(
                        await clients.filter(created_at__gte=now_date.date()).count(),
                        await clients.filter(created_at__gte=this_week.date()).count(),
                        await clients.filter(created_at__gte=this_month.date()).count(),
                        await clients.filter().count(),
                    ),
                ],
            ),
        )
        paster = [paster[i:i + 4] for i in range(0, len(paster), 4)]
        bytes = make_analitic(bot_info.username, [
            [
                AnaliticInfoData(
                    'Общая информация',
                    [
                        ImageAnaliticsSimpleData("Все пользователи: ", users),
                        ImageAnaliticsSimpleData("Новые пользователи: ", new_users),
                        ImageAnaliticsSimpleData("Заработано всего: ", earned),
                        ImageAnaliticsSimpleData("Прибыль(Сегодня): ", earned_today),
                    ]
                ),
                AnaliticInfoData(
                    'Общая информация 2',
                    [
                        ImageAnaliticsSimpleData("Заказов за сегодня: ", ordered_today),
                    ]
                ),
            ],
            *paster
        ])
        await query.message.answer_photo(types.BufferedInputFile(bytes, filename="image.png"))
        await query.message.answer(_("Аналитика готова"))
    elif callback_data.action == "broadcast":
        try:
            await query.message.delete()
        except TelegramBadRequest:
            await query.message.edit_reply_markup()
        text = strings.BROADCAST.format(
            int(await shortcuts.get_all_users_count() * settings.SLEEP_TIME)
        )
        broadcast = await models.BroadcastModel.filter(bot=bot).first()
        additional_text = ""
        if broadcast:
            text += _("\n\n📣 Сейчас идет рассылка, последний клиент {broadcast_last_complete_user_id}").format(broadcast_last_complete_user_id=broadcast.last_complete_user_id)
        await query.message.answer(text=text, reply_markup=reply_kb.cancel())
        await state.set_state(BroadcastState.message)
    elif callback_data.action == "mandatory-subscription":
        chats = await shortcuts.get_subscription_chats(bot)
        text = strings.get_subscription_chats(bot.mandatory_subscription, chats)
        await query.message.edit_text(text, reply_markup=inline_kb.mandatory_subscription_status(
            bot.mandatory_subscription, len(chats)), disable_web_page_preview=True)
    elif callback_data.action == "change-photo":
        await query.message.edit_text(_("Отправьте фото чтобы изменить"), reply_markup=inline_kb.admin_panel_cancel())
        await state.set_state(ChangePhoto.photo)
    elif callback_data.action == "channel-link":
        await query.message.edit_text(_("Отправьте ссылку на канал\n"
                                      "Текущий: {bot_news_channel}").format(bot_news_channel=bot.news_channel),
                                      reply_markup=inline_kb.admin_panel_cancel())
        await state.set_state(ChangeChannelLink.link)
    elif callback_data.action == "change-percent":
        await query.message.edit_text(
            _("Ваша процентная ставка: {bot_percent}%\n\n"
            "Выберите процент для изменения:").format(bot_percent=bot.percent),
            reply_markup=percents('edit-percent-in-bot', "back-admin", bot.id)
        )
    elif callback_data.action == "change-admin":
        await state.set_state(ChangeAdmin.uid)
        await query.message.edit_text(_("Отправьте ИД нового администратора"
                                      "(Внимание! После введения ид этот человек "
                                      "автоматический станет владельцем этого бота)"),
                                      reply_markup=inline_kb.admin_panel_cancel())
    elif callback_data.action == "change-support":
        await state.set_state(ChangeSupport.username_or_uid)
        await query.message.edit_text(_("Отправьте username или ИД новой поддержки\n"
                                      "Текущий: {bot_support}").format(bot_support=bot.support),
                                      reply_markup=inline_kb.admin_panel_cancel())
    elif callback_data.action == "dump-users":
        await query.message.edit_text(_("Готовимся... Пожалуйста, подождите немного. (Может занять до нескольких часов)"))
        data = _("uid, Полное имя, Имя пользователя, Текущий баланс, Баланс за всё время, Кол-во заказов, Сумма заказов\n")
        infos = await shortcuts.get_users_statistic(query.from_user.id)
        for info in infos:
            data += ",".join(list([str(x) for x in info.values()]))
            data += "\n"
        with BytesIO() as file:
            file.write(data.encode("utf-8"))
            file.seek(0)
            await query.message.answer_document(types.BufferedInputFile(file.read(), "users.txt"))
    elif callback_data.action == "promocodes":
        uid = query.from_user.id
        await query.message.edit_text(_("Панель управление промокодами"),
                                      reply_markup=await inline_kb.promocode_menu(uid))
    elif callback_data.action == "manage-switch-promotion":
        await query.message.edit_text(
            _("Здесь Вы можете включить или отключить возможность накрутки подписчиков через Ваш бот\nТекущее состояние: {on_off}").format(on_off=('_(Включено') if bot.enable_promotion else _('Отключено')),
            reply_markup=inline_kb.switcher('switch-promotion'))
    elif callback_data.action == "manage-switch-create":
        await query.message.edit_text(
            _("Здесь Вы можете включить или отключить возможность создавать дочерних ботов через Ваш бот\nТекущее состояние: {'Включено' if bot.enable_child_bot else 'Отключено'}").format(on_off=_('Включено') if bot.enable_child_bot else _('Отключено')),
            reply_markup=inline_kb.switcher('switch-create'))
    elif callback_data.action == "manage-switch-music":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам слушать музыку\nТекущее состояние: {'Включено' if bot.enable_music else 'Отключено'}",
            reply_markup=inline_kb.switcher('switch-music'))
    elif callback_data.action == "manage-switch-download":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам скачивать видео из ютуба\nТекущее состояние: {'Включено' if bot.enable_download else 'Отключено'}",
            reply_markup=inline_kb.switcher('switch-download'))
    elif callback_data.action == "manage-switch-leomatch":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам знакомиться между собой\nТекущее состояние: {'Включено' if bot.enable_leo else 'Отключено'}\n",
            reply_markup=inline_kb.switcher('switch-leo'))
    elif callback_data.action == "manage-switch-chatgpt":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам пользоваться ChatGPT\nТекущее состояние: {'Включено' if bot.enable_chatgpt else 'Отключено'}\n",
            reply_markup=inline_kb.switcher('switch-chatgpt'))
    elif callback_data.action == "manage-switch-horoscope":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам пользоваться Гороскопом\nТекущее состояние: {'Включено' if bot.enable_horoscope else 'Отключено'}\n",
            reply_markup=inline_kb.switcher('switch-horoscope'))
    elif callback_data.action == "manage-switch-anon":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам пользоваться Анонимным чатом\nТекущее состояние: {'Включено' if bot.enable_anon else 'Отключено'}\n",
            reply_markup=inline_kb.switcher('switch-anon'))
    elif callback_data.action == "manage-switch-sms":
        await query.message.edit_text(
            f"Здесь Вы можете включить или отключить возможность клиентам заказывать виртуальные номер\nТекущее состояние: {'Включено' if bot.enable_sms else 'Отключено'}\n",
            reply_markup=inline_kb.switcher('switch-sms'))
    elif callback_data.action == "cancel":
        await state.clear()
        await query.message.edit_text("Панель администратора", reply_markup=await inline_kb.admin_buttons())


@client_bot_router.message(state=BroadcastState.message, content_types=settings.ALLOWED_CONTENT_TYPES)
async def broadcast_message(message: types.Message, state: FSMContext, bot: Bot):
    await state.update_data(message=message.json(exclude_none=True))
    call = get_call_method(message)(message.from_user.id)
    await message.answer("Сообщение готово к отправке.", reply_markup=types.ReplyKeyboardRemove())
    call.reply_markup = inline_kb.post_buttons(call.reply_markup)
    await bot(call)


@client_bot_router.callback_query(BroadcastCallbackData.filter())
async def broadcast_confirmation(query: types.CallbackQuery, callback_data: BroadcastCallbackData, state: FSMContext):
    if callback_data.action == "send":
        await query.message.delete()
        await query.message.answer("Рассылка началась")
        loop = asyncio.get_event_loop()
        bot = await shortcuts.get_bot()
        data = await state.get_data()
        inline = data.get("broad_markup")
        broadcast_id = await add_broadcast(query.from_user.id, data.get('message'), bot=bot, broadcast_to_admin=False,
                                           inline=inline)
        try:
            await collect_and_run_broadcast(broadcast_id)
        except Exception as e:
            await query.message.answer(f"Ошибка: {e}")
    elif callback_data.action == "add-button":
        await query.answer()
        await query.message.answer("Отправьте кнопки. Например, [Перейти](https://t.me/DoSimplebot)",
                                   disable_web_page_preview=True,
                                   reply_markup=reply_kb.cancel())
        await state.set_state(Post.buttons)
        await state.update_data(
            markup=query.message.reply_markup.json(exclude_none=True),
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )


@client_bot_router.message(state=Post.buttons)
async def post_buttons(message: types.Message, state: FSMContext, bot: Bot):
    inline_link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')  # noqa
    buttons = inline_link_re.findall(message.text)
    if not buttons:
        await message.answer("Вы неправильно отправили. Отправьте еще раз.")
    else:
        data = await state.get_data()
        old_btns = data.get("broad_markup") or ""
        old_btns += f"{message.text}\n"
        await state.update_data(broad_markup=old_btns)
        markup = types.InlineKeyboardMarkup(**json.loads(data.get("markup")))
        chat_id = data.get("chat_id")
        message_id = data.get("message_id")
        new_markup = inline_kb.add_buttons_to_post(markup, buttons)
        await bot.edit_message_reply_markup(chat_id, message_id, reply_markup=new_markup)
        await bot.send_message(chat_id, "Кнопки добавлены", reply_to_message_id=message_id,
                               reply_markup=await reply_kb.main_menu(message.from_user.id))


@client_bot_router.message(state=ChangePhoto.photo,
                           content_types=[types.ContentType.PHOTO, types.ContentType.ANIMATION])
async def change_photo(message: types.Message, state: FSMContext):
    bot = await shortcuts.get_bot()
    if message.animation:
        file_id = message.animation.file_id
        bot.photo_is_gif = True
    else:
        file_id = message.photo[-1].file_id
        bot.photo_is_gif = False
    bot.photo = file_id
    await bot.save()
    await message.answer("Изменено ✅")
    await state.clear()


@client_bot_router.message(state=ChangeChannelLink.link)
async def change_channel_link(message: types.Message, state: FSMContext):
    if not check_url(message.text):
        await message.answer("Не верный url")
        await state.clear()
        return
    bot = await shortcuts.get_bot()
    bot.news_channel = message.text
    await bot.save()
    await message.answer("Изменено ✅")
    await state.clear()


@client_bot_router.message(state=ChangeAdmin.uid)
async def change_admin(message: types.Message, state: FSMContext, bot: Bot):
    try:
        uid = int(message.text)
        main_bot_user = await shortcuts.get_main_bot_user(uid)
        if main_bot_user:
            try:
                await bot.send_chat_action(uid, action="typing")
            except (TelegramBadRequest, TelegramForbiddenError, TelegramNotFound):
                await message.answer("Пользователь не найден. Попросите его отправить команду /start боту.")
            else:
                bot_ = await shortcuts.get_bot()
                bot_.owner = main_bot_user
                await bot_.save()
                await message.answer("✅ Админ успешно изменен")
                await bot.send_message(uid,
                                       "Этот бот передается вам. Отправьте команду /admin, "
                                       "чтобы увидеть панель администратора.")
        else:
            await message.answer("Пользователь не найден. Попросите его отправить команду /start главному боту.")
    except ValueError:
        await message.answer("Неверный ид пользователя")
    else:
        await state.clear()


@client_bot_router.message(state=ChangeSupport.username_or_uid)
async def change_support(message: types.Message, state: FSMContext):
    support = message.text
    if len(support) > 32:
        await message.answer("Неверное username или ид")
    else:
        if "@" in support:
            support = support.replace("@", "")
        bot_ = await shortcuts.get_bot()
        bot_.support = support
        await bot_.save()
        await message.answer("✅ Успешно изменен")
        await state.clear()


@client_bot_router.message(F.chat.id.in_(settings.ADMIN_LIST), commands="stat")
async def statistics(message: types.Message):
    text = (f"Пользователей всего: {await shortcuts.get_all_users_count()}\n"
            f"Новые пользователи: {await shortcuts.get_new_users_count()}\n"
            f"Заработано всего: {await shortcuts.earned()}\n"
            f"Прибыль(Сегодня): {await shortcuts.earned_today()}\n"
            f"Заказов за сегодня: {await shortcuts.ordered_today()}\n")
    await message.answer(text)


@client_bot_router.callback_query(MandatorySubscription.filter())
async def mandatory_subscription_actions(query: types.CallbackQuery, callback_data: MandatorySubscription,
                                         state: FSMContext, bot: Bot):
    bot_obj = await shortcuts.get_bot()
    chats = await shortcuts.get_subscription_chats(bot_obj)
    if callback_data.action == "switch":
        if bot_obj.mandatory_subscription is True:
            bot_obj.mandatory_subscription = False
            await query.answer("Выключен")
            await bot_obj.save()
        else:
            if chats:
                bot_obj.mandatory_subscription = True
                await query.answer("Включен")
                await bot_obj.save()
            else:
                await query.answer("Невозможно включить. Никакого чата нет. Сначала добавьте чат.", show_alert=True)
                return
    elif callback_data.action == "add":
        await state.set_state(AddSubscriptionChat.chat_id)
        try:
            await query.message.delete()
        except TelegramBadRequest:
            await query.message.edit_reply_markup()
        await query.message.answer("Отправите ИД канала или группы", reply_markup=reply_kb.cancel())
        return
    elif callback_data.action == "remove":
        text = "Выберите, чтобы удалить\n\n"
        for idx, chat in enumerate(chats, start=1):
            text += f"{idx}) {html.link(chat.title, chat.username or chat.invite_link)}\n"
        await query.message.edit_text(
            text,
            reply_markup=inline_kb.choose_subscription_chat(chats),
            disable_web_page_preview=True
        )
        return
    elif callback_data.action == "choose-to-remove":
        if callback_data.id:
            chat = await shortcuts.get_subscription_chat(bot_obj, callback_data.id)
            if chat:
                with suppress(TelegramBadRequest, TelegramForbiddenError):
                    await bot.revoke_chat_invite_link(chat.uid, chat.invite_link)
                await chat.delete()
            chats = await shortcuts.get_subscription_chats(bot_obj)
            if not chats:
                bot_obj.mandatory_subscription = False
                await bot_obj.save()
    elif callback_data.action == None:
        await query.answer()
        await query.message.edit_text("Панель администратора", reply_markup=await inline_kb.admin_buttons())
        return
    text = strings.get_subscription_chats(bot_obj.mandatory_subscription, chats)
    await query.message.edit_text(text, reply_markup=inline_kb.mandatory_subscription_status(
        bot_obj.mandatory_subscription, len(chats)), disable_web_page_preview=True)


@client_bot_router.message(state=AddSubscriptionChat.chat_id)
async def add_subscription_chat(message: types.Message, state: FSMContext, bot: Bot):
    chat_id = message.text
    await bot.send_chat_action(message.chat.id, "typing")
    bot_ = await shortcuts.get_bot()
    try:
        chat_info = await bot.get_chat(chat_id)
        invite_link = await bot.create_chat_invite_link(
            chat_info.id, name="Invite link for the smm bot"
        )
        await shortcuts.add_subscription_chat(bot_, chat_info, invite_link)
        await message.answer("✅ Чат добавлен", reply_markup=types.ReplyKeyboardRemove())
        chats = await shortcuts.get_subscription_chats(bot_)
        text = strings.get_subscription_chats(bot_.mandatory_subscription, chats)
        await message.answer(text, reply_markup=inline_kb.mandatory_subscription_status(
            bot_.mandatory_subscription, len(chats)), disable_web_page_preview=True)
    except (TelegramBadRequest, TelegramNotFound, TelegramForbiddenError):
        await message.answer("Чат не найден. "
                             "Убедитесь, что бот является администратором в чате "
                             "и имеет достаточные привилегии")
    except IntegrityError:
        await message.answer("Этот чат уже добавлен")
    else:
        await state.clear()
