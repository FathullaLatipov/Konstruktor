# from aiogram.dispatcher.filters.callback_data import CallbackData
from aiogram.filters.callback_data import CallbackData


class SocialNetworkCallbackData(CallbackData, prefix="social"):
    action: str
    id: int


class ServiceCategoryCallbackData(CallbackData, prefix="service-category"):
    action: str
    id: int
    smm_idx: int


class ServiceCallbackData(CallbackData, prefix="service"):
    action: str
    id: int = None
    page: int = None
    category_idx: int = None
    smm_idx: int = None


class ServiceChoseCallbackData(CallbackData, prefix="service-chose"):
    action: str = None
    service: int
    category_idx: int
    smm_idx: int


class TransferCallbackData(CallbackData, prefix="transfer"):
    action: str


class MainMenuCallbackData(CallbackData, prefix="main-menu"):
    action: str = None


class BalanceCallbackData(CallbackData, prefix="balance"):
    action: str = None


class AdminPanelCallbackData(CallbackData, prefix="admin"):
    action: str = None


class Switch(CallbackData, prefix="switcher-state"):
    action: str = None


class BroadcastCallbackData(CallbackData, prefix="broadcast"):
    action: str
    confirm: bool = None


class MandatorySubscription(CallbackData, prefix="mandatory-s"):
    action: str = None
    id: int = None


class FavouritesCallback(CallbackData, prefix="favourite"):
    action: str
    service: int
    smm: int
    category: int


class Promocodes(CallbackData, prefix="lyrics"):
    action: str
    promocode_id: int = None
