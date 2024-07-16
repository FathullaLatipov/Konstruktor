from datetime import datetime, timedelta
import logging
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import fasteners
from clientbot.handlers.horoscope.keyboards.inline import inline_builder
from clientbot.utils.smm import save_services
from config import scheduler
from clientbot.handlers.leomatch.shortcuts import get_distinkt_likes, get_likes_count
from clientbot.handlers.leomatch.keyboards.reply_kb import yes_no
from clientbot import strings, shortcuts
from clientbot.handlers.leomatch.data.state import LeomatchProfiles
from db import models
from loader import bot_session
from clientbot.data.schemas import OrderSchema
from clientbot.utils.smm import get_order_statuses
from mainbot.shortcuts import add_to_watch_at_admin
from helpers.functions import send_message
from asyncio import Lock
from aiogram import Bot
from aiogram.types import URLInputFile
from aiogram.dispatcher.fsm.state import State
import yt_dlp
from aiogram.utils.i18n import gettext as _

logger = logging.getLogger()

lock = Lock()


async def leo_alert_likes():
    async with Lock():
        leos = await get_distinkt_likes()
        for leo in leos:
            user: models.LeoMatchModel = await leo.to_user
            client: models.User = await user.user
            count = await get_likes_count(client.uid)
            if count > 0:
                bot_db = await shortcuts.get_bot_by_username(user.bot_username)
                async with Bot(token=bot_db.token, session=bot_session).context(auto_close=False) as bot:
                    state = shortcuts.get_fsm_context(bot, client.uid)
                    current_state_str = await state.get_state()
                    if isinstance(current_state_str, str):
                        state_info = current_state_str.split(":")
                        current_state = State(state_info[1], state_info[0])
                    else:
                        current_state = State()

                    if current_state.state != LeomatchProfiles.MANAGE_LIKES.state:
                        if not current_state_str:
                            await bot.send_message(client.uid,
                                                   _("Вам поставили лайк! ({count} шт.), показать их?").format(
                                                       count=count),
                                                   reply_markup=yes_no())
                            await state.set_state(LeomatchProfiles.MANAGE_LIKES)
                        else:
                            if count != user.count_likes:
                                try:
                                    await bot.send_message(client.uid,
                                                           _("У вас новый лайк! ({count} шт.) После завершения текущего дела, проверьте, кому вы понравились, нажав /start и подождав следующее уведомление.").format(
                                                               count=count))
                                    user.count_likes = count
                                    await user.save()
                                except Exception as e:
                                    pass


async def save_services_categories():
    await save_services()


async def check_orders(lock: Lock):
    async with lock:
        orders = await shortcuts.get_not_completed_orders__full()
        if len(orders) == 0:
            return
        pages = len(orders) // 100 + 1
        for page_number in range(pages):
            statuses = await get_order_statuses(orders[page_number * 100: (page_number + 1) * 100])
            for order_id in statuses:
                order = await shortcuts.get_order(order_id)
                user: models.ClientBotUser = await order.user
                if 'error' not in statuses[order_id]:
                    order_status = OrderSchema(**statuses[order_id])
                else:
                    order.status = strings.ORDER_CANCELED
                    await order.save()
                    continue
                if order.status == order_status.status:
                    continue
                bot: models.Bot = await user.bot
                owner: models.MainBotUser = await bot.owner
                if order_status.status == strings.ORDER_CANCELED:
                    await add_to_watch_at_admin(bot, order.pk, datetime.now(), owner.balance, order.bot_admin_profit,
                                                _("Заказ отменен"))
                    if not order.money_returned_to_user:
                        await shortcuts.update_user_balance(user, order.price)
                        order.money_returned_to_user = True
                        await order.save()
                    await send_message(bot.token, owner.uid,
                                       _("😔 Заказ #{order_order_id} не выполнен. Деньги убраны с заморозки").format(
                                           order_order_id=order.order_id))
                    await send_message(bot.token, user.uid, _("😔 Ваш заказ #{order_order_id} отменен. "
                                                              "Деньги возвращены на баланс бота."
                                                              "Возможно вы допустили какую-то ошибку, "
                                                              "попробуйте оформить заказ заново или выбрать другую услугу.").format(
                        order_order_id=order.order_id))
                    if bot.parent:
                        parent: models.Bot = await bot.parent
                        parent_owner: models.MainBotUser = await parent.owner
                        await send_message(parent.token,
                                           _("😔 Заказ от дочернего бота не выполнен, деньги убраны с заморозки"))
                        await add_to_watch_at_admin(parent, order.pk, datetime.now(), parent_owner.balance,
                                                    order.bot_admin_profit, _("Заказ отменен"))

                elif order_status.status == strings.COMPLETED:
                    await add_to_watch_at_admin(bot, order.pk, datetime.now(), owner.balance, order.bot_admin_profit,
                                                _("Выполнен заказ: Выполнен"))
                    if not order.money_returned_to_admin:
                        await shortcuts.give_bonus_to_admin(owner, order.bot_admin_profit)
                        order.money_returned_to_admin = True
                        await order.save()
                    await send_message(bot.token, user.uid,
                                       _("👍 Заказ #{order_order_id} выполнен. Услуга: {order_category}").format(
                                           order_order_id=order.order_id, order_category=order.category))
                    if bot.parent:
                        if not order.money_returned_to_parent:
                            await shortcuts.update_parent_balance(bot.parent, order.price)
                            order.money_returned_to_parent = True
                            await order.save()
                elif order_status.status == strings.PARTIAL:
                    price, profit, bot_admin_profit = await shortcuts.calculate_price(user.uid, order_status.charge)
                    price = order.price - price
                    if not order.money_returned_to_user:
                        user.balance += price
                        await user.save()
                        order.money_returned_to_user = True
                        await order.save()
                    order.remains = order_status.remains
                    order.price = price
                    order.profit = profit
                    order.bot_admin_profit = bot_admin_profit
                    await order.save()
                    if not order.money_returned_to_admin:
                        await send_message(bot.token, owner.uid, _("😔 Заказ #{order_order_id} частично выполнен. "
                                                                   "Остаток средств вернулся {price}, начислен на баланс.").format(
                            order_order_id=order.order_id, price=price))
                        await shortcuts.give_bonus_to_admin(owner, bot_admin_profit)
                        order.money_returned_to_admin = True
                        await order.save()
                    await send_message(bot.token, user.uid, _("😔 Заказ #{order_order_id} частично выполнен. ").format(
                        order_order_id=order.order_id))
                    if bot.parent:
                        if not order.money_returned_to_parent:
                            await shortcuts.update_parent_balance(bot.parent, order.price)
                            await send_message(bot.token, _("😔 Заказ #{order_order_id} частично выполнен. ").format(
                                order_order_id=order.order_id))
                            order.money_returned_to_parent = True
                            await order.save()
                order.updated_at = datetime.now()
                order.status = order_status.status
                order.remains = order_status.remains
                await order.save()


async def horoscope_everyday():
    async with Lock():
        clients = await models.ClientBotUser.filter(enable_horoscope_everyday_alert=True)
        for client in clients:
            bot: models.Bot = await client.bot
            async with Bot(bot.token, bot_session, parse_mode="HTML").context(auto_close=False) as bot_:
                await bot_.send_message(
                    client.uid,
                    _("🔮 <b>Посмотри свой гороскоп на сегодня и узнай, что тебя ждет!</b>"),
                    reply_markup=inline_builder(_("👀 Посмотреть"), "look_horoscope")
                )


async def task_runner():
    tasks = models.TaskModel.all().limit(1)
    copy = await tasks._clone()
    await tasks.delete()
    for task in copy:
        client: models.ClientBotUser = await task.client
        bot: models.Bot = await client.bot
        if task.task_type.value == models.TaskType.DOWNLOAD_MEDIA.value:
            url = task.data['url']
            async with Bot(bot.token, session=bot_session).context(auto_close=False) as bot_:
                await bot_.send_chat_action(client.uid, "upload_video")
                ydl_opts = {
                    'cachedir': False,
                    'noplaylist': True,
                    'outtmpl': 'clientbot/downloads/%(title)s.%(ext)s',
                    'format': 'bestvideo[ext=mp4]+bestaudio[ext=mp3]/best[ext=mp4]/best',
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        info = ydl.extract_info(url, download=False)
                        await bot_.send_video(client.uid, URLInputFile(info['url']), supports_streaming=True)
                    except Exception as e:
                        await bot_.send_message(client.uid, _("Не удалось скачать это видео: {e}").format(e=e))


async def manage_orders():
    orders = await models.SMSOrder.filter(receive_status="wait")
    for order in orders:
        now = datetime.now()
        can_ban = datetime.strptime(order.created_at.strftime("%d %m %Y %H:%M:%S"), "%d %m %Y %H:%M:%S") + timedelta(
            hours=2, minutes=20)
        if now > can_ban:
            client: models.ClientBotUser = await order.user
            bot: models.Bot = await client.bot
            async with Bot(token=bot.token, session=bot_session, parse_mode="HTML").context(auto_close=True) as bot_:
                client.balance += order.price
                await client.save()
                try:
                    await bot_.send_message(client.uid,
                                            _("Время ожидания заказа #{order_order_id} истекло. Ваш заказ отменен, деньги вернулись на баланс").format(
                                                order_order_id=order.order_id))
                    try:
                        await bot_.delete_message(client.uid, order.msg_id)
                    except:
                        pass
                    bot: models.Bot = await client.bot
                    owner: models.MainBotUser = await bot.owner
                    async with Bot(bot.token, bot_session).context(auto_close=True) as b:
                        await b.send_message(owner.uid,
                                             _("Заказ #{order_order_id} отменился, деньги вернулись на баланс клиента.").format(
                                                 order_order_id=order.order_id))
                finally:
                    order.receive_status = "canceled"
                    await order.save()


lock_file = 'apscheduler.lock'
with fasteners.InterProcessLock(lock_file):
    scheduler.add_job(check_orders, args=(lock,), trigger=IntervalTrigger(minutes=10), coalesce=True, max_instances=1,
                      replace_existing=False, misfire_grace_time=60)
    # scheduler.add_job(leo_alert_likes, trigger=IntervalTrigger(minutes=1), coalesce=True, max_instances=25)
    # scheduler.add_job(horoscope_everyday, trigger=CronTrigger(hour=0, minute=0), coalesce=True, max_instances=1, replace_existing=False, misfire_grace_time=60)

scheduler.add_job(task_runner, trigger=IntervalTrigger(seconds=10), max_instances=25)
scheduler.add_job(manage_orders, trigger=IntervalTrigger(minutes=1), coalesce=True, max_instances=1,
                  replace_existing=False, misfire_grace_time=60)
