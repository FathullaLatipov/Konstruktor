from typing import Any, Awaitable, Callable, Dict, Optional, TYPE_CHECKING

from aiogram import BaseMiddleware, types, html
from aiogram.types import TelegramObject, User
from aiogram.utils.keyboard import InlineKeyboardBuilder

from clientbot import shortcuts

if TYPE_CHECKING:
    from db.models import SubscriptionChat


def subscription_chats(chats: list):
    builder = InlineKeyboardBuilder()
    buttons = []
    for chat in chats:
        buttons.append(
            types.InlineKeyboardButton(text=chat.title,
                                       url=f"https://t.me/{chat.username}" if chat.username else chat.invite_link)
        )
    builder.row(
        *buttons,
        width=2
    )
    builder.row(
        types.InlineKeyboardButton(text="✅ Проверить подписку", callback_data="check-subscription"),
        width=1
    )
    return builder.as_markup()


class CheckSubscription(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:

        user: Optional[User] = data.get("event_from_user")

        if isinstance(event, types.CallbackQuery):
            if event.data == "check-subscription":
                return await handler(event, data)

        bot_obj = await shortcuts.get_bot()
        if bot_obj.mandatory_subscription:
            if user_obj := await shortcuts.get_user(user.id):
                statement = user_obj.subscribed_chats_at > bot_obj.subscription_chats_changed_at
                if user_obj.uid != bot_obj.owner.uid and not (statement and user_obj.subscribed_all_chats):
                    chats = await shortcuts.get_subscription_chats(bot_obj)
                    markup = subscription_chats(chats)
                    text = html.bold("Чтобы пользоваться ботом, необходимо подписаться на наши каналы")
                    if isinstance(event, types.CallbackQuery):
                        await event.message.answer(
                            text,
                            reply_markup=markup
                        )
                    elif isinstance(event, types.Message):
                        await event.answer(
                            text,
                            reply_markup=markup
                        )
                    return
        return await handler(event, data)
