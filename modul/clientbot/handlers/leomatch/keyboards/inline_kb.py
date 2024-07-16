from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from modul.clientbot.handlers.leomatch.data.callback_datas import LeomatchLikeAction, LeomatchProfileAction, \
    LeomatchProfileAlert, LeomatchProfileBlock, LikeActionEnum, ProfileActionEnum
from aiogram.utils.i18n import gettext as _


def profile_view_action(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👍", callback_data=LeomatchProfileAction(action=ProfileActionEnum.LIKE,
                                                                           user_id=user_id).pack()),
        InlineKeyboardButton(text="💌", callback_data=LeomatchProfileAction(action=ProfileActionEnum.MESSAGE,
                                                                           user_id=user_id).pack()),
        InlineKeyboardButton(text="⚠️",
                             callback_data=LeomatchLikeAction(action=ProfileActionEnum.REPORT, user_id=user_id).pack()),
        # InlineKeyboardButton(text="💤", callback_data=LeomatchProfileAction(action=ProfileActionEnum.SLEEP).pack()),
        InlineKeyboardButton(text="👎", callback_data=LeomatchProfileAction(action=ProfileActionEnum.DISLIKE).pack()),
        width=4
    )
    return builder.as_markup()


def profile_like_action(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❤️",
                             callback_data=LeomatchLikeAction(action=LikeActionEnum.LIKE, user_id=user_id).pack()),
        InlineKeyboardButton(text="👎",
                             callback_data=LeomatchLikeAction(action=LikeActionEnum.DISLIKE, user_id=user_id).pack()),
        # InlineKeyboardButton(text="⚠️", callback_data=LeomatchLikeAction(action=LikeActionEnum.REPORT, user_id=user_id).pack()),
        width=4
    )
    return builder.as_markup()


def profile_alert(sender_id: int, account_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Да"), callback_data=LeomatchProfileAlert(action="yes", sender_id=sender_id,
                                                                              account_id=account_id).pack()),
        InlineKeyboardButton(text=_("Нет"), callback_data=LeomatchProfileAlert(action="no").pack()),
        width=2
    )
    return builder.as_markup()


def profile_alert_action(sender_id: int, account_id: int):
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=_("Заблокировать"), callback_data=LeomatchProfileBlock(account_id=account_id).pack()),
        InlineKeyboardButton(text=_("Заблокировать отправителя"),
                             callback_data=LeomatchProfileBlock(account_id=sender_id).pack()),
        InlineKeyboardButton(text=_("Отменить"), callback_data=LeomatchProfileBlock().pack()),
        width=2
    )
    return builder.as_markup()


def write_profile(username_or_uid: str or int, is_username: bool = False):
    builder = InlineKeyboardBuilder()
    link = f"https://t.me/{username_or_uid}" if is_username else f"tg://user?id={username_or_uid}"
    builder.row(
        InlineKeyboardButton(text=_("Написать"), url=link),
        width=4
    )
    return builder.as_markup()
