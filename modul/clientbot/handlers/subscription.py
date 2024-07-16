from datetime import timezone, datetime

from aiogram import types, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.utils.i18n import gettext as _

from clientbot import shortcuts
from loader import client_bot_router

NOT_MEMBER_OF_THE_CHAT = ['left', 'restricted', 'kicked']


@client_bot_router.chat_member()
async def chat_member_update(chat_member_updated: types.ChatMemberUpdated, bot: Bot):
    bot_obj = await shortcuts.get_bot()
    if await shortcuts.get_subscription_chat(bot_obj, chat_member_updated.chat.id):
        chat_member = chat_member_updated.new_chat_member
        chat_title = chat_member_updated.chat.title or chat_member_updated.chat.first_name
        if bot_obj.mandatory_subscription:
            if user_obj := await shortcuts.get_user(chat_member.user.id):
                if chat_member.status in NOT_MEMBER_OF_THE_CHAT:
                    if user_obj.subscribed_all_chats:
                        user_obj.subscribed_all_chats = False
                        await user_obj.save()
                        try:
                            await bot.send_message(user_obj.uid, _("Вы ушли с {chat_title}. "
                                                                 "Вы больше не можете использовать бота.").format(chat_title=chat_title))
                        except (TelegramBadRequest, TelegramForbiddenError):
                            pass


@client_bot_router.callback_query(text="check-subscription")
async def check_subscription(query: types.CallbackQuery, bot: Bot):
    bot_obj = await shortcuts.get_bot()
    chats = await shortcuts.get_subscription_chats(bot_obj)
    is_member = False
    for chat in chats:
        chat_member = await bot.get_chat_member(chat.uid, query.from_user.id)
        if chat_member.status not in NOT_MEMBER_OF_THE_CHAT:
            is_member = True
        if not is_member:
            await query.answer(_("Вы присоединились не ко всем каналам"), show_alert=True)
            return
    try:
        await query.message.edit_text(_("Вы присоединились ко всем каналам. Вы можете использовать бота."))
    except:
        await query.message.delete()
        await query.answer(_("Вы присоединились ко всем каналам. Вы можете использовать бота."), show_alert=True)
    user_obj = await shortcuts.get_user(query.from_user.id)
    if user_obj != None:
        user_obj.subscribed_all_chats = True
        user_obj.subscribed_chats_at = datetime.now(timezone.utc)
        await user_obj.save()
