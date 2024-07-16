from aiogram.dispatcher.filters.callback_data import CallbackData

class BalanceCallbackData(CallbackData, prefix="balance"):
    action: str = None


class CountryCallbackData(CallbackData, prefix="country"):
    action: str
    country_code: str = ""
    page: int = 1


class ProductCallbackData(CallbackData, prefix="product"):
    action: str = 'retrieve'
    country_code: str = ""
    product: str = None
    page: int = 1


class OrderCallbackData(CallbackData, prefix="order"):
    action: str
    order_id: int


class OrderHistoryCallbackData(CallbackData, prefix="order-history"):
    action: str = "paginate"
    page: int = 1


class BalanceHistoryCallbackData(CallbackData, prefix="balance-history"):
    action: str = "paginate"
    page: int = 1
