import json
from math import ceil
from clientbot.handlers.sms import shortcuts
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from clientbot.handlers.sms.data.callback_data import (
    CountryCallbackData,
    ProductCallbackData,
    OrderCallbackData,
    OrderHistoryCallbackData,
    BalanceHistoryCallbackData,
)
from config import settings
from aiogram.utils.i18n import gettext as _

cancel_button = InlineKeyboardButton(text=_("Отмена"), callback_data="cancel")


def back_kb(callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data=callback_data)
    )
    return builder.as_markup()


def country_search_result(countries: list):
    builder = InlineKeyboardBuilder()
    for country in countries:
        country_name = shortcuts.get_contry(country['country_code'])
        builder.row(
            InlineKeyboardButton(text=f"{country_name} ({country[1]}%)",
                                 callback_data=CountryCallbackData(action="retrieve", country_code=country[2]).pack()),
            width=1
        )
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data=CountryCallbackData(action="paginate").pack())
    )
    return builder.as_markup()


async def countries_kb(page: int = 1, search_key: str = None):
    countries, length = shortcuts.get_countries(page, search_key=search_key)
    builder = InlineKeyboardBuilder()
    buttons = []
    for country in countries:
        country: dict = country
        country_code = country.get('id')
        buttons.append(
            InlineKeyboardButton(text=country["name"],
                                 callback_data=CountryCallbackData(action="retrieve", country_code=country_code,
                                                                   page=page).pack())
        )
    builder.row(*buttons, width=3)
    pagination_row = []
    pages = ceil(length / 15)
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️",
                                 callback_data=CountryCallbackData(action="paginate", country_code=country_code,
                                                                   country="-1", page=page - 1).pack())
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Стр: {page} из {pages}",
                             callback_data=CountryCallbackData(action="page-list", country_code=country_code,
                                                               country="-1", page=page).pack())
    )
    if page < pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=CountryCallbackData(action="paginate",
                                                                              country_code=country_code, country="-1",
                                                                              page=page + 1).pack())
        )
    builder.row(*pagination_row, width=3)
    return builder.as_markup()


async def countries_pages_kb(page: int = 1):
    builder = InlineKeyboardBuilder()
    nothing, length = shortcuts.get_countries()
    pages = ceil(length / 15)
    buttons = []
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=CountryCallbackData(action="paginate", country_code="-1", page=i).pack())
        )
    builder.row(*buttons, width=6)
    builder.row(
        InlineKeyboardButton(text=_("Назад"),
                             callback_data=CountryCallbackData(action="paginate", country_code="-1", page=page).pack()),
        width=1
    )
    return builder.as_markup()


async def products_kb(country_code: str, page: int = 1):
    builder = InlineKeyboardBuilder()
    buttons = []
    try:
        products, length = await shortcuts.get_products(country_code, page)
    except Exception as e:
        raise e

    for product in products:
        product: dict = product
        key = list(product.keys())[0]
        count = product[key]['count']
        product_name = f"{product[key]['service']} ({count})"
        buttons.append(
            InlineKeyboardButton(text=f"{product_name}",
                                 callback_data=ProductCallbackData(action="retrieve",
                                                                   country_code=country_code,
                                                                   product=product[key]['slug']).pack())
        )
    builder.row(*buttons, width=3)
    pagination_row = []
    pages = ceil(length / 15)
    if page > 1:
        pagination_row.append(
            InlineKeyboardButton(text="⬅️", callback_data=ProductCallbackData(action="paginate",
                                                                              country_code=country_code,
                                                                              product="-1",
                                                                              page=page - 1).pack())
        )
    pagination_row.append(
        InlineKeyboardButton(text=f"Стр: {page} из {pages}",
                             callback_data=ProductCallbackData(action="page-list",
                                                               country_code=country_code,
                                                               product="-1",
                                                               page=page).pack())
    )
    if page < pages:
        pagination_row.append(
            InlineKeyboardButton(text="➡️", callback_data=ProductCallbackData(action="paginate",
                                                                              country_code=country_code,
                                                                              product="-1",
                                                                              page=page + 1).pack())
        )
    builder.row(*pagination_row, width=3)
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data="show_countries"),
        width=1
    )
    return builder.as_markup()


async def products_pages_kb(callback_data: ProductCallbackData):
    nothing, length = await shortcuts.get_products(callback_data.country_code, callback_data.page)
    builder = InlineKeyboardBuilder()
    pages = ceil(length / 15)
    buttons = []
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}!-" if i == callback_data.page else str(i),
                                 callback_data=ProductCallbackData(
                                     country_code=callback_data.country_code,
                                     product=callback_data.product,
                                     action="paginate", page=i).pack())
        )
    builder.row(*buttons, width=6)
    builder.row(
        InlineKeyboardButton(text=_("Назад"),
                             callback_data=ProductCallbackData(country_code=callback_data.country_code,
                                                               product=callback_data.product, action="paginate",
                                                               page=callback_data.page).pack()),
        width=1
    )
    return builder.as_markup()


def buy_product_kb(country_code: str, product: str):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Купить"),
                             callback_data=ProductCallbackData(
                                 action="buy",
                                 country_code=country_code,
                                 product=product,
                                 page=1
                             ).pack()),
        InlineKeyboardButton(text=_("Назад"),
                             callback_data=ProductCallbackData(
                                 action="paginate",
                                 country_code=country_code,
                                 product=product,
                                 page=1
                             ).pack()),
        width=1
    )
    return builder.as_markup()


def order_actions(order_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Изменить номер"),
                             callback_data=OrderCallbackData(action="change", order_id=order_id).pack()),
        InlineKeyboardButton(text=_("Бан"),
                             callback_data=OrderCallbackData(action="ban", order_id=order_id).pack()),
        width=2
    )
    return builder.as_markup()


def order_history_kb(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=OrderHistoryCallbackData(page=page - 1).pack())
        )
    buttons.append(
        InlineKeyboardButton(text=f"Стр. {page} из {pages}",
                             callback_data=OrderHistoryCallbackData(action="page-list", page=page).pack())
    )
    if page < pages:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=OrderHistoryCallbackData(page=page + 1).pack())
        )
    builder.row(*buttons, width=3)
    return builder.as_markup()


def order_history_pages(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=OrderHistoryCallbackData(page=i).pack())
        )
    builder.row(*buttons, width=8)
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data=OrderHistoryCallbackData(page=page).pack()),
        width=1
    )
    return builder.as_markup()


def balance_history_kb(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    if page > 1:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=BalanceHistoryCallbackData(page=page - 1).pack())
        )
    buttons.append(
        InlineKeyboardButton(text=f"Стр. {page} из {pages}",
                             callback_data=BalanceHistoryCallbackData(action="page-list", page=page).pack())
    )
    if page < pages:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=BalanceHistoryCallbackData(page=page + 1).pack())
        )
    builder.row(*buttons, width=3)
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data=BalanceHistoryCallbackData(action="back").pack()),
        width=1
    )
    return builder.as_markup()


def balance_history_pages(length: int, page: int = 1):
    pages = ceil(length / settings.HISTORY_LIMIT)
    buttons = []
    builder = InlineKeyboardBuilder()
    for i in range(1, pages + 1):
        buttons.append(
            InlineKeyboardButton(text=f"-{i}-" if i == page else str(i),
                                 callback_data=BalanceHistoryCallbackData(page=i).pack())
        )
    builder.row(*buttons, width=8)
    builder.row(
        InlineKeyboardButton(text=_("Назад"), callback_data=BalanceHistoryCallbackData(page=page).pack()),
        width=1
    )
    return builder.as_markup()


def product_search_result(products: list, country_code: str):
    builder = InlineKeyboardBuilder()
    for product in products:
        builder.row(
            InlineKeyboardButton(text=f"{product[0].capitalize()} ({product[1]}%)",
                                 callback_data=ProductCallbackData(action="retrieve",
                                                                   country_code=country_code,
                                                                   product=product[0]).pack()),
            width=1
        )
    builder.row(
        InlineKeyboardButton(text=_("Назад"),
                             callback_data=ProductCallbackData(action="paginate",
                                                               country_code=country_code, ).pack())
    )
    return builder.as_markup()
