# from typing import Union, Optional
# from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
# from aiogram.utils.keyboard import InlineKeyboardBuilder
# # from modul.clientbot.utils.smm import get_categories, get_category, get_service, get_services_by_category
# # from shazamio import Serialize
# from aiogram.utils.i18n import gettext as _
# from modul.clientbot.data.callback_datas import (
#     BalanceCallbackData,
#     FavouritesCallback,
#     MainMenuCallbackData,
#     Switch,
#     SocialNetworkCallbackData,
#     ServiceCategoryCallbackData,
#     ServiceCallbackData,
#     ServiceChoseCallbackData,
#     AdminPanelCallbackData,
#     BroadcastCallbackData,
#     MandatorySubscription,
#     Promocodes,
#     TransferCallbackData
# )
# from modul.clientbot import strings, shortcuts
#
# cancel_button = InlineKeyboardButton(text=_("Отмена"), callback_data="cancel")
#
# async def promocode_menu(uid: int):
#     builder = InlineKeyboardBuilder()
#     promocodes = await PromocodesModel.filter(admin__uid=uid)
#     codes = [InlineKeyboardButton(text=f"{x.code[:10]} - {x.sum}", callback_data=Promocodes(action="select", promocode_id=x.pk).pack()) for x in promocodes]
#     builder.row(
#         *codes,
#         InlineKeyboardButton(text=_("Добавить промокод"), callback_data=Promocodes(action="add").pack()),
#         InlineKeyboardButton(text=_("Назад"), callback_data=Promocodes(action="back").pack()),
#         width=1
#     )
#     return builder.as_markup()
#
# def promocode_manage(promocode_id: int):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Продлить промокод"), callback_data=Promocodes(action="refill", promocode_id=promocode_id).pack()),
#         InlineKeyboardButton(text=_("Удалить промокод"), callback_data=Promocodes(action="delete", promocode_id=promocode_id).pack()),
#         InlineKeyboardButton(text=_("Назад"), callback_data=AdminPanelCallbackData(action="promocodes").pack()),
#         width=1
#     )
#     return builder.as_markup()
#
# def promocode_sure_delete(promocode_id: int):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Да"), callback_data=Promocodes(action="delete-confirm", promocode_id=promocode_id).pack()),
#         InlineKeyboardButton(text=_("Нет"), callback_data=Promocodes(action="select", promocode_id=promocode_id).pack()),
#         width=1
#     )
#     return builder.as_markup()
#
# def add_balance():
#     builder = InlineKeyboardBuilder()
#     builder.row(InlineKeyboardButton(text=_("💰 Пополнить баланс"), callback_data=BalanceCallbackData(action="refill").pack()),)
#     builder.row(InlineKeyboardButton(text=_("🎁 Ввести промокод"), callback_data=BalanceCallbackData(action="promocode").pack()),)
#     return builder.as_markup()
#
# def balance_menu():
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("📈 История"),
#                              callback_data=BalanceCallbackData(action="history").pack()),
#         InlineKeyboardButton(text=_("💰 Пополнить баланс"),
#                              callback_data=BalanceCallbackData(action="refill").pack()),
#         InlineKeyboardButton(text=_("🎁 Ввести промокод"), callback_data=BalanceCallbackData(action="promocode").pack()),
#         InlineKeyboardButton(
#             text=strings.BACK, callback_data=MainMenuCallbackData().pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def transfer_keyboard():
#     builder = InlineKeyboardBuilder()
#     builder.add(InlineKeyboardButton(text=_("Перевести деньги на баланс"),
#                                      callback_data=TransferCallbackData(action="transfer_money").pack())
#                 )
#     return builder.as_markup()
#
#
# async def social_networks() -> InlineKeyboardMarkup:
#     builder = InlineKeyboardBuilder()
#     buttons = []
#     for index, item in enumerate(strings.SMM_CATEGORIES):
#         buttons.append(InlineKeyboardButton(text=F"{strings.SMM_CATEGORIES_EMOJIS[index]} {item}",
#                                             callback_data=SocialNetworkCallbackData(action="obtain",
#                                                                                     id=index).pack()))
#     builder.row(*buttons, width=2)
#     builder.row(
#         InlineKeyboardButton(text=_("Избранные"),
#                              callback_data=SocialNetworkCallbackData(action="favourites", id=0).pack()),
#         width=1)
#     builder.row(
#         InlineKeyboardButton(text=_("« Назад"),
#                              callback_data=SocialNetworkCallbackData(action="back", id=0).pack()),
#         width=1)
#     return builder.as_markup()
#
#
# async def service_category(smm_category_index: int):
#     smm_category = strings.SMM_CATEGORIES[smm_category_index]
#     builder = InlineKeyboardBuilder()
#     categories = await get_categories(smm_category)
#     if not categories:
#         return None
#     for index, category in enumerate(categories):
#         builder.row(
#             InlineKeyboardButton(text=category,
#                                  callback_data=ServiceCategoryCallbackData(action="obtain",
#                                                                            id=index,
#                                                                            smm_idx=smm_category_index).pack()),
#             width=2)
#     builder.row(
#         InlineKeyboardButton(text=_("« Назад"),
#                              callback_data=ServiceCategoryCallbackData(action="back", id=0,
#                                                                        smm_idx=smm_category_index).pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# async def services(smm_idx: int, category_idx: int):
#     builder = InlineKeyboardBuilder()
#     category = await get_category(smm_idx, category_idx)
#     for service in await get_services_by_category(category):
#         builder.row(InlineKeyboardButton(text=service.name,
#                                          callback_data=ServiceCallbackData(action="obtain",
#                                                                            smm_idx=smm_idx,
#                                                                            category_idx=category_idx,
#                                                                            id=service.service).pack()),
#                     width=2)
#     builder.row(
#         InlineKeyboardButton(text=_("« Назад"),
#                              callback_data=ServiceCallbackData(action="back", category_idx=category_idx,
#                                                                smm_idx=smm_idx).pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def service_chose(smm_idx: int, category_idx: int, service: int):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Выбрать"),
#                              callback_data=ServiceChoseCallbackData(
#                                  smm_idx=smm_idx,
#                                  category_idx=category_idx,
#                                  service=service
#                              ).pack()),
#         InlineKeyboardButton(text=_("Добавить в избранное"),
#                              callback_data=ServiceChoseCallbackData(
#                                  action="add_to_favourites",
#                                  smm_idx=smm_idx,
#                                  category_idx=category_idx,
#                                  service=service
#                              ).pack()),
#         InlineKeyboardButton(text=_("« Назад"),
#                              callback_data=ServiceChoseCallbackData(
#                                  action="back",
#                                  smm_idx=smm_idx,
#                                  category_idx=category_idx,
#                                  service=service
#                              ).pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def favourite_service_chose(smm_idx: int, category_idx: int, service: int):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Выбрать"),
#                              callback_data=ServiceChoseCallbackData(
#                                  smm_idx=smm_idx,
#                                  category_idx=category_idx,
#                                  service=service
#                              ).pack()),
#         InlineKeyboardButton(text=_("Удалить из избранного"),
#                              callback_data=FavouritesCallback(action="delete", service=service, smm=smm_idx,
#                                                               category=category_idx).pack()),
#         InlineKeyboardButton(text=_("« Назад"),
#                              callback_data=FavouritesCallback(action="back", service=service, smm=smm_idx,
#                                                               category=category_idx).pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def payment(url: str, order_id: str):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Оплатить"), url=url)
#         , cancel_button
#         , width=1
#     )
#     return builder.as_markup()
#
#
# def order_pagination(page=1, page_count=1):
#     builder = InlineKeyboardBuilder()
#     if page > 1:
#         builder.add(
#             InlineKeyboardButton(
#                 text="⬅️", callback_data=f'order-pagination:{page - 1}')
#         )
#     if page_count > page:
#         builder.add(
#             InlineKeyboardButton(
#                 text="➡️", callback_data=f"order-pagination:{page + 1}")
#         )
#     return builder.as_markup()
#
# def switcher(name: str):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(text=_("Переключить"), callback_data=Switch(action=name).pack()),
#         InlineKeyboardButton(text=_("Отмена"), callback_data=Switch(action="cancel").pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# async def admin_buttons():
#     builder = InlineKeyboardBuilder()
#     bot = await shortcuts.get_current_bot()
#     builder.row(
#         InlineKeyboardButton(text=_("Запрос истории"), callback_data=AdminPanelCallbackData(
#             action="request_history").pack()),
#         InlineKeyboardButton(text=_("📊 Статистика"), callback_data=AdminPanelCallbackData(
#             action="statistics").pack()),
#         InlineKeyboardButton(text=_("✉️ Рассылка"), callback_data=AdminPanelCallbackData(
#             action="broadcast").pack()),
#         InlineKeyboardButton(text=_("📄 Обязательная подписка"),
#                              callback_data=AdminPanelCallbackData(action="mandatory-subscription").pack()),
#         # InlineKeyboardButton(text="🖼 Сменить фото",
#         #                      callback_data=AdminPanelCallbackData(action="change-photo").pack()),
#         InlineKeyboardButton(text=_("📢 Изменить новостной канал"),
#                              callback_data=AdminPanelCallbackData(action="channel-link").pack()),
#         InlineKeyboardButton(text=_("⚖️ Изменить процент"),
#                              callback_data=AdminPanelCallbackData(action="change-percent").pack()),
#         InlineKeyboardButton(text=_("👨‍💻 Изменить username поддержки"),
#                              callback_data=AdminPanelCallbackData(action="change-support").pack()),
#         InlineKeyboardButton(text=_("💸 Продать бота"),
#                              callback_data=AdminPanelCallbackData(action="change-admin").pack()),
#         InlineKeyboardButton(text=_("📥 Дамп пользователей"),
#                              callback_data=AdminPanelCallbackData(action="dump-users").pack()),
#         InlineKeyboardButton(text=_("🎁 Промокоды"),
#                              callback_data=AdminPanelCallbackData(action="promocodes").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_promotion else '🔴' }" + _("Вкл / выкл накрутку"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-promotion").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_child_bot else '🔴' }" + _("Вкл / выкл создания бота"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-create").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_music else '🔴' }" + _("Вкл / выкл музыку"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-music").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_download else '🔴' }" + _("Вкл / выкл скачивание медиа"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-download").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_leo else '🔴' }" + _("Вкл / выкл Знакомства"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-leomatch").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_chatgpt else '🔴' }" + _("Вкл / выкл ChatGPT"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-chatgpt").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_horoscope else '🔴' }" + _("Вкл / выкл Гороскор"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-horoscope").pack()),
#         InlineKeyboardButton(text=f"{'🟢' if bot.enable_anon else '🔴' }" + _("Вкл / выкл Анонимный чат"),
#                              callback_data=AdminPanelCallbackData(action="manage-switch-anon").pack()),
#
#         width=1
#
#     )
#     return builder.as_markup()
#
#
# def post_buttons(reply_markup: Optional[InlineKeyboardMarkup] = None):
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(
#             text=_("Начать рассылку"), callback_data=BroadcastCallbackData(action="send").pack()),
#         InlineKeyboardButton(text=_("Добавить кнопку"), callback_data=BroadcastCallbackData(
#             action="add-button").pack()),
#         width=1
#     )
#     if reply_markup:
#         buttons = []
#         for row in reply_markup.inline_keyboard:
#             for button in row:
#                 if button.url:
#                     buttons.append(button)
#         if buttons:
#             builder.row(*buttons, width=len(buttons))
#     return builder.as_markup()
#
# def admin_panel_cancel():
#     builder = InlineKeyboardBuilder()
#     builder.row(
#         InlineKeyboardButton(
#             text=strings.BACK, callback_data=AdminPanelCallbackData(action="cancel").pack())
#     )
#     return builder.as_markup()
#
# def add_buttons_to_post(markup: InlineKeyboardMarkup, buttons: list):
#     builder = InlineKeyboardBuilder(markup=markup.inline_keyboard)
#     builder.row(*[InlineKeyboardButton(text=text, url=url)
#                   for text, url in buttons], width=len(buttons))
#     return builder.as_markup()
#
# def gen_buttons(buttons: list):
#     builder = InlineKeyboardBuilder()
#     builder.row(*[InlineKeyboardButton(text=text, url=url) for text, url in buttons], width=1)
#     return builder.as_markup()
#
#
# def remove_buttons_from_post(reply_markup: Optional[InlineKeyboardMarkup] = None):
#     if reply_markup:
#         keyboards = reply_markup.inline_keyboard
#         builder = InlineKeyboardBuilder()
#         for row in keyboards:
#             buttons = []
#             for button in row:
#                 if button.url:
#                     buttons.append(button)
#             if buttons:
#                 builder.row(*buttons, width=len(buttons))
#         return builder.as_markup()
#
#
# def mandatory_subscription_status(is_turned_on: bool, chats_count: int = 0):
#     builder = InlineKeyboardBuilder()
#     btn_txt = _("Выключить") if is_turned_on else _("Включить")
#     builder.row(
#         InlineKeyboardButton(text=btn_txt,
#                              callback_data=MandatorySubscription(action="switch").pack()),
#         width=1
#     )
#     action_buttons = [
#         InlineKeyboardButton(
#             text=_("➕ Добавить чат"), callback_data=MandatorySubscription(action="add").pack())
#     ]
#     if chats_count:
#         action_buttons.append(
#             InlineKeyboardButton(text=_("🗑 Удалить чат"), callback_data=MandatorySubscription(
#                 action="remove").pack())
#         )
#     builder.row(*action_buttons, width=len(action_buttons))
#     builder.row(
#         InlineKeyboardButton(
#             text=strings.BACK, callback_data=MandatorySubscription().pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def choose_subscription_chat(chats: list):
#     builder = InlineKeyboardBuilder()
#     buttons = []
#     for idx, chat in enumerate(chats, 1):
#         buttons.append(
#             InlineKeyboardButton(text=str(idx),
#                                  callback_data=MandatorySubscription(action="choose-to-remove", id=chat.uid).pack())
#         )
#     builder.row(*buttons, width=8)
#     builder.row(
#         InlineKeyboardButton(text=strings.BACK, callback_data=MandatorySubscription(
#             action="choose-to-remove").pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# def info_menu(support: Union[int, str], channel_link: str = None):
#     if isinstance(support, int) or support.isdigit():
#         support_link = f"tg://user?id={support}"
#     else:
#         support_link = f"https://t.me/{support}"
#     builder = InlineKeyboardBuilder()
#     buttons = [
#         InlineKeyboardButton(text=_("👨‍💻 Техподдержка / Администратор"), url=support_link),
#         InlineKeyboardButton(text="❓ FAQ", callback_data="faq-information")
#     ]
#     if channel_link:
#         buttons.append(InlineKeyboardButton(
#             text=_("📢 Новости"), url=channel_link))
#     builder.row(
#         *buttons,
#         InlineKeyboardButton(
#             text=strings.BACK, callback_data=MainMenuCallbackData().pack()),
#         width=1
#     )
#     return builder.as_markup()
#
#
# async def get_favourites_btns(user_id: int) -> InlineKeyboardMarkup:
#     """Генерация кнопок избранных"""
#     builder = InlineKeyboardBuilder()
#     buttons = []
#     favourties = await shortcuts.get_favourites(user_id)
#     for favourite in favourties:
#         service = await get_service(favourite.service)
#         if service:
#             buttons.append(
#                 InlineKeyboardButton(text=f"{service.name}", callback_data=FavouritesCallback(action="view",
#                                                                                             service=favourite.service,
#                                                                                             smm=favourite.smm,
#                                                                                             category=favourite.category).pack())
#             )
#     builder.row(*buttons, width=1)
#     builder.row(
#         InlineKeyboardButton(text=strings.BACK, callback_data=FavouritesCallback(action="exit",
#                                                                                  service=-1, smm=-1,
#                                                                                  category=-1).pack()),
#         width=1
#     )
#     return builder.as_markup()
