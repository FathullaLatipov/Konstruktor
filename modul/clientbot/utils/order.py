# import math
#
# from aiogram import Bot, types
# from aiogram.fsm.context import FSMContext
#
# from modul.clientbot import strings, shortcuts
# from modul.clientbot.data.schemas import OrderSchema, Service
# from modul.clientbot.keyboards import reply_kb, inline_kb
# from modul.helpers.functions import send_message
# from modul.config import settings_conf
# from modul.loader import client
#
#
# # async def paginate_orders(user_id: int, page=1):
# #     limit = 5
# #     offset = (page - 1) * limit
# #     queryset = await shortcuts.get_orders(user_id)
# #     orders, count = await queryset.offset(offset).limit(limit), await queryset.count()
# #     if count:
# #         page_count = math.ceil(count / limit)
# #         text = strings.get_order_details(orders, page, page_count)
# #         reply_markup = inline_kb.order_pagination(page, page_count)
# #         return text, reply_markup
# #     return False, False
#
#
# async def perform_order(message: types.Message, state: FSMContext, service: Service):
#     user_id = message.from_user.id
#     data = await state.get_data()
#     await state.clear()
#     bot_owner = await shortcuts.get_bot_owner()
#     if "quantity" in data or "_quantity" in data:
#         quantity = data.get('_quantity', None)
#         if quantity is None:
#             quantity = data.get("quantity")
#         service_price = shortcuts.calculate_service_price(service, quantity)
#     else:
#         quantity = 1
#         service_price = float(service.rate)
#     price, profit, bot_percent = await shortcuts.calculate_price(user_id, service_price)
#     params = {
#         'action': 'add',
#         'service': service.service,
#     }
#     user = await shortcuts.get_user(user_id)
#     if user.balance < price:
#         await message.answer(f"Не достаточно на балансе, не хватает: {user.balance - price}", reply_markup=inline_kb.add_balance())
#         return
#     post_data = {key: value for key, value in data.items() if not key.startswith("_")}
#     params.update(post_data)
#     if service.type == strings.ServiceType.DEFAULT and "interval" in params:
#         params["runs"] = params['quantity'] // params['interval']
#     async with client.session.get(settings.SMM_BASE_API_URL, params=params) as response:
#         response = await response.json()
#     if 'error' in response:
#         if response['error'] == strings.HAS_ACTIVE_ORDER:
#             text = strings.HAS_ACTIVE_ORDER_RU
#         else:
#             text = strings.API_ERROR
#         await message.answer(text=text, reply_markup=await reply_kb.main_menu(message.from_user.id))
#         return
#     await message.answer(text=strings.ORDER_SUCCEEDED.format(response["order"]),
#                          reply_markup=await reply_kb.main_menu(message.from_user.id))
#     await shortcuts.update_user_balance(user_id, price * -1)
#     await shortcuts.save_order(user_id, response['order'], service.name, quantity, price, profit,
#                                bot_percent, data.get('link'), service.service, data.get("_category_idx"), data.get("_smm_idx"))
#     bot = Bot.get_current()
#     try:
#         await bot.send_message(chat_id=bot_owner.uid,
#                                 text=f"🥁Успешно был оплачен заказ на сумму {price}₽. Ваш доход: {bot_percent}₽.")
#     except:
#         pass
#     current = await shortcuts.get_current_bot()
#     if current.parent:
#         parent = await current.parent
#         owner = await parent.owner
#         await send_message(parent.token, owner.uid, f"🚀Вам начислено {price * 0.05}₽ от дочернего бота")