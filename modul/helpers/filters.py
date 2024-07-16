from typing import Any, Union, Dict, Optional

from aiogram import Bot, Router
from aiogram.filters import BaseFilter
from aiogram.types import User, CallbackQuery, Message, TelegramObject
from ..config import settings_conf
from ..models import Bot


class IsSMMBot(BaseFilter):
    async def __call__(self, event, bot: Bot) -> Union[bool, Dict[str, Any]]:
        return settings_conf.BOT_TOKEN != bot.token


class IsMainBot(BaseFilter):
    async def __call__(self, event: TelegramObject, bot: Bot) -> bool:
        return settings_conf.BOT_TOKEN == bot.token


class IsClientBot(BaseFilter):
    async def __call__(self, event: TelegramObject, bot: Bot) -> bool:
        return settings_conf.BOT_TOKEN != bot.token


def setup_main_bot_filter(router1: Router, router2: Router):
    print('dopmne')
    router1.message.filter(IsMainBot())
    router1.callback_query.filter(IsMainBot())
    router2.message.filter(IsClientBot())
    router2.callback_query.filter(IsClientBot())
    print(router1.message.handlers)


class ChatFilter(BaseFilter):
    chat_id: Union[list, Union[int, str]]

    async def __call__(self, obj: Union[Message, CallbackQuery], **kwargs: Any) -> Union[bool, Dict[str, Any]]:
        user: Optional[User] = kwargs.get('event_from_user', None)
        if isinstance(self.chat_id, int):
            self.chat_id = [self.chat_id]
        elif not isinstance(self.chat_id, list):
            self.chat_id = list(self.chat_id)
        return user.id in self.chat_id
