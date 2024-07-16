from aiogram.filters.callback_data import CallbackData
from strenum import StrEnum


class ProfileActionEnum(StrEnum):
    LIKE = "LIKE"
    MESSAGE = "MESSAGE"
    SLEEP = "SLEEP"
    DISLIKE = "DISLIKE"
    REPORT = "REPORT"


class LikeActionEnum(StrEnum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    REPORT = "REPORT"


class LeomatchProfileAction(CallbackData, prefix="leo-pa"):
    action: ProfileActionEnum
    user_id: int = None


class LeomatchLikeAction(CallbackData, prefix="leo-pa"):
    action: LikeActionEnum
    user_id: int


class LeomatchProfileAlert(CallbackData, prefix="leo-alert"):
    action: str
    sender_id: int = None
    account_id: int = None


class LeomatchProfileBlock(CallbackData, prefix="leo-block"):
    account_id: int = None
